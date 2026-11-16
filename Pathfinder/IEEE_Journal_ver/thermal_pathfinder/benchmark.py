"""Run the frozen asymmetric-terrain and thermal-parameter benchmark."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from dataclasses import asdict, replace
import hashlib
from itertools import product
import json
from pathlib import Path
import platform
import re

import mujoco
import numpy as np

from .connected_terrain import Branch, ConnectedTerrain
from .connected_walk import walk_branch
from .model import JOINT_NAMES, build_xml
from .pilot import METHODS, mirrored_starts, walk_summary
from .planning import rank_routes
from .thermal import ThermalSettings, ThermalState
from .walking import SAMPLE_SECONDS

ROUTES = {"rises_left": 1, "rises_right": -1}
SOURCE_FILES = ("benchmark", "connected_terrain", "connected_walk", "model", "pilot", "planning",
                "thermal", "walking")


def load_design(config_path):
    spec = json.loads(config_path.read_text())
    base_path = config_path.with_name(spec["base_config"])
    base = json.loads(base_path.read_text())
    maps = {}
    for item in spec["maps"]:
        name = item["id"]
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name in maps:
            raise ValueError(f"Invalid or repeated map ID: {name}")
        options = base["terrain"] | item["terrain"]
        terrain = ConnectedTerrain(**options)
        if (terrain.bank_angle(1) == terrain.bank_angle(-1)
                and terrain.branch_offset(1) == terrain.branch_offset(-1)
                and terrain.left_bank_shift_m == terrain.right_bank_shift_m):
            raise ValueError(f"Expected an asymmetric map: {name}")
        maps[name] = options
    if not maps:
        raise ValueError("Expected at least one map")
    heating = spec["heating_rate_multipliers"]
    cooling = spec["cooling_time_constants_s"]
    if any(not axis or len(axis) != len(set(axis)) for axis in (heating, cooling)):
        raise ValueError("Thermal axes must be nonempty and contain unique values")
    baseline = ThermalSettings(**base["thermal"])
    settings = {
        (heat, tau): replace(
            baseline, time_constant_s=tau,
            rise_at_reference_c=baseline.rise_at_reference_c * heat * tau / baseline.time_constant_s,
        )
        for heat, tau in product(heating, cooling)
    }
    starts = mirrored_starts(base, baseline)
    walking = {
        "speed": base["command_speed_m_s"],
        "deadline": base["deadline_s"],
        "max_lateral": base["max_corridor_drift_m"],
        "goal_radius": base["goal_radius_m"],
    }
    files = [config_path, base_path, *(Path(__file__).with_name(f"{name}.py") for name in SOURCE_FILES)]
    manifest = {
        "study": spec, "base": base, "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files
        },
        "runtime": {"python": platform.python_version(), "mujoco": mujoco.__version__, "numpy": np.__version__},
        "joint_order": JOINT_NAMES, "sample_interval_s": SAMPLE_SECONDS, "methods": METHODS,
        "thermal_settings": [
            {"heating_rate_multiplier": heat, "cooling_time_constant_s": tau, **asdict(value)}
            for (heat, tau), value in settings.items()
        ],
    }
    return manifest, maps, walking, settings, starts


def walk_job(options, side, walking, path, settings=None, initial=None):
    branch = Branch(ConnectedTerrain(**options), side)
    thermal = None if settings is None else ThermalState(settings, initial)
    history = [] if thermal is None else [thermal.temperature_c.copy()]
    walk = walk_branch(branch, **walking, thermal=thermal, temperature_history=history)
    np.savez_compressed(path, torque_nm=walk.torques, body_xyz_m=walk.body_xyz_m,
                        foot_contacts=walk.foot_contacts, temperature_c=np.asarray(history))
    if thermal is None:
        return walk
    return walk_summary(walk) | {
        "peak_c": float(thermal.peak_by_joint_c.max()),
        "trace": f"traces/{path.name}",
        "execution": "physics_replay",
    }


def nominal_execution(profile, settings, initial, path):
    """Reconstruct exact nominal-physics outcomes when derating never activates."""
    thermal = ThermalState(settings, initial)
    history = [thermal.temperature_c.copy()]
    for torque in profile.torques:
        thermal.advance(torque, SAMPLE_SECONDS)
        if thermal.peak_by_joint_c.max() > settings.derate_start_c:
            return None
        history.append(thermal.temperature_c.copy())
    np.savez_compressed(path, torque_nm=profile.torques, body_xyz_m=profile.body_xyz_m,
                        foot_contacts=profile.foot_contacts, temperature_c=np.asarray(history))
    return walk_summary(profile) | {
        "peak_c": float(thermal.peak_by_joint_c.max()),
        "trace": f"traces/{path.name}",
        "execution": "nominal_physics_reused",
    }


def summarize(rows, executions, map_ids, thermal_ids, draws, seed):
    per_map = {name: {} for name in map_ids}
    by_thermal = []
    totals = {}
    for method in METHODS:
        values = [row for row in rows if row["method"] == method]
        totals[method] = {
            "scheduled": len(values),
            "completed": sum(row["completed"] for row in values),
            "no_route": sum(row["selected_route"] is None for row in values),
            "selected_route_failed": sum(row["selected_route"] is not None and not row["completed"] for row in values),
        }
        for name in map_ids:
            subset = [row for row in values if row["map"] == name]
            per_map[name][method] = sum(row["completed"] for row in subset) / len(subset)
    indices = np.random.default_rng(seed).integers(0, len(map_ids), size=(draws, len(map_ids)))
    comparisons = {}
    per_joint_rows = [row for row in rows if row["method"] == "per_joint"]
    for baseline in METHODS[1:]:
        base_rows = [row for row in rows if row["method"] == baseline]
        delta = np.array([per_map[name]["per_joint"] - per_map[name][baseline] for name in map_ids])
        comparisons[baseline] = {
            "completion_difference_pp": float(100 * delta.mean()),
            "descriptive_map_bootstrap_95_pp": (100 * np.quantile(delta[indices].mean(axis=1), [0.025, 0.975])).tolist(),
            "per_joint_only": sum(left["completed"] and not right["completed"]
                                  for left, right in zip(per_joint_rows, base_rows, strict=True)),
            "baseline_only": sum(right["completed"] and not left["completed"]
                                 for left, right in zip(per_joint_rows, base_rows, strict=True)),
        }
    for heat, tau in thermal_ids:
        subset = [row for row in rows if (row["heating_rate_multiplier"], row["cooling_time_constant_s"]) == (heat, tau)]
        count = sum(row["method"] == "per_joint" for row in subset)
        paired_routes = [[row["selected_route"] for row in subset if row["map"] == name and row["method"] == "per_joint"]
                         for name in map_ids]
        reversals = sum(len(routes) == 2 and None not in routes and len(set(routes)) == 2 for routes in paired_routes)
        by_thermal.append({
            "heating_rate_multiplier": heat, "cooling_time_constant_s": tau, "starts": count,
            "per_joint_reversals": reversals,
            "completed": {method: sum(row["completed"] for row in subset if row["method"] == method)
                          for method in METHODS},
        })
    return {
        "maps": len(map_ids), "per_method": totals, "completion_rate_by_map": per_map,
        "paired_comparisons": comparisons, "by_thermal_setting": by_thermal,
        "warm_route_executions": len(executions),
        "nominal_physics_reused": sum(row["execution"] == "nominal_physics_reused" for row in executions),
    }


def run(config_path, output, workers):
    manifest, maps, walking, settings, starts = load_design(config_path)
    spec = manifest["study"]
    if workers < 1 or spec["bootstrap_draws"] < 1:
        raise ValueError("Expected positive worker and bootstrap counts")
    output.mkdir(parents=True, exist_ok=False)
    trace_dir = output / "traces"
    trace_dir.mkdir()
    write_json(output / "manifest.json", manifest)
    print(f"Frozen manifest: {output / 'manifest.json'}", flush=True)

    profiles, executions, jobs = {}, {}, {}
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for name, options in maps.items():
            (output / f"{name}.xml").write_text(build_xml(ConnectedTerrain(**options)) + "\n")
            for route, side in ROUTES.items():
                path = trace_dir / f"{name}_nominal_{route}.npz"
                jobs[executor.submit(walk_job, options, side, walking, path)] = (name, route)
        for job in as_completed(jobs):
            name, route = jobs[job]
            walk = job.result()
            profiles[name, route] = walk
            print(f"Nominal {name}/{route}: {walk.failure or 'completed'} ({walk.elapsed_s:.1f} s)", flush=True)

        jobs.clear()
        for name, (heat, tau), start, route in product(maps, settings, starts, ROUTES):
            key = name, heat, tau, start, route
            path = trace_dir / f"{name}_heat{heat:g}_tau{tau:g}_{start}_{route}.npz"
            reuse = nominal_execution(profiles[name, route], settings[heat, tau], starts[start], path)
            if reuse is None:
                job = executor.submit(walk_job, maps[name], ROUTES[route], walking, path,
                                      settings[heat, tau], starts[start])
                jobs[job] = key
            else:
                executions[key] = reuse
        print(f"Warm routes: {len(jobs)} physics replays, {len(executions)} nominal trajectories reused", flush=True)
        for index, job in enumerate(as_completed(jobs), 1):
            executions[jobs[job]] = job.result()
            if index % 12 == 0 or index == len(jobs):
                print(f"Physics replays: {index}/{len(jobs)}", flush=True)

    rows = []
    for name, (heat, tau), start in product(maps, settings, starts):
        nominal = {route: profiles[name, route] for route in ROUTES}
        for method in METHODS:
            route, predictions = rank_routes(method, settings[heat, tau], starts[start], nominal, SAMPLE_SECONDS)
            selected = executions[name, heat, tau, start, route] if route else None
            rows.append({
                "map": name, "heating_rate_multiplier": heat, "cooling_time_constant_s": tau, "start": start,
                "method": method, "selected_route": route, "completed": selected["completed"] if selected else False,
                "failure": selected["failure"] if selected else "no_route",
                "elapsed_s": selected["elapsed_s"] if selected else None,
                "peak_c": selected["peak_c"] if selected else None,
                **{f"{name}_predicted_peak_c": value["peak_c"] for name, value in predictions.items()},
                **{f"{name}_predicted_feasible": value["feasible"] for name, value in predictions.items()},
            })
    execution_rows = [
        {"map": name, "heating_rate_multiplier": heat, "cooling_time_constant_s": tau, "start": start,
         "route": route, **executions[name, heat, tau, start, route]}
        for name, (heat, tau), start, route in product(maps, settings, starts, ROUTES)
    ]
    report = summarize(rows, execution_rows, list(maps), list(settings), spec["bootstrap_draws"], spec["bootstrap_seed"])
    report["nominal_routes"] = {
        name: {route: walk_summary(profiles[name, route]) for route in ROUTES} for name in maps
    }
    with (output / "decisions.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_json(output / "executions.json", execution_rows)
    write_json(output / "summary.json", report)
    print(json.dumps(report["per_method"], indent=2), flush=True)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/asymmetric_benchmark.json"))
    parser.add_argument("--output", type=Path, default=Path("results/asymmetric_benchmark"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.output, args.workers)


if __name__ == "__main__":
    main()
