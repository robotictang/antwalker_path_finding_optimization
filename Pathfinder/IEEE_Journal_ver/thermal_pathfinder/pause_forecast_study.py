"""Evaluate a per-motor pause forecast on archived schedules and new courses."""

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
import json
from pathlib import Path
from statistics import mean

import numpy as np

from .junction_pause import replay_pause
from .margin_profiles import digest
from .mission_analysis import paired_result
from .mission_profiles import arguments, design
from .model import JOINT_NAMES
from .network_study import write_json
from .pause_forecast import PauseForecast, equivalent_squared_torque
from .reactive_study import check_execution, choose_progress, load_inputs

METHODS = ("fixed_reactive", "time_only_fallback", "pause_forecast_fallback")


def read(path):
    return json.loads(path.read_text())


def identify_load(config, pilot, duration):
    manifest = read(pilot / "manifest.json")
    spec = manifest["study"]
    _, _, thermal, _, _ = design(config.with_name(spec["source_config"]))
    settings = thermal[spec["setting"]]
    by_approach = defaultdict(list)
    traces = {}
    for row in read(pilot / "summary.json")["schedules"]:
        if row["pause_s"] != duration or row["pause"] is None:
            continue
        path = pilot / row["trace"]
        if digest(path) != row["trace_sha256"]:
            raise ValueError(f"Development trial changed: {path}")
        hold = row["pause"]
        before, after = (np.asarray(hold[f"temperature_{phase}_c"]) for phase in ("before", "after"))
        duration_s = hold["resumed_s"] - hold["started_s"]
        by_approach[row["schedule"][0]].append(equivalent_squared_torque(before, after, duration_s, settings))
        traces[row["trace"]] = row["trace_sha256"]
    if not by_approach:
        raise ValueError("Missing completed pause windows in the development set")
    load = np.mean([np.mean(group, axis=0) for group in by_approach.values()], axis=0)
    weights = {approach: len(rows) for approach, rows in by_approach.items()}
    return load, {"approach_counts": weights, "traces_sha256": traces,
                  "squared_torque_nm2": dict(zip(JOINT_NAMES, load.tolist(), strict=True)),
                  "development_summary_sha256": digest(pilot / "summary.json")}


def archive_diagnostic(config, references, transfer, load, duration, margin):
    cases = read(transfer / "summary.json")["cases"]
    rows = []
    for reference in sorted({row["reference"] for row in cases}):
        root = references / reference
        lock, networks, thermal, starts, walking = design(config.with_name(f"{reference}.json"))
        if read(root / "manifest.json") != json.loads(json.dumps(lock)):
            raise ValueError("Archive simulator provenance changed")
        spec = lock["study"] | {"pause_s": duration}
        walks, profiles, _ = load_inputs(networks, spec, root, walking["goal_radius"])
        for case in cases:
            if case["reference"] != reference or not case["schedule"]:
                continue
            name, setting, start = (case[field] for field in ("map", "setting", "start"))
            path = Path(case["pause"]["trace"])
            if digest(path) != case["pause"]["trace_sha256"]:
                raise ValueError(f"Archived evaluation replay changed: {path}")
            options = {action.name: action for action in walks[name]}
            schedule = tuple(options[action] for action in case["schedule"])
            settings = thermal[setting]
            predictor = PauseForecast(networks[name], profiles[name], settings, spec, walking["goal_radius"], load)
            initial = starts[setting][start]
            predicted = predictor.predict_pause(schedule, initial)
            no_pause = predictor.predict(schedule, initial, True)
            actual = case["pause"]
            arrived = actual["pause"]
            if arrived:
                entry = np.asarray(arrived["temperature_before_c"])
                observed_exit = np.asarray(arrived["temperature_after_c"])
                exit_estimate = settings.advance(entry, np.sqrt(load), arrived["resumed_s"] - arrived["started_s"])
                local_error = float(np.abs(exit_estimate - observed_exit).mean())
            else:
                local_error = None
            rows.append({
                "map": name, "setting": setting, "start": start,
                "actual_outcome": actual["failure"] or "completed", "actual_elapsed_s": actual["elapsed_s"],
                "actual_peak_c": actual["peak_c"], "observed_pause_exit_peak_c": arrived["peak_after_c"] if arrived else None,
                "observed_entry_conditioned_motor_mae_c": local_error,
                "time_only_s": no_pause.elapsed_s + duration, "pause_forecast": asdict(predicted),
                "time_only_admits": no_pause.elapsed_s + duration <= case["deadline_s"],
                "thermal_forecast_admits": predicted.elapsed_s <= case["deadline_s"] and predicted.peak_c < settings.limit_c - margin,
            })
    finished = [row for row in rows if row["actual_outcome"] == "completed"]
    reached = [row for row in rows if row["observed_pause_exit_peak_c"] is not None]
    screens = {
        key: dict(Counter(f"{'admit' if row[key] else 'reject'}/{row['actual_outcome']}" for row in rows))
        for key in ("time_only_admits", "thermal_forecast_admits")
    }
    return {
        "schedules": len(rows), "finished": len(finished), "reached_pause": len(reached), "screening": screens,
        "completed_peak_mae_c": mean(abs(row["actual_peak_c"] - row["pause_forecast"]["peak_c"]) for row in finished),
        "completed_pause_time_mae_s": mean(abs(row["actual_elapsed_s"] - row["pause_forecast"]["elapsed_s"]) for row in finished),
        "completed_time_only_mae_s": mean(abs(row["actual_elapsed_s"] - row["time_only_s"]) for row in finished),
        "hold_exit_hottest_mae_c": mean(abs(row["observed_pause_exit_peak_c"] - row["pause_forecast"]["pause_exit_peak_c"])
                                       for row in reached),
        "hold_exit_motor_mae_c_given_observed_entry": mean(row["observed_entry_conditioned_motor_mae_c"] for row in reached),
        "cases": rows,
    }


