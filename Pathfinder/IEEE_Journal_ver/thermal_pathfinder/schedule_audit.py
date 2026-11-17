"""Exhaustively replay available schedules for the adverse reactive-planning cases."""

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path

from .margin_profiles import digest
from .mission_completion import replay
from .mission_profiles import design
from .network_study import write_json
from .reactive_forecast import ProgressForecast
from .reactive_margin import Margins
from .reactive_margin_study import verify_calibration
from .reactive_study import check_execution, load_inputs

COMPARISONS = {
    "reactive_forecast": ("stitched_nominal", "progress_reactive"),
    "reactive_margin_transfer": ("reactive_fixed", "reactive_calibrated"),
}


def adverse_cases(plans, runs, comparison):
    cases = {}
    for plan in plans:
        case = tuple(plan[field] for field in ("map", "setting", "start"))
        cases.setdefault(case, {})[plan["method"]] = plan
    for case, methods in cases.items():
        baseline, newer = (methods[name] for name in comparison)
        before, after = (runs.get(row["execution"], {}) for row in (baseline, newer))
        reasons = []
        if before.get("completed") and not after.get("completed"):
            reasons.append("lost_completion")
        if after.get("failure") == "thermal_limit":
            reasons.append("selected_thermal_stop")
        if reasons:
            yield case, reasons, (baseline, newer)


def disposition(peak, elapsed, limit, deadline, margins):
    failed = []
    if peak >= limit - margins.temperature_c:
        failed.append("temperature")
    if elapsed > deadline - margins.deadline_s:
        failed.append("deadline")
    return "+".join(failed) or "admitted"


def summarize(case, rows):
    completed = [row for row in rows if row["outcome"] == "completed"]
    admitted = {}
    for label in rows[0]["screening"]:
        selected = [row for row in rows if row["screening"][label] == "admitted"]
        choice = min(selected, default=None, key=lambda row: (
            row["forecast"]["peak_c"], row["forecast"]["elapsed_s"], tuple(row["schedule"])
        ))
        admitted[label] = {
            "outcomes": dict(Counter(row["outcome"] for row in selected)),
            "finishable_schedules_rejected": dict(Counter(
                row["screening"][label] for row in completed if row["screening"][label] != "admitted"
            )),
            "lowest_forecast_admission": choice["execution"] if choice else None,
            "lowest_forecast_outcome": choice["outcome"] if choice else "no_route",
        }
    case.update({
        "outcomes": dict(Counter(row["outcome"] for row in rows)),
        "forecast_screens": admitted,
        "fastest_observed_finish": min(completed, default=None, key=lambda row: row["elapsed_s"]),
        "coolest_observed_finish": min(completed, default=None, key=lambda row: row["peak_c"]),
        "schedules": rows,
    })


