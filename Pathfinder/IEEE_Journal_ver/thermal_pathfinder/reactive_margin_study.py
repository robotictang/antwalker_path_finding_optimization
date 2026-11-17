"""Test frozen reactive margins on new MuJoCo courses."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
from statistics import median

from .margin_profiles import digest
from .mission_analysis import paired_result
from .mission_completion import choose_route, forecast, replay
from .mission_profiles import arguments, design
from .network_planning import EdgeThermalModel
from .network_study import write_json
from .reactive_forecast import ProgressForecast
from .reactive_margin import DEFAULT_CONFIG, DEFAULT_OUTPUT, DEFAULT_REFERENCE, Margins, observations, screen
from .reactive_study import check_execution, choose_progress, load_inputs

METHODS = ("stitched_fixed", "reactive_fixed", "reactive_calibrated")


def verify_calibration(config, output, reference):
    path = output / "calibration.json"
    calibration = json.loads(path.read_text())
    if digest(config) != calibration["held_out_config_sha256"]:
        raise ValueError("Held-out configuration changed after calibration")
    for parent, key in ((reference, "development_sha256"), (Path(__file__).parent, "source_sha256")):
        if any(digest(parent / name) != sha for name, sha in calibration[key].items()):
            raise ValueError(f"Frozen calibration input changed in {parent}")
    return Margins(**calibration["selected"]["margins"])


def summarize(plans, predictions, executions, spec, thermal, calibrated):
    paired = {course["id"]: {method: [] for method in METHODS} for course in spec["maps"]}
    by_method = {}
    for method in METHODS:
        subset = [plan for plan in plans if plan["method"] == method]
        outcomes = Counter()
        for plan in subset:
            run = executions.get(plan["execution"])
            outcome = (run["failure"] or "completed") if run is not None else plan["planning_failure"]
            outcomes[outcome] += 1
            paired[plan["map"]][method].append(outcome == "completed")
        by_method[method] = {
            "outcomes": dict(outcomes), "median_planning_s": median(row["planning_s"] for row in subset),
            "max_planning_s": max(row["planning_s"] for row in subset),
        }

    comparisons = {}
    for baseline in METHODS[:2]:
        target = by_method[METHODS[2]]["outcomes"].get("thermal_limit", 0)
        control = by_method[baseline]["outcomes"].get("thermal_limit", 0)
        gain = paired_result([(row[baseline], row[METHODS[2]]) for row in paired.values()], spec["bootstrap_seed"])
        gain["calibrated_only"] = gain.pop("per_motor_only")
        gain["baseline_only"] = gain.pop("anonymous_only")
        gain["meets_completion_target"] = gain["mean_gain_pp"] >= spec["minimum_gain_pp"]
        gain["additional_thermal_stops"] = target - control
        gain["meets_joint_target"] = gain["meets_completion_target"] and target <= control
        comparisons[baseline] = gain

    rows = observations(predictions, executions, spec["maps"], thermal)
    fixed = Margins(spec["thermal_margin_c"], 0.0)
    return {
        "margins": asdict(calibrated), "paired_starts": len(plans) // len(METHODS),
        "decisions": len(plans), "physics_replays": len(executions), "by_method": by_method,
        "completed_by_map": {name: {method: sum(values) for method, values in row.items()}
                             for name, row in paired.items()},
        "comparisons": comparisons,
        "common_replay_screening": {METHODS[1]: screen(fixed, rows), METHODS[2]: screen(calibrated, rows)},
    }


def run(config, output, reference, workers):
    calibrated = verify_calibration(config, output, reference)
    lock, networks, settings, starts, walking = design(config)
    if json.loads((output / "manifest.json").read_text()) != json.loads(json.dumps(lock)):
        raise ValueError("Frozen nominal manifest differs from the current experiment")
    spec = lock["study"]
    deadlines = {item["id"]: item["deadline_s"] for item in spec["maps"]}
    fixed = Margins(spec["thermal_margin_c"], 0.0)
    walks, profiles, provenance = load_inputs(networks, spec, output, walking["goal_radius"])
    folder = output / "missions"
    folder.mkdir()
    write_json(output / "evaluation_manifest.json", {
        "nominal_manifest_sha256": digest(output / "manifest.json"),
        "calibration_sha256": digest(output / "calibration.json"),
        "profile_index_sha256": digest(output / "edge_profiles.json"),
        "nominal_profiles": provenance,
        "methods": dict(zip(METHODS, map(asdict, (fixed, fixed, calibrated)), strict=True)),
    })
    plans, schedules, predictions = [], {}, {}
    for name, network in networks.items():
        for setting, thermal in settings.items():
            stitched = {action: EdgeThermalModel.from_walk(walk, thermal) for action, walk in walks[name].items()}
            predictor = ProgressForecast(network, profiles[name], thermal, spec, walking["goal_radius"])
            stages = [[action for action in stitched if action.edge.stage == stage] for stage in network.edges]
            probe = min(product(*stages), default=(), key=lambda route: (
                sum(stitched[a].elapsed_s for a in route), tuple(a.name for a in route)
            ))
            deadline = deadlines[name]
            budget = spec["planning_budget_s"]
            for start, initial in starts[setting].items():
                case = (name, setting, start)
                baseline = choose_route(network, stitched, (initial,), deadline,
                                        thermal.limit_c - fixed.temperature_c, budget)
                choices = (baseline, *(choose_progress(
                    network, predictor, initial, deadline - margins.deadline_s,
                    thermal.limit_c - margins.temperature_c, budget, stitched, True
                ) for margins in (fixed, calibrated)))
                keys = {}
                for method, choice in zip(METHODS, choices, strict=True):
                    schedule, peak, duration, planning_s, examined, failure = choice
                    key = "_".join((*case, *(action.name for action in schedule))) if schedule else None
                    keys[schedule] = key
                    plans.append({
                        "map": name, "setting": setting, "start": start, "method": method, "execution": key,
                        "actions": [action.name for action in schedule], "predicted_peak_c": peak,
                        "predicted_elapsed_s": duration, "planning_s": planning_s, "schedules_examined": examined,
                        "planning_failure": failure,
                    })
                if probe:
                    keys.setdefault(probe, "_".join((*case, *(action.name for action in probe))))
                for schedule, key in keys.items():
                    if key is None:
                        continue
                    pred = predictor.predict(schedule, initial, True)
                    schedules[key] = (*case, schedule)
                    predictions[key] = {
                        "progress_reactive": asdict(pred),
                        "stitched_nominal": {"peak_c": forecast(schedule, stitched, initial),
                                             "elapsed_s": sum(stitched[a].elapsed_s for a in schedule)},
                        "fastest_nominal_probe": schedule == probe,
                    }
        print(f"Planned {name}", flush=True)
    write_json(output / "plans.json", plans)
    write_json(output / "schedule_forecasts.json", predictions)
    print(f"Saved {len(plans)} paired decisions; running {len(schedules)} distinct warm walks", flush=True)

    executions = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {
            pool.submit(replay, networks[name], schedule, spec, deadlines[name], walking, settings[setting],
                        starts[setting][start], folder / f"{key}.npz"): key
            for key, (name, setting, start, schedule) in schedules.items()
        }
        for count, future in enumerate(as_completed(jobs), 1):
            key = jobs[future]
            name, setting, start, _ = schedules[key]
            outcome = future.result()
            check_execution(folder / f"{key}.npz", outcome, starts[setting][start], networks[name],
                            settings[setting], deadlines[name], walking["goal_radius"])
            executions[key] = outcome
            print(f"{count}/{len(jobs)} {key}: {outcome['failure'] or 'completed'}", flush=True)
    write_json(output / "executions.json", dict(sorted(executions.items())))
    report = summarize(plans, predictions, executions, spec, lock["thermal"], calibrated)
    write_json(output / "summary.json", report)
    print(json.dumps(report, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=DEFAULT_CONFIG, output=DEFAULT_OUTPUT)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.config, args.output, args.reference, args.workers)


if __name__ == "__main__":
    main()
