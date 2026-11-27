"""Evaluate per-motor graph routing against reactive slowdown in MuJoCo."""

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
import hashlib
import json
from math import isfinite
from pathlib import Path
import platform
import re

import mujoco
import numpy as np

from .connected_walk import walk_branch
from .model import JOINT_NAMES, build_xml
from .network import RouteNetwork
from .network_planning import EdgeThermalModel, fastest_route, thermal_route
from .pilot import mirrored_starts, walk_summary
from .speed_policy import ThermalSlowdown
from .thermal import ThermalSettings, ThermalState
from .walking import SAMPLE_SECONDS

METHODS = {
    "fastest_fixed_speed": (False, False),
    "fastest_reactive_slowdown": (False, True),
    "per_motor_fixed_speed": (True, False),
    "per_motor_with_slowdown": (True, True),
}
SOURCES = ("network_study", "network", "network_planning", "speed_policy", "connected_walk",
           "connected_terrain", "walking", "model", "thermal", "pilot")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def identifier(name):
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise ValueError(f"Invalid ID: {name}")
    return name


def load_design(config):
    spec = json.loads(config.read_text())
    base_path = config.with_name(spec["base_config"])
    base = json.loads(base_path.read_text())
    networks = {identifier(item["id"]): [base["terrain"] | stage for stage in item["stages"]]
                for item in spec["maps"]}
    baseline = ThermalSettings(**base["thermal"])
    settings = {}
    for item in spec["thermal_settings"]:
        key = identifier(item["id"])
        tau = item["cooling_time_constant_s"]
        settings[key] = replace(
            baseline, time_constant_s=tau,
            rise_at_reference_c=baseline.rise_at_reference_c * item["heating_multiplier"]
            * tau / baseline.time_constant_s,
        )
    if (len(networks) != len(spec["maps"]) or not networks
            or len(settings) != len(spec["thermal_settings"]) or not settings):
        raise ValueError("Expected unique network and thermal IDs")
    if any(not isfinite(spec[key]) or spec[key] <= 2 for key in ("deadline_s", "edge_deadline_s")):
        raise ValueError("Invalid deadlines")
    policy = ThermalSlowdown(**spec["slowdown"])
    if not baseline.ambient_c < policy.resume_c < policy.trigger_c < baseline.limit_c:
        raise ValueError("Slowdown thresholds must be inside the thermal range")
    starts = mirrored_starts(base, baseline)
    walking = {
        "speed": base["command_speed_m_s"],
        "max_lateral": base["max_corridor_drift_m"],
        "goal_radius": base["goal_radius_m"],
    }
    files = (config, base_path, *(Path(__file__).with_name(f"{name}.py") for name in SOURCES))
    manifest = {
        "study": spec, "base": base, "methods": METHODS, "joint_order": JOINT_NAMES,
        "thermal_settings": {key: asdict(value) for key, value in settings.items()},
        "sample_interval_s": SAMPLE_SECONDS,
        "runtime": {"python": platform.python_version(), "mujoco": mujoco.__version__, "numpy": np.__version__},
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    return manifest, networks, settings, starts, walking


def walk_job(network, edges, walking, deadline, path, settings=None, initial=None, slowdown=None):
    route = network.route(edges, local_start=settings is None)
    thermal = ThermalState(settings, initial) if settings is not None else None
    history = [] if thermal is None else [thermal.temperature_c.copy()]
    policy = ThermalSlowdown(**slowdown) if slowdown is not None else None
    walk = walk_branch(route, **walking, deadline=deadline, thermal=thermal, temperature_history=history,
                       speed_policy=policy)
    np.savez_compressed(path, body_xyz_m=walk.body_xyz_m, torque_nm=walk.torques,
                        foot_contacts=walk.foot_contacts, temperature_c=np.asarray(history),
                        centerline_xy_m=np.column_stack((route.x, route.y)))
    if thermal is None:
        return walk
    return walk_summary(walk) | {
        "trace": f"traces/{path.name}", "peak_c": float(thermal.peak_by_joint_c.max()),
        "slow_seconds": policy.slow_seconds if policy else 0.0, "slowdown_events": policy.events if policy else [],
    }


def run(config, output, workers):
    manifest, maps, settings, starts, walking = load_design(config)
    spec = manifest["study"]
    networks = {key: RouteNetwork(stages, spec["resolution_m"]) for key, stages in maps.items()}
    output.mkdir(parents=True, exist_ok=False)
    trace_dir = output / "traces"
    trace_dir.mkdir()
    write_json(output / "manifest.json", manifest)
    print(f"Frozen manifest: {output / 'manifest.json'}", flush=True)
    all_walks, plans, executions = {}, [], {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {}
        for name, network in networks.items():
            all_walks[name] = {}
            scene_route = network.route(tuple(edges[0] for edges in network.edges.values()))
            (output / f"{name}.xml").write_text(build_xml(scene_route) + "\n")
            for edges in network.edges.values():
                for edge in edges:
                    path = trace_dir / f"{name}_profile_{edge.name}.npz"
                    job = pool.submit(walk_job, network, (edge,), walking, spec["edge_deadline_s"], path)
                    jobs[job] = name, edge
        for job in as_completed(jobs):
            name, edge = jobs[job]
            walk = job.result()
            all_walks[name][edge] = walk
            print(f"Edge {name}/{edge.name}: {walk.failure or 'completed'} ({walk.elapsed_s:.1f} s)", flush=True)
        write_json(output / "edge_profiles.json", {
            name: {edge.name: walk_summary(walk) for edge, walk in sorted(walks.items(), key=lambda item: item[0].name)}
            for name, walks in all_walks.items()
        })

        missions = {}
        for name, network in networks.items():
            walks = all_walks[name]
            fixed = fastest_route(network, walks, spec["deadline_s"])
            for thermal_id, thermal in settings.items():
                profiles = {edge: EdgeThermalModel.from_walk(walk, thermal)
                            for edge, walk in walks.items() if walk.completed}
                for start, initial in starts.items():
                    label = thermal_route(network, profiles, initial, thermal.limit_c, spec["deadline_s"])
                    for method, (aware, slow) in METHODS.items():
                        edges = (label.edges if label else None) if aware else fixed
                        route_id = "_".join(edge.name for edge in edges) if edges else None
                        key = f"{name}_{thermal_id}_{start}_{route_id}_{'slow' if slow else 'fixed'}" if edges else None
                        plans.append({
                            "map": name, "setting": thermal_id, "start": start, "method": method,
                            "route": route_id, "execution": key,
                            "predicted_peak_c": label.peak_c if aware and label else None,
                            "predicted_junction_temperatures_c": (
                                [value.tolist() for value in label.junction_temperatures_c] if aware and label else None
                            ),
                        })
                        if key and key not in missions:
                            path = trace_dir / f"{key}.npz"
                            missions[key] = pool.submit(walk_job, network, edges, walking, spec["deadline_s"],
                                                        path, thermal, initial, spec["slowdown"] if slow else None)
        write_json(output / "plans.json", plans)
        print(f"Scheduled {len(plans)} decisions and {len(missions)} distinct continuous mission runs", flush=True)
        for job in as_completed({future: key for key, future in missions.items()}):
            key = next(name for name, future in missions.items() if future is job)
            executions[key] = job.result()
            result = executions[key]
            print(f"Mission {len(executions)}/{len(missions)} {key}: {result['failure'] or 'completed'}", flush=True)

    rows = [{**plan, "completed": executions[plan["execution"]]["completed"] if plan["execution"] else False,
             "failure": executions[plan["execution"]]["failure"] if plan["execution"] else "no_route"}
            for plan in plans]
    by_method = {}
    for method in METHODS:
        subset = [row for row in rows if row["method"] == method]
        counts = Counter(row["failure"] or "completed" for row in subset)
        by_method[method] = {"scheduled": len(subset), "outcomes": dict(counts)}
    write_json(output / "executions.json", dict(sorted(executions.items())))
    write_json(output / "decisions.json", rows)
    write_json(output / "summary.json", {"by_method": by_method, "unique_missions": len(executions)})
    print(json.dumps(by_method, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/network_study.json"))
    parser.add_argument("--output", type=Path, default=Path("results/network_study"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.output, args.workers)


if __name__ == "__main__":
    main()
