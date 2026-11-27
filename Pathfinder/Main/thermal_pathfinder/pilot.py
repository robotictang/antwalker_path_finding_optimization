"""Headless command for the mirrored cross-slope development experiment."""

import argparse
from dataclasses import fields
import json
from math import radians, tan
from pathlib import Path
import platform
import re

import mujoco
import numpy as np

from .model import JOINT_NAMES, Terrain, build_xml
from .planning import rank_routes
from .thermal import ThermalSettings, ThermalState
from .walking import SAMPLE_SECONDS, Walk, simulate

METHODS = ("per_joint", "maximum_only", "mean_only", "time_only")


def walk_summary(walk: Walk):
    summary = {field.name: getattr(walk, field.name) for field in fields(walk)
               if not isinstance(getattr(walk, field.name), np.ndarray)}
    if walk.torques.size:
        rms = np.sqrt(np.mean(walk.torques**2, axis=0))
        summary["rms_torque_by_joint_nm"] = dict(zip(JOINT_NAMES, rms.tolist(), strict=True))
    return summary


def add_trace(traces, prefix, walk):
    traces[f"{prefix}_torque_nm"] = walk.torques
    traces[f"{prefix}_body_xyz_m"] = walk.body_xyz_m
    traces[f"{prefix}_foot_contacts"] = walk.foot_contacts


def mirrored_starts(config, settings):
    warm = float(config["starting_temperatures_c"]["warm"])
    cool = float(config["starting_temperatures_c"]["cool"])
    if not settings.ambient_c <= cool < warm < settings.limit_c:
        raise ValueError("Expected ambient <= cool < warm < thermal limit")
    return {
        "left_warm": np.repeat([warm, cool], len(JOINT_NAMES) // 2),
        "right_warm": np.repeat([cool, warm], len(JOINT_NAMES) // 2),
    }


def run(config_path, output):
    config = json.loads(config_path.read_text())
    settings = ThermalSettings(**config["thermal"])
    route_specs = config["routes"]
    if len(route_specs) != 2 or any(
        not re.fullmatch(r"[a-z][a-z0-9_]*", route["name"]) or route["name"] == "flat" or
        not 0 < abs(route["slope_deg"]) < 45 for route in route_specs
    ):
        raise ValueError("Expected two named routes with slope magnitudes between 0 and 45 degrees")
    routes = {route["name"]: tan(radians(route["slope_deg"])) for route in route_specs}
    if len(routes) != 2 or not np.isclose(sum(routes.values()), 0) or any(slope == 0 for slope in routes.values()):
        raise ValueError("This pilot requires two nonzero mirrored cross-slopes")
    scenarios = mirrored_starts(config, settings)
    walk_settings = {
        "distance": config["distance_m"],
        "speed": config["command_speed_m_s"],
        "deadline": config["deadline_s"],
        "max_lateral": config["max_corridor_drift_m"],
    }
    profiles = {name: simulate(slope, **walk_settings) for name, slope in routes.items()}
    output.mkdir(parents=True, exist_ok=True)
    flat = simulate(0, **walk_settings)
    traces = {}
    add_trace(traces, "flat", flat)
    for name, walk in profiles.items():
        add_trace(traces, f"profile_{name}", walk)
    report = {
        "config": config,
        "runtime": {"python": platform.python_version(), "mujoco": mujoco.__version__, "numpy": np.__version__},
        "joint_order": JOINT_NAMES,
        "sample_interval_s": SAMPLE_SECONDS,
        "flat_walk": walk_summary(flat),
        "nominal_routes": {name: walk_summary(profile) for name, profile in profiles.items()},
        "starting_states": {},
    }
    for name, slope in {"flat": 0.0, **routes}.items():
        (output / f"{name}.xml").write_text(build_xml(Terrain(slope)) + "\n")
    evaluate_routes(
        report, traces, settings, scenarios, profiles,
        lambda route, thermal, history: simulate(routes[route], **walk_settings,
                                                 thermal=thermal, temperature_history=history),
    )
    report["pilot_checks"]["all_nominal_walks_completed"] &= flat.completed
    save_report(report, traces, output)
    return report


def evaluate_routes(report, traces, settings, scenarios, profiles, replay):
    for name, initial in scenarios.items():
        methods, execution = {}, {}
        for route in profiles:
            thermal = ThermalState(settings, initial)
            history = [thermal.temperature_c.copy()]
            walk = replay(route, thermal, history)
            add_trace(traces, f"{name}_{route}", walk)
            traces[f"{name}_{route}_temperature_c"] = np.asarray(history)
            execution[route] = {
                **walk_summary(walk),
                "peak_c": float(thermal.peak_by_joint_c.max()),
                "peak_by_joint_c": dict(zip(JOINT_NAMES, thermal.peak_by_joint_c.tolist(), strict=True)),
            }
        for method in METHODS:
            route, predictions = rank_routes(method, settings, initial, profiles, SAMPLE_SECONDS)
            methods[method] = {
                "selected_route": route, "predictions": predictions,
                "completed": route is not None and execution[route]["completed"],
            }
        report["starting_states"][name] = {
            "temperature_c": initial.tolist(), "mean_c": float(initial.mean()), "maximum_c": float(initial.max()),
            "methods": methods, "execution": execution,
        }
    per_joint = [state["methods"]["per_joint"] for state in report["starting_states"].values()]
    report["pilot_checks"] = {
        "all_nominal_walks_completed": all(walk.completed for walk in profiles.values()),
        "per_joint_route_reversal": all(decision["selected_route"] for decision in per_joint)
        and len({decision["selected_route"] for decision in per_joint}) == 2,
        "completion_counts_by_method": {
            method: sum(state["methods"][method]["completed"] for state in report["starting_states"].values())
            for method in METHODS
        },
    }


def save_report(report, traces, output):
    np.savez_compressed(output / "traces.npz", **traces)
    (output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/pilot.json"))
    parser.add_argument("--output", type=Path, default=Path("results/pilot"))
    args = parser.parse_args()
    report = run(args.config, args.output)
    flat = report["flat_walk"]
    print(f"Flat walking: {'completed' if flat['completed'] else flat['failure']} ({flat['forward_m']:.2f} m)")
    for name, result in report["starting_states"].items():
        print(f"{name} (mean {result['mean_c']:.1f} C, max {result['maximum_c']:.1f} C)")
        for method, decision in result["methods"].items():
            route = decision["selected_route"]
            status = "completed" if decision["completed"] else result["execution"][route]["failure"] if route else "no feasible route"
            print(f"  {method}: {route or 'none'} ({status})")
    print(f"Results: {args.output / 'summary.json'}")


if __name__ == "__main__":
    main()
