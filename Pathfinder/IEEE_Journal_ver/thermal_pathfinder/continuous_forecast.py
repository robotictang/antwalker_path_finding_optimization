"""Compare stitched branch forecasts with continuous nominal route forecasts."""

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
from statistics import mean
from types import SimpleNamespace

import numpy as np

from .audit_network import require
from .connected_walk import walk_branch
from .margin_study import arguments, verified_design
from .network_planning import EdgeThermalModel
from .network_study import write_json
from .route_speed_study import SpeedAction, SpeedSchedule
from .walking import SAMPLE_SECONDS


def mission_schedule(network, plan):
    edges = {edge.name: edge for stage in network.edges.values() for edge in stage}
    return tuple(SpeedAction(edges[name], fraction)
                 for name, fraction in zip(plan["route"], plan["speed_fractions"], strict=True))


def profile_route(network, schedule, spec, walking, path):
    route = network.route(tuple(action.edge for action in schedule))
    policy = SpeedSchedule(tuple(network.junctions[1:-1]), tuple(action.fraction for action in schedule),
                           spec["transition_s"])
    walk = walk_branch(route, **walking, deadline=spec["deadline_s"], position_speed_policy=policy)
    np.savez_compressed(path, torque_nm=walk.torques, body_xyz_m=walk.body_xyz_m,
                        foot_contacts=walk.foot_contacts)
    return {"trace": path.name, "completed": walk.completed, "failure": walk.failure,
            "elapsed_s": walk.elapsed_s, "junction_events": policy.events}


def paired_error_metrics(rows):
    """Measure peak errors only on walks that reached the goal."""
    complete = [row for row in rows if row["outcome"] == "completed"
                and row["continuous_predicted_peak_c"] is not None]
    result = {"paired_finishes": len(complete)}
    for name in ("branch", "continuous"):
        errors = [row["observed_peak_c"] - row[f"{name}_predicted_peak_c"] for row in complete]
        result[name] = {
            "mean_absolute_error_c": mean(abs(error) for error in errors) if errors else None,
            "mean_observed_minus_predicted_c": mean(errors) if errors else None,
            "maximum_underprediction_c": max(0, max(errors)) if errors else None,
        }
    result["continuous_closer"] = sum(
        abs(row["observed_peak_c"] - row["continuous_predicted_peak_c"]) + 1e-9
        < abs(row["observed_peak_c"] - row["branch_predicted_peak_c"]) for row in complete
    )
    result["branch_closer"] = sum(
        abs(row["observed_peak_c"] - row["branch_predicted_peak_c"]) + 1e-9
        < abs(row["observed_peak_c"] - row["continuous_predicted_peak_c"]) for row in complete
    )
    return result


def screen(rows, margins):
    results = {}
    for name in ("branch", "continuous"):
        results[name] = []
        for margin in margins:
            counts = Counter(admitted=0, completed=0, thermal_stops=0,
                             other_failures=0, finishable_rejected=0, no_forecast=0)
            for row in rows:
                peak = row[f"{name}_predicted_peak_c"]
                if peak is None:
                    counts["no_forecast"] += 1
                if peak is not None and peak < row["limit_c"] - margin:
                    counts["admitted"] += 1
                    counts["completed"] += row["outcome"] == "completed"
                    counts["thermal_stops"] += row["outcome"] == "thermal_limit"
                    counts["other_failures"] += row["outcome"] not in ("completed", "thermal_limit")
                elif row["outcome"] == "completed":
                    counts["finishable_rejected"] += 1
            results[name].append({"margin_c": margin, **counts})
    return results


