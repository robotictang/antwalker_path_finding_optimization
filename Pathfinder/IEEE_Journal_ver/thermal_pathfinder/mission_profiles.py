"""Freeze the mission-completion benchmark and generate its nominal edge profiles."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from itertools import product
import json
from pathlib import Path
import platform

import mujoco
import numpy as np

from .fan_network import FanNetwork
from .margin_profiles import digest
from .model import build_xml
from .network_study import walk_job, write_json
from .pilot import mirrored_starts, walk_summary
from .route_speed_profiles import trace_name
from .thermal import ThermalSettings
from .walking import SAMPLE_SECONDS


def design(config):
    spec = json.loads(config.read_text())
    base_path = config.with_name(spec["base_config"])
    base = json.loads(base_path.read_text())
    baseline = ThermalSettings(**base["thermal"])
    settings, starts = {}, {}
    for setting in spec["thermal_settings"]:
        tau = setting["cooling_time_constant_s"]
        key = setting["id"]
        settings[key] = replace(
            baseline, time_constant_s=tau, rise_at_reference_c=baseline.rise_at_reference_c
            * setting["heating_multiplier"] * tau / baseline.time_constant_s,
        )
        starts[key] = mirrored_starts(
            {"starting_temperatures_c": {"warm": setting["warm_c"], "cool": setting["cool_c"]}}, baseline
        )
    networks = {item["id"]: FanNetwork(item["stages"], spec["resolution_m"]) for item in spec["maps"]}
    walking = {"speed": base["command_speed_m_s"], "max_lateral": base["max_corridor_drift_m"],
               "goal_radius": base["goal_radius_m"]}
    sources = ("fan_network", "mission_profiles", "mission_completion", "mission_analysis", "network",
               "network_study", "network_planning", "connected_terrain", "connected_walk", "walking",
               "model", "pilot", "route_speed_study", "route_speed_profiles", "speed_policy", "thermal")
    manifest = {
        "study": spec, "base": base, "sample_interval_s": SAMPLE_SECONDS,
        "runtime": {"python": platform.python_version(), "mujoco": mujoco.__version__, "numpy": np.__version__},
        "thermal": {key: asdict(value) for key, value in settings.items()},
        "sha256": {path.name: digest(path) for path in (
            config, base_path, *(Path(__file__).with_name(f"{source}.py") for source in sources)
        )},
    }
    return manifest, networks, settings, starts, walking


def run(config, output, workers):
    manifest, networks, _, _, walking = design(config)
    spec = manifest["study"]
    folder = output / "profiles"
    folder.mkdir(parents=True, exist_ok=False)
    write_json(output / "manifest.json", manifest)
    print(f"Frozen manifest: {output / 'manifest.json'}", flush=True)
    records = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        for name, network in networks.items():
            scene = network.route(tuple(edges[0] for edges in network.edges.values()))
            (output / f"{name}.xml").write_text(build_xml(scene) + "\n")
            for edges in network.edges.values():
                for edge, fraction in product(edges, spec["speed_fractions"]):
                    filename = trace_name(name, edge, fraction)
                    job = pool.submit(walk_job, network, (edge,), walking | {"speed": walking["speed"] * fraction},
                                      spec["edge_deadline_s"], folder / filename)
                    pending[job] = filename
        for index, job in enumerate(as_completed(pending), 1):
            filename = pending[job]
            records[filename] = walk_summary(job.result())
            print(f"{index}/{len(pending)} {filename}: {records[filename]['failure'] or 'completed'}", flush=True)
    write_json(output / "edge_profiles.json", dict(sorted(records.items())))


def arguments(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", type=Path, default=Path("experiments/mission_completion.json"))
    parser.add_argument("--output", type=Path, default=Path("results/mission_completion"))
    return parser


def main():
    parser = arguments(__doc__)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.output, args.workers)


if __name__ == "__main__":
    main()
