"""Freeze calibration and generate branch profiles on new test courses."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
import hashlib
from itertools import product
import json
from math import isfinite
from pathlib import Path
import platform

import mujoco
import numpy as np

from .model import build_xml
from .network import RouteNetwork
from .network_study import identifier, walk_job, write_json
from .pilot import mirrored_starts, walk_summary
from .route_speed_profiles import trace_name
from .thermal import ThermalSettings
from .walking import SAMPLE_SECONDS

METHODS = ("per_motor_fixed_speed", "fastest_route_planned_speeds", "per_motor_route_and_speed")
SOURCES = ("margin_profiles", "margin_study", "margin_analysis", "route_speed_study", "route_speed_profiles",
           "network_study", "network", "network_planning", "thermal", "walking", "connected_walk",
           "connected_terrain", "model", "pilot", "speed_policy")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calibration(development, reference, margins):
    manifest = json.loads((development / "manifest.json").read_text())
    if manifest["reference_decisions_sha256"] != digest(reference / "decisions.json"):
        raise ValueError("Development run and reference decisions do not match")
    decisions = json.loads((development / "decisions.json").read_text())
    runs = {
        "reference": json.loads((reference / "executions.json").read_text()),
        "continuous_replay": json.loads((development / "executions.json").read_text()),
    }
    predictions = {}
    for row in decisions:
        if row["method"] not in METHODS or row["execution"] is None:
            continue
        key = row["execution_source"], row["execution"]
        prediction = row["predicted_peak_c"]
        predictions[key] = min(predictions.get(key, prediction), prediction)
    records = []
    for (source, key), prediction in sorted(predictions.items()):
        result = runs[source][key]
        records.append({
            "source": source, "execution": key, "predicted_peak_c": prediction,
            "observed_peak_c": result["peak_c"], "failure": result["failure"],
            "observed_minus_predicted_c": result["peak_c"] - prediction,
        })
    worst = max(row["observed_minus_predicted_c"] for row in records)
    chosen = next((margin for margin in margins if margin >= worst), None)
    if chosen is None:
        raise ValueError("Development error exceeds the full margin grid")
    return {
        "records": records, "maximum_observed_underprediction_c": worst, "selected_margin_c": chosen,
        "input_sha256": {
            "development_decisions": digest(development / "decisions.json"),
            "development_executions": digest(development / "executions.json"),
            "reference_executions": digest(reference / "executions.json"),
        },
    }


def load_design(config):
    spec = json.loads(config.read_text())
    base_path = config.with_name(spec["base_config"])
    base = json.loads(base_path.read_text())
    baseline = ThermalSettings(**base["thermal"])
    fractions, margins = spec["speed_fractions"], spec["margin_grid_c"]
    if (not fractions or fractions[0] != 1 or len(fractions) != len(set(fractions))
            or not all(0 < fraction <= 1 for fraction in fractions)
            or not margins or margins[0] != 0 or margins != sorted(set(margins))
            or not all(isfinite(margin) for margin in margins)
            or not all(isfinite(spec[key]) and spec[key] > 0 for key in ("deadline_s", "edge_deadline_s", "transition_s"))):
        raise ValueError("Invalid speed, margin, or duration in study design")
    networks = {identifier(item["id"]): RouteNetwork([base["terrain"] | stage for stage in item["stages"]],
                                                      spec["resolution_m"]) for item in spec["maps"]}
    settings = {}
    for item in spec["thermal_settings"]:
        tau = item["cooling_time_constant_s"]
        settings[identifier(item["id"])] = replace(
            baseline, time_constant_s=tau,
            rise_at_reference_c=baseline.rise_at_reference_c * item["heating_multiplier"]
            * tau / baseline.time_constant_s,
        )
    if (not networks or len(networks) != len(spec["maps"]) or not settings
            or len(settings) != len(spec["thermal_settings"])):
        raise ValueError("Missing or duplicate test maps or thermal settings")
    walking = {"speed": base["command_speed_m_s"], "max_lateral": base["max_corridor_drift_m"],
               "goal_radius": base["goal_radius_m"]}
    lock = {
        "study": spec, "base": base, "methods": METHODS, "sample_interval_s": SAMPLE_SECONDS,
        "runtime": {"python": platform.python_version(), "mujoco": mujoco.__version__, "numpy": np.__version__},
        "settings": {key: asdict(value) for key, value in settings.items()},
        "source_sha256": {path.name: digest(path) for path in (
            config, base_path, *(Path(__file__).with_name(f"{source}.py") for source in SOURCES)
        )},
    }
    return lock, networks, settings, mirrored_starts(base, baseline), walking


def run(config, development, reference, output, workers):
    lock, networks, _, _, walking = load_design(config)
    spec = lock["study"]
    lock["calibration"] = calibration(development, reference, spec["margin_grid_c"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "profiles").mkdir()
    write_json(output / "manifest.json", lock)
    print(f"Frozen development-selected margin: {lock['calibration']['selected_margin_c']:.2f} C", flush=True)
    records = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {}
        for name, network in networks.items():
            scene = network.route(tuple(edges[0] for edges in network.edges.values()))
            (output / f"{name}.xml").write_text(build_xml(scene) + "\n")
            for edges in network.edges.values():
                for edge, fraction in product(edges, spec["speed_fractions"]):
                    filename = trace_name(name, edge, fraction)
                    job = pool.submit(walk_job, network, (edge,), walking | {"speed": walking["speed"] * fraction},
                                      spec["edge_deadline_s"], output / "profiles" / filename)
                    jobs[job] = filename
        for index, job in enumerate(as_completed(jobs), 1):
            filename = jobs[job]
            records[filename] = walk_summary(job.result())
            if index % 12 == 0 or records[filename]["failure"]:
                print(f"Edge profiles {index}/{len(jobs)} {filename}: {records[filename]['failure'] or 'completed'}",
                      flush=True)
    write_json(output / "edge_profiles.json", dict(sorted(records.items())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/thermal_margin_study.json"))
    parser.add_argument("--development", type=Path, default=Path("results/route_speed_study"))
    parser.add_argument("--reference", type=Path, default=Path("results/network_study"))
    parser.add_argument("--output", type=Path, default=Path("results/thermal_margin_study"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.development, args.reference, args.output, args.workers)


if __name__ == "__main__":
    main()
