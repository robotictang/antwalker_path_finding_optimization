"""Diagnose completion disagreements using matched schedules with and without slowdown."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path

import numpy as np

from .audit_network import require
from .margin_profiles import digest
from .mission_completion import METHODS, choose_route, forecast, replay as adaptive_replay
from .mission_profiles import design
from .network_planning import EdgeThermalModel
from .network_study import write_json
from .route_speed_study import read_profiles, replay as fixed_schedule_replay
from .walking import STAND_SECONDS


def selected_cases(plans, runs):
    pairs = {}
    for plan in plans:
        key = tuple(plan[field] for field in ("map", "setting", "start"))
        pairs.setdefault(key, {})[plan["method"]] = plan
    for key, methods in pairs.items():
        selected = [methods[method] for method in METHODS]
        completed = [bool(plan["execution"] and runs[plan["execution"]]["completed"]) for plan in selected]
        if completed[0] != completed[1]:
            yield key, selected


def execution_summary(record, path, sample_s, deadline):
    with np.load(path) as trace:
        temperatures = trace["temperature_c"]
        body = trace["body_xyz_m"]
        require(len(temperatures) == len(body) + 1, f"Invalid trace lengths: {path.name}")
        require(np.isclose(temperatures.max(), record["peak_c"]), f"Peak mismatch: {path.name}")
        require(np.isclose(len(body) * sample_s, record["elapsed_s"]), f"Duration mismatch: {path.name}")
    events = record.get("slowdown_events", [])
    return {
        "outcome": record["failure"] or "completed", "peak_c": record["peak_c"],
        "elapsed_s": record["elapsed_s"], "deadline_s": deadline,
        "goal_time_s": record["elapsed_s"] if record["completed"] else None,
        "first_slowdown_trigger_s": events[0]["walking_time_s"] + STAND_SECONDS if events else None,
        "trace": str(path),
    }


def run(config, reference, output, workers):
    lock, networks, thermal, starts, walking = design(config)
    require(json.loads((reference / "manifest.json").read_text()) == json.loads(json.dumps(lock)),
            "Reference profiles do not match source or design")
    plans = json.loads((reference / "plans.json").read_text())
    runs = json.loads((reference / "executions.json").read_text())
    spec = lock["study"]
    maps = {item["id"]: item for item in spec["maps"]}
    profiles, _ = read_profiles(reference, networks, spec["speed_fractions"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "missions").mkdir()
    write_json(output / "manifest.json", {
        "source_sha256": digest(Path(__file__)), "selection": "all original completed-versus-incomplete pairs",
        "reference_sha256": {name: digest(reference / name) for name in
                             ("manifest.json", "plans.json", "executions.json", "edge_profiles.json")},
        "comparison": "same starting state and schedule; remove reactive speed override only",
    })
    cases = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {}
        for (name, setting, start), plans_for_case in selected_cases(plans, runs):
            initial = starts[setting][start]
            settings = thermal[setting]
            network = networks[name]
            deadline = maps[name]["deadline_s"]
            models = {action: EdgeThermalModel.from_walk(walk, settings)
                      for action, walk in profiles[name].items() if walk.completed}
            actions = {(action.edge.name, action.fraction): action for action in models}
            schedule_records = {}
            methods = {}
            for plan in plans_for_case:
                method = plan["method"]
                if plan["execution"]:
                    schedule = tuple(actions[key] for key in zip(plan["route"], plan["speed_fractions"], strict=True))
                    schedule_records[schedule] = plan["execution"]
                    methods[method] = {"schedule": [action.name for action in schedule]}
                else:
                    methods[method] = {"planning_failure": plan["planning_failure"]}
                hypotheses = tuple(starts[setting].values()) if method == METHODS[0] else (initial,)
                best, peak, _, _, _, failure = choose_route(
                    network, models, hypotheses, deadline, 1e6, spec["planning_budget_s"]
                )
                require(failure != "planning_timeout", "Diagnostic search exceeded original planning budget")
                methods[method].update({
                    "lowest_forecast_c": peak,
                    "would_admit_at_zero_margin": peak is not None and peak < settings.limit_c,
                    "lowest_forecast_schedule": [action.name for action in best],
                })
                if not plan["execution"] and best:
                    schedule_records.setdefault(best, None)
            by_schedule = []
            for schedule, saved_key in schedule_records.items():
                prefix = "_".join((name, setting, start, *(action.name for action in schedule)))
                active_peak = forecast(schedule, models, initial)
                row = {
                    "schedule": [action.name for action in schedule],
                    "stitched_forecast_c": active_peak,
                    "stitched_time_s": sum(models[action].elapsed_s for action in schedule),
                    "would_admit_labeled_at_0_5": active_peak < settings.limit_c - spec["thermal_margin_c"],
                    "would_admit_labeled_at_zero": active_peak < settings.limit_c,
                }
                if saved_key:
                    saved = runs[saved_key]
                    row["adaptive"] = execution_summary(
                        saved, reference / saved["trace"], lock["sample_interval_s"], deadline
                    )
                else:
                    path = output / "missions" / f"{prefix}_adaptive.npz"
                    task = pool.submit(adaptive_replay, network, schedule, spec, deadline, walking, settings, initial, path)
                    jobs[task] = row, "adaptive", path, deadline
                path = output / "missions" / f"{prefix}_scheduled_only.npz"
                task = pool.submit(fixed_schedule_replay, network, schedule, spec, deadline, walking, settings, initial, path)
                jobs[task] = row, "scheduled_only", path, deadline
                by_schedule.append(row)
            cases.append({"map": name, "setting": setting, "start": start, "methods": methods, "schedules": by_schedule})
        print(f"{len(cases)} disagreements, {len(jobs)} new replays", flush=True)
        for future in as_completed(jobs):
            row, policy, path, deadline = jobs[future]
            row[policy] = execution_summary(future.result(), path, lock["sample_interval_s"], deadline)
            print(f"{path.stem}: {row[policy]['outcome']}", flush=True)
    write_json(output / "summary.json", {"cases": cases, "new_replays": len(jobs)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/mission_completion.json"))
    parser.add_argument("--reference", type=Path, default=Path("results/mission_completion"))
    parser.add_argument("--output", type=Path, default=Path("results/discordant_replays"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.reference, args.output, args.workers)


if __name__ == "__main__":
    main()
