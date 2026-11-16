"""Execute both branches from a common start to a common goal in MuJoCo."""

import argparse
import json
from math import isfinite
from pathlib import Path
import platform

import mujoco
import numpy as np

from .connected_terrain import Branch, ConnectedTerrain
from .connected_walk import walk_branch
from .model import JOINT_NAMES, build_xml
from .pilot import add_trace, evaluate_routes, mirrored_starts, save_report, walk_summary
from .thermal import ThermalSettings
from .walking import SAMPLE_SECONDS


def run(config_path, output, *, heating_multiplier=1.0):
    if not isfinite(heating_multiplier) or heating_multiplier <= 0:
        raise ValueError("Heating multiplier must be finite and positive")
    config = json.loads(config_path.read_text())
    config["thermal"]["rise_at_reference_c"] *= heating_multiplier
    terrain = ConnectedTerrain(**config["terrain"])
    settings = ThermalSettings(**config["thermal"])
    scenarios = mirrored_starts(config, settings)
    branches = {"rises_left": Branch(terrain, 1), "rises_right": Branch(terrain, -1)}
    speed, deadline = config["command_speed_m_s"], config["deadline_s"]
    drift, radius = config["max_corridor_drift_m"], config["goal_radius_m"]
    if not 0 < speed <= 0.3 or not 0 < radius < 1 or not 0 < drift < terrain.branch_offset_m or deadline <= 2:
        raise ValueError("Invalid speed, deadline, corridor tolerance, or goal radius")

    def replay(route, thermal=None, history=None):
        print(f"Simulating {route} ({'nominal' if thermal is None else 'thermal'})", flush=True)
        return walk_branch(branches[route], speed, deadline, drift, radius, thermal, history)

    profiles = {name: replay(name) for name in branches}
    traces = {"terrain_x_m": terrain.x_grid, "terrain_y_m": terrain.y_grid, "terrain_height_m": terrain.heights}
    for name, profile in profiles.items():
        branch = branches[name]
        traces[f"{name}_centerline_xy_m"] = np.column_stack((branch.x, branch.y))
        add_trace(traces, f"profile_{name}", profile)
    report = {
        "config": config,
        "heating_multiplier": heating_multiplier,
        "runtime": {"python": platform.python_version(), "mujoco": mujoco.__version__, "numpy": np.__version__},
        "joint_order": JOINT_NAMES,
        "sample_interval_s": SAMPLE_SECONDS,
        "start_xy_m": [0.0, 0.0],
        "goal_xy_m": [terrain.goal_x, 0.0],
        "nominal_routes": {name: walk_summary(profile) for name, profile in profiles.items()},
        "starting_states": {},
    }
    evaluate_routes(report, traces, settings, scenarios, profiles, replay)
    output.mkdir(parents=True, exist_ok=True)
    (output / "scene.xml").write_text(build_xml(terrain) + "\n")
    save_report(report, traces, output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/connected_pilot.json"))
    parser.add_argument("--output", type=Path, default=Path("results/connected_pilot"))
    parser.add_argument("--heating-multiplier", type=float, default=1.0,
                        help="Scale the assumed rise at reference torque for a development sensitivity run")
    args = parser.parse_args()
    report = run(args.config, args.output, heating_multiplier=args.heating_multiplier)
    for name, outcome in report["nominal_routes"].items():
        print(f"{name}: {'reached goal' if outcome['completed'] else outcome['failure']} "
              f"after {outcome['elapsed_s']:.1f} s")
    print(json.dumps(report["pilot_checks"], indent=2))
    print(f"Results: {args.output / 'summary.json'}")


if __name__ == "__main__":
    main()