def run(experiments, results, output, workers):
    output.mkdir(parents=True, exist_ok=False)
    folder = output / "missions"
    folder.mkdir()
    source_locks, cases, jobs, rows = {}, [], [], {}
    margin_run = results / "reactive_margin_transfer"
    calibrated = verify_calibration(experiments / "reactive_margin_transfer.json", margin_run,
                                    results / "reactive_forecast")
    policy_margins = {"fixed": Margins(0.50, 0), "calibrated": calibrated, "zero": Margins(0, 0)}
    for name, comparison in COMPARISONS.items():
        reference = results / name
        lock, networks, settings, starts, walking = design(experiments / f"{name}.json")
        spec = lock["study"]
        if json.loads((reference / "manifest.json").read_text()) != json.loads(json.dumps(lock)):
            raise ValueError(f"Original profile provenance has changed for {name}")
        files = ("manifest.json", "plans.json", "executions.json", "schedule_forecasts.json", "edge_profiles.json")
        source_locks[name] = {file: digest(reference / file) for file in files}
        plans, runs, forecasts = (json.loads((reference / file).read_text()) for file in files[1:4])
        walks, profiles, provenance = load_inputs(networks, spec, reference, walking["goal_radius"])
        profile_lock = reference / ("evaluation_manifest.json" if name == "reactive_margin_transfer"
                                    else "forecast_manifest.json")
        if json.loads(profile_lock.read_text())["nominal_profiles"] != provenance:
            raise ValueError(f"Archived profile hashes have changed for {name}")
        source_locks[name][profile_lock.name] = digest(profile_lock)
        deadlines = {row["id"]: row["deadline_s"] for row in spec["maps"]}
        for identity, reasons, plans_for_case in adverse_cases(plans, runs, comparison):
            course, setting, start = identity
            network, thermal, initial, deadline = networks[course], settings[setting], starts[setting][start], deadlines[course]
            predictor = ProgressForecast(network, profiles[course], thermal, spec, walking["goal_radius"])
            stages = [[action for action in walks[course] if action.edge.stage == stage] for stage in network.edges]
            case_rows = []
            for schedule in product(*stages):
                key = "_".join((*identity, *(action.name for action in schedule)))
                prediction = predictor.predict(schedule, initial, True)
                if key in forecasts:
                    saved = forecasts[key]["progress_reactive"]
                    if any(saved[field] != value for field, value in asdict(prediction).items()):
                        raise ValueError(f"Forecast changed for reused execution {key}")
                row = {
                    "execution": key, "schedule": [action.name for action in schedule], "forecast": asdict(prediction),
                    "screening": {label: disposition(prediction.peak_c, prediction.elapsed_s, thermal.limit_c,
                                                      deadline, margins) for label, margins in policy_margins.items()},
                }
                mission = (network, schedule, spec, deadline, walking, thermal, initial)
                if key in runs:
                    previous = runs[key]
                    path = reference / previous["trace"]
                    add_outcome(row, previous, path, mission, output, "archive")
                else:
                    jobs.append((row, mission, folder / f"{key}.npz"))
                rows[key] = row
                case_rows.append(row)
            cases.append(({
                "reference": name, "map": course, "setting": setting, "start": start, "reasons": reasons,
                "deadline_s": deadline, "physical_limit_c": thermal.limit_c, "original_plans": {
                    plan["method"]: {
                        "execution": plan["execution"], "planning_failure": plan["planning_failure"],
                        "outcome": (runs[plan["execution"]]["failure"] or "completed") if plan["execution"] else None,
                    } for plan in plans_for_case
                },
            }, case_rows))
    archive_hashes = {key: row["trace_sha256"] for key, row in rows.items() if row.get("origin") == "archive"}
    write_json(output / "manifest.json", {
        "source_sha256": digest(Path(__file__)), "references_sha256": source_locks,
        "calibration_sha256": digest(margin_run / "calibration.json"),
        "margins": {label: asdict(margins) for label, margins in policy_margins.items()},
        "archived_trace_sha256": archive_hashes, "new_schedule_ids": [row["execution"] for row, _, _ in jobs],
    })
    print(f"{len(cases)} cases, {len(rows)} schedules, {len(jobs)} new replays", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(replay, *mission, path): (row, mission, path) for row, mission, path in jobs}
        for count, future in enumerate(as_completed(pending), 1):
            row, mission, path = pending[future]
            add_outcome(row, future.result(), path, mission, output, "new")
            print(f"{count}/{len(pending)} {row['execution']}: {row['outcome']}", flush=True)
    for case, case_rows in cases:
        summarize(case, case_rows)
    report = {"schedule_count": len(rows), "new_replays": len(jobs), "archived_replays": len(archive_hashes),
              "cases": [case for case, _ in cases]}
    write_json(output / "summary.json", report)
    print(json.dumps([{k: case[k] for k in ("map", "setting", "start", "outcomes", "forecast_screens")}
                      for case, _ in cases], indent=2))


def add_outcome(row, outcome, path, mission, output, origin):
    network, _, _, deadline, walking, settings, initial = mission
    check_execution(path, outcome, initial, network, settings, deadline, walking["goal_radius"])
    row.update({
        "outcome": outcome["failure"] or "completed", "peak_c": outcome["peak_c"], "elapsed_s": outcome["elapsed_s"],
        "forward_m": outcome["forward_m"], "slowdown_events": outcome["slowdown_events"],
        "origin": origin, "trace": str(path.relative_to(output)) if origin == "new" else str(path),
        "trace_sha256": digest(path),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", type=Path, default=Path("experiments"))
    parser.add_argument("--references", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/schedule_audit"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.experiments, args.references, args.output, args.workers)


if __name__ == "__main__":
    main()