def summary(plans, executions, spec):
    by_method, by_map = {}, {course["id"]: {} for course in spec["maps"]}
    for method in METHODS:
        selected = [row for row in plans if row["method"] == method]
        outcomes = [executions[row["execution"]]["failure"] or "completed" if row["execution"] else row["planning_failure"]
                    for row in selected]
        by_method[method] = {"outcomes": dict(Counter(outcomes)),
                             "max_planning_s": max(row["planning_s"] for row in selected)}
        for name in by_map:
            by_map[name][method] = [outcome == "completed" for row, outcome in zip(selected, outcomes, strict=True)
                                   if row["map"] == name]
    effects = {}
    for method in METHODS[:-1]:
        result = paired_result([(row[method], row[METHODS[-1]]) for row in by_map.values()], spec["bootstrap_seed"])
        result["pause_forecast_only"] = result.pop("per_motor_only")
        result["baseline_only"] = result.pop("anonymous_only")
        stops = by_method[METHODS[-1]]["outcomes"].get("thermal_limit", 0) - by_method[method]["outcomes"].get("thermal_limit", 0)
        result["additional_thermal_stops"] = stops
        result["meets_completion_target_without_more_stops"] = result["mean_gain_pp"] >= spec["minimum_gain_pp"] and stops <= 0
        effects[method] = result
    return {"starts": len(plans) // len(METHODS), "decisions": len(plans), "replays": len(executions),
            "by_method": by_method,
            "completed_by_map": {name: {method: sum(values) for method, values in group.items()}
                                 for name, group in by_map.items()},
            "comparisons": effects}


class PauseOnly:
    def __init__(self, predictor):
        self.predictor = predictor

    def predict(self, schedule, initial, _):
        return self.predictor.predict_pause(schedule, initial)