def run(config, development, reference, source, output, workers):
    lock, networks, settings, starts, walking = verified_design(config, development, reference, source)
    spec = lock["study"]
    runs = json.loads((source / "executions.json").read_text())
    plans = json.loads((source / "plans.json").read_text())
    unique, routes = {}, {}
    for plan in plans:
        key = plan["execution"]
        if not key:
            continue
        signature = (plan["map"], mission_schedule(networks[plan["map"]], plan))
        record = (signature, plan["start"], plan["setting"], plan["predicted_peak_c"])
        require(unique.setdefault(key, record) == record, f"Conflicting inputs for {key}")
        if signature not in routes:
            name, actions = signature
            routes[signature] = "_".join((name, *(action.name for action in actions)))
    require(set(unique) == set(runs), "Execution keys do not match plans")
    output.mkdir(parents=True, exist_ok=False)
    profiles = output / "profiles"
    profiles.mkdir()
    inputs = (source / "manifest.json", source / "plans.json", source / "executions.json",
              source / "summary.json", Path(__file__))
    write_json(output / "manifest.json", {
        "input_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
        "source_study": spec["name"], "margins_c": spec["margin_grid_c"],
        "profiles": sorted(routes.values()),
    })

    records = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {
            pool.submit(profile_route, networks[name], schedule, spec, walking, profiles / f"{route_id}.npz"):
                route_id for (name, schedule), route_id in routes.items()
        }
        for index, future in enumerate(as_completed(pending), 1):
            route_id = pending[future]
            records[route_id] = future.result()
            print(f"{index}/{len(pending)} {route_id}: {records[route_id]['failure'] or 'completed'}", flush=True)
    write_json(output / "profiles.json", dict(sorted(records.items())))

    rows, models = [], {}
    for execution, (signature, start, setting, branch_peak) in sorted(unique.items()):
        name, schedule = signature
        route_id = routes[signature]
        record = records[route_id]
        model_key = route_id, setting
        continuous_peak = None
        if record["completed"]:
            if model_key not in models:
                with np.load(profiles / record["trace"]) as trace:
                    torque, xyz, contacts = (trace[key] for key in ("torque_nm", "body_xyz_m", "foot_contacts"))
                    require(len(torque) == len(xyz) == len(contacts)
                            and np.isclose(len(torque) * SAMPLE_SECONDS, record["elapsed_s"]),
                            f"Malformed profile {route_id}")
                    require(np.linalg.norm(xyz[-1, :2] - [networks[name].junctions[-1], 0])
                            <= walking["goal_radius"], f"Profile missed goal {route_id}")
                    require(len(record["junction_events"]) == len(schedule) - 1, f"Missing junction {route_id}")
                    profile = SimpleNamespace(completed=True, torques=torque, elapsed_s=record["elapsed_s"])
                models[model_key] = EdgeThermalModel.from_walk(profile, settings[setting])
            _, continuous_peak = models[model_key].propagate(starts[start])
        observed = runs[execution]
        rows.append({
            "execution": execution, "map": name, "setting": setting, "start": start, "route": route_id,
            "branch_predicted_peak_c": branch_peak, "continuous_predicted_peak_c": continuous_peak,
            "observed_peak_c": observed["peak_c"], "outcome": observed["failure"] or "completed",
            "limit_c": settings[setting].limit_c,
        })
    write_json(output / "forecasts.json", rows)
    by_course = {name: [row for row in rows if row["map"] == name] for name in networks}
    report = {
        "continuous_profiles": len(records),
        "profile_outcomes": dict(Counter(row["failure"] or "completed" for row in records.values())),
        "thermal_replays": len(rows),
        "replay_outcomes": dict(Counter(row["outcome"] for row in rows)),
        "paired_peak_errors": paired_error_metrics(rows),
        "screen": screen(rows, spec["margin_grid_c"]),
        "by_course": {name: {"paired_peak_errors": paired_error_metrics(subset),
                             "screen": screen(subset, spec["margin_grid_c"])}
                      for name, subset in by_course.items()},
    }
    write_json(output / "summary.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "by_course"}, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=Path("experiments/thermal_margin_transfer.json"),
                        output=Path("results/continuous_forecast_transfer"))
    parser.add_argument("--source", type=Path, default=Path("results/thermal_margin_transfer"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.development, args.reference, args.source, args.output, args.workers)


if __name__ == "__main__":
    main()
