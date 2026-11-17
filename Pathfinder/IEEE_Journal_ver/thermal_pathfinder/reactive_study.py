"""Compare route decisions from scheduled and reactive forecasts on fixed new courses."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
from statistics import median
from time import perf_counter
from types import SimpleNamespace

import numpy as np

from .margin_profiles import digest
from .mission_analysis import paired_result
from .mission_completion import choose_route, forecast, replay
from .mission_profiles import arguments, design
from .network_planning import EdgeThermalModel
from .network_study import write_json
from .reactive_forecast import Prediction, ProgressForecast, ProgressProfile
from .route_speed_profiles import trace_name
from .route_speed_study import SpeedAction
from .walking import SAMPLE_SECONDS

METHODS = ("stitched_nominal", "progress_scheduled", "progress_reactive")


def load_inputs(networks, spec, output, goal_radius):
    records = json.loads((output / "edge_profiles.json").read_text())
    walks, profiles, provenance = {}, {}, {}
    fractions = spec["speed_fractions"]
    used_records = set()
    for name, network in networks.items():
        walks[name], profiles[name] = {}, {}
        for stage, edges in network.edges.items():
            length = network.junctions[stage + 1] - network.junctions[stage]
            for edge in edges:
                filenames = [trace_name(name, edge, fraction) for fraction in fractions]
                used_records.update(filenames)
                supported = all(records[filename]["completed"] for filename in filenames)
                for fraction, filename in zip(fractions, filenames, strict=True):
                    path = output / "profiles" / filename
                    provenance[filename] = {
                        "sha256": digest(path), "common_candidate": supported,
                        "outcome": records[filename]["failure"] or "completed",
                    }
                    with np.load(path) as trace:
                        positions, torque = trace["body_xyz_m"], trace["torque_nm"]
                        elapsed = records[filename]["elapsed_s"]
                        if (len(positions) != len(torque) or not np.isclose(elapsed, len(torque) * SAMPLE_SECONDS)
                                or not np.isfinite(torque).all() or not np.isfinite(positions).all()):
                            raise ValueError(f"Malformed nominal profile {path}")
                        if records[filename]["completed"] and np.linalg.norm(positions[-1, :2] - [length, 0]) > goal_radius:
                            raise ValueError(f"Nominal profile missed the goal {path}")
                        if supported:
                            action = SpeedAction(edge, fraction)
                            walks[name][action] = SimpleNamespace(completed=True, torques=torque, elapsed_s=elapsed)
                            profiles[name][action] = ProgressProfile.from_trace(
                                trace, length - goal_radius, spec["progress_bin_m"]
                            )
    if used_records != set(records):
        raise ValueError("Unexpected records in the nominal profile index")
    return walks, profiles, provenance


def choose_progress(network, predictor, initial, deadline, ceiling, budget, actions, with_slowdown):
    started = perf_counter()
    stages = [[action for action in actions if action.edge.stage == stage] for stage in network.edges]
    best = None
    examined = 0
    for schedule in product(*stages):
        if perf_counter() - started >= budget:
            return (), None, None, perf_counter() - started, examined, "planning_timeout"
        prediction = predictor.predict(schedule, initial, with_slowdown)
        examined += 1
        key = (prediction.peak_c, prediction.elapsed_s, tuple(action.name for action in schedule))
        if prediction.elapsed_s <= deadline and prediction.peak_c < ceiling and (best is None or key < best[0]):
            best = (key, schedule)
    duration = perf_counter() - started
    if duration >= budget:
        return (), None, None, duration, examined, "planning_timeout"
    if best is None:
        return (), None, None, duration, examined, "no_route"
    return best[1], best[0][0], best[0][1], duration, examined, None


def check_execution(path, outcome, start, network, settings, deadline, goal_radius):
    with np.load(path) as trace:
        temp, body, torque = (trace[field] for field in ("temperature_c", "body_xyz_m", "torque_nm"))
    if (len(temp) != len(body) + 1 or len(body) != len(torque)
            or not np.isclose(len(body) * SAMPLE_SECONDS, outcome["elapsed_s"])
            or not np.array_equal(temp[0], start) or not np.isclose(temp.max(), outcome["peak_c"])):
        raise ValueError(f"Inconsistent execution trace {path}")
    if outcome["completed"] and (
        np.linalg.norm(body[-1, :2] - [network.junctions[-1], 0]) > goal_radius
        or temp.max() >= settings.limit_c or outcome["elapsed_s"] > deadline + 1e-6
        or len(outcome["junction_events"]) != len(network.sections) - 1
    ):
        raise ValueError(f"Invalid completion {path}")
    if outcome["failure"] == "thermal_limit" and temp[-1].max() < settings.limit_c:
        raise ValueError(f"Invalid thermal stop {path}")


def summarize(plans, predictions, executions, spec):
    def outcome(plan):
        run = executions.get(plan["execution"])
        return (run["failure"] or "completed") if run is not None else plan["planning_failure"]

    by_method = {}
    by_map = {item["id"]: {} for item in spec["maps"]}
    for method in METHODS:
        subset = [plan for plan in plans if plan["method"] == method]
        by_method[method] = {
            "outcomes": dict(Counter(outcome(plan) for plan in subset)),
            "maximum_planning_s": max(plan["planning_s"] for plan in subset),
            "median_planning_s": median(plan["planning_s"] for plan in subset),
        }
        for name in by_map:
            by_map[name][method] = [outcome(plan) == "completed" for plan in subset if plan["map"] == name]

    comparisons = {}
    for baseline in METHODS[:2]:
        effect = paired_result([(item[baseline], item[METHODS[2]]) for item in by_map.values()],
                               spec["bootstrap_seed"])
        effect["reactive_only"] = effect.pop("per_motor_only")
        effect["baseline_only"] = effect.pop("anonymous_only")
        effect["meets_10_point_target"] = effect["mean_gain_pp"] >= spec["minimum_gain_pp"]
        comparisons[baseline] = effect

    screening = {}
    for method in METHODS:
        counts = Counter()
        errors = {"peak_c": [], "elapsed_s": []}
        trigger_timing_errors = []
        for key, alternatives in predictions.items():
            pred = alternatives[method]
            run = executions[key]
            status = run["failure"] or "completed"
            counts[f"{'admit' if pred['admissible'] else 'reject'}/{status}"] += 1
            if run["completed"]:
                for metric in errors:
                    errors[metric].append(abs(pred[metric] - run[metric]))
            if method == METHODS[2]:
                observed = run["slowdown_events"]
                predicted = pred["first_trigger_s"]
                counts[f"trigger observed={bool(observed)} predicted={predicted is not None}"] += 1
                if observed and predicted is not None:
                    trigger_timing_errors.append(abs(predicted - observed[0]["walking_time_s"]))
        screening[method] = {
            "counts": dict(counts), "completed_replays_with_error": len(errors["peak_c"]),
            "mean_abs_peak_error_c": float(np.mean(errors["peak_c"])) if errors["peak_c"] else None,
            "mean_abs_elapsed_error_s": float(np.mean(errors["elapsed_s"])) if errors["elapsed_s"] else None,
            "mean_abs_first_trigger_error_s": float(np.mean(trigger_timing_errors)) if trigger_timing_errors else None,
        }
    return {
        "paired_starts": len(plans) // len(METHODS), "decisions": len(plans),
        "physics_replays": len(executions), "by_method": by_method,
        "completions_by_map": {name: {method: sum(values) for method, values in by_method.items()}
                               for name, by_method in by_map.items()},
        "completion_comparisons": comparisons, "screening_on_common_replays": screening,
    }


def run(config, output, workers):
    lock, networks, settings, starts, walking = design(config)
    if json.loads((output / "manifest.json").read_text()) != json.loads(json.dumps(lock)):
        raise ValueError("Nominal profile manifest does not match current experiment")
    spec = lock["study"]
    deadlines = {item["id"]: item["deadline_s"] for item in spec["maps"]}
    walks, profiles, provenance = load_inputs(networks, spec, output, walking["goal_radius"])
    folder = output / "missions"
    folder.mkdir(exist_ok=False)
    write_json(output / "forecast_manifest.json", {
        "nominal_manifest_sha256": digest(output / "manifest.json"), "profile_index_sha256": digest(output / "edge_profiles.json"),
        "sources": {name: digest(Path(__file__).with_name(name))
                    for name in ("reactive_study.py", "reactive_forecast.py")},
        "methods": METHODS, "nominal_profiles": provenance,
    })
    plans, schedules, predictions = [], {}, {}
    for name, network in networks.items():
        for setting, thermal in settings.items():
            stitched = {action: EdgeThermalModel.from_walk(walk, thermal) for action, walk in walks[name].items()}
            predictor = ProgressForecast(network, profiles[name], thermal, spec, walking["goal_radius"])
            deadline = deadlines[name]
            ceiling = thermal.limit_c - spec["thermal_margin_c"]
            budget = spec["planning_budget_s"]
            # A fastest nominal probe per case gives common screening data even when every planner rejects.
            stages = [[action for action in stitched if action.edge.stage == stage] for stage in network.edges]
            probe = min(product(*stages), default=(),
                        key=lambda route: (sum(stitched[a].elapsed_s for a in route), tuple(a.name for a in route)))
            for start, initial in starts[setting].items():
                choices = [choose_route(network, stitched, (initial,), deadline, ceiling, budget)]
                choices.extend(choose_progress(network, predictor, initial, deadline, ceiling, budget, stitched, enabled)
                               for enabled in (False, True))
                case = (name, setting, start)
                for method, choice in zip(METHODS, choices, strict=True):
                    schedule, peak, duration, planning_s, examined, failure = choice
                    key = "_".join((*case, *(action.name for action in schedule))) if schedule else None
                    plans.append({
                        "map": name, "setting": setting, "start": start, "method": method, "execution": key,
                        "actions": [action.name for action in schedule], "predicted_peak_c": peak,
                        "predicted_elapsed_s": duration, "planning_s": planning_s, "schedules_examined": examined,
                        "planning_failure": failure,
                    })
                selected = dict.fromkeys((probe, *(choice[0] for choice in choices)))
                for schedule in selected:
                    if not schedule:
                        continue
                    key = "_".join((*case, *(action.name for action in schedule)))
                    schedules[key] = (*case, schedule)
                    variants = (Prediction(forecast(schedule, stitched, initial),
                                           sum(stitched[a].elapsed_s for a in schedule), None),
                                predictor.predict(schedule, initial, False),
                                predictor.predict(schedule, initial, True))
                    predictions[key] = {
                        method: asdict(pred) | {"admissible": bool(pred.peak_c < ceiling and pred.elapsed_s <= deadline)}
                        for method, pred in zip(METHODS, variants, strict=True)
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
    result = summarize(plans, predictions, executions, spec)
    write_json(output / "summary.json", result)
    print(json.dumps(result, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=Path("experiments/reactive_forecast.json"), output=Path("results/reactive_forecast"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.config, args.output, args.workers)


if __name__ == "__main__":
    main()