def run(config, output, references, workers):
    lock, networks, thermal, starts, walking = design(config)
    if read(output / "manifest.json") != json.loads(json.dumps(lock)):
        raise ValueError("Held-out nominal profiles do not match the current design")
    spec = lock["study"]
    duration, margin = spec["pause_s"], spec["thermal_margin_c"]
    pilot = references / "junction_pause"
    transfer = references / "junction_pause_transfer"
    load, provenance = identify_load(config, pilot, duration)
    # Freeze the model and selection gates before evaluating any paused replay.
    write_json(output / "pause_model.json", provenance | {
        "pause_s": duration, "thermal_margin_c": margin, "held_out_config_sha256": digest(config),
        "sources_sha256": {name: digest(Path(__file__).with_name(name)) for name in (
            "pause_forecast.py", "pause_forecast_study.py", "junction_pause.py", "reactive_forecast.py", "reactive_study.py"
        )},
    })
    diagnostic = archive_diagnostic(config, references, transfer, load, duration, margin)
    write_json(output / "archived_evaluation.json", diagnostic | {"reference_sha256": digest(transfer / "summary.json")})
    print("Archived evaluation", json.dumps({k: v for k, v in diagnostic.items() if k != "cases"}), flush=True)

    folder = output / "missions"
    folder.mkdir(exist_ok=False)
    walks, profiles, hashes = load_inputs(networks, spec, output, walking["goal_radius"])
    write_json(output / "evaluation_manifest.json", {"profile_hashes": hashes,
                                                    "pause_model_sha256": digest(output / "pause_model.json")})
    deadlines = {course["id"]: course["deadline_s"] for course in spec["maps"]}
    plans, jobs = [], {}
    for name, network in networks.items():
        deadline = deadlines[name]
        for setting, settings in thermal.items():
            predictor = PauseForecast(network, profiles[name], settings, spec, walking["goal_radius"], load)
            pause = PauseOnly(predictor)
            ceiling = settings.limit_c - margin
            budget = spec["planning_budget_s"]
            actions = walks[name]
            for start, initial in starts[setting].items():
                initial_plan = choose_progress(network, predictor, initial, deadline, ceiling, budget, actions, True)
                for method in METHODS:
                    result = initial_plan
                    hold = 0.0
                    estimate_s = initial_plan[3]
                    if method != METHODS[0] and initial_plan[5] == "no_route":
                        # Include the baseline search in the same two-second decision budget.
                        search, due, cap = ((predictor, deadline - duration, float("inf")) if method == METHODS[1]
                                            else (pause, deadline, ceiling))
                        result = choose_progress(network, search, initial, due, cap, budget - estimate_s, actions, True)
                        estimate_s += result[3]
                        hold = duration
                    schedule, peak, elapsed, _, examined, failure = result
                    key = "_".join((name, setting, start, *(a.name for a in schedule), f"pause{hold:g}")) if schedule else None
                    plans.append({"map": name, "setting": setting, "start": start, "method": method,
                                  "schedule": [a.name for a in schedule], "pause_s": hold,
                                  "predicted_peak_c": peak if method != METHODS[1] or not hold else None,
                                  "predicted_elapsed_s": elapsed + duration if elapsed is not None and method == METHODS[1] and hold else elapsed,
                                  "planning_s": estimate_s, "planning_failure": failure,
                                  "schedules_examined_in_final_search": examined, "execution": key})
                    if schedule:
                        jobs[key] = (network, schedule, spec, deadline, walking, settings, initial,
                                     float(network.junctions[1]), hold, folder / f"{key}.npz")
        print(f"Planned {name}", flush=True)
    write_json(output / "plans.json", plans)
    executions = {}
    print(f"{len(plans)} decisions, {len(jobs)} new replays", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(replay_pause, *mission): key for key, mission in jobs.items()}
        for index, future in enumerate(as_completed(pending), 1):
            key = pending[future]
            record = future.result()
            network, _, _, deadline, walking, settings, initial, _, _, path = jobs[key]
            check_execution(path, record, initial, network, settings, deadline, walking["goal_radius"])
            executions[key] = record | {"trace_sha256": digest(path)}
            print(f"{index}/{len(jobs)} {key}: {record['failure'] or 'completed'}", flush=True)
    write_json(output / "executions.json", dict(sorted(executions.items())))
    result = summary(plans, executions, spec)
    write_json(output / "summary.json", result)
    print(json.dumps(result, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=Path("experiments/pause_forecast.json"), output=Path("results/pause_forecast"))
    parser.add_argument("--references", type=Path, default=Path("results"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.config, args.output, args.references, args.workers)


if __name__ == "__main__":
    main()
