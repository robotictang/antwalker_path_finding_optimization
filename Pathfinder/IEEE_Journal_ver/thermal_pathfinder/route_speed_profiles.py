"""Profile constant speed actions on the existing route networks."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from math import isfinite
from pathlib import Path

from .network import RouteNetwork
from .network_study import load_design, walk_job, write_json
from .pilot import walk_summary


def load_profiles_design(config):
    spec = json.loads(config.read_text())
    network_config = config.with_name(spec["network_config"])
    network_manifest, maps, thermal, starts, walking = load_design(network_config)
    fractions = spec["speed_fractions"]
    if (not fractions or fractions[0] != 1 or len(fractions) != len(set(fractions))
            or not all(0 < fraction <= 1 for fraction in fractions)
            or not all(isfinite(spec[key]) and spec[key] > 0 for key in ("transition_s", "edge_deadline_s"))):
        raise ValueError("Invalid speed study configuration")
    networks = {name: RouteNetwork(stages, network_manifest["study"]["resolution_m"])
                for name, stages in maps.items()}
    return spec, network_manifest, networks, thermal, starts, walking


def trace_name(name, edge, fraction):
    return f"{name}_{edge.name}_speed{fraction:g}.npz"


def validate_reference(reference, manifest):
    saved = json.loads((reference / "manifest.json").read_text())
    expected = json.loads(json.dumps(manifest))
    # The spatial policy is optional. Audit its single source change against the frozen original.
    old_walk = reference / "frozen_source/thermal_pathfinder/connected_walk.py"
    expected["sha256"]["connected_walk.py"] = hashlib.sha256(old_walk.read_bytes()).hexdigest()
    if saved != expected:
        raise ValueError("Reference network run does not match the configured networks and baseline source")


def run(config, reference, output, workers):
    spec, manifest, networks, _, _, walking = load_profiles_design(config)
    validate_reference(reference, manifest)
    output.mkdir(parents=True, exist_ok=False)
    traces = output / "profiles"
    traces.mkdir()
    baseline = json.loads((reference / "edge_profiles.json").read_text())
    records = {}
    lock = {
        "study": spec, "network_manifest": manifest,
        "reference_manifest_sha256": hashlib.sha256((reference / "manifest.json").read_bytes()).hexdigest(),
        "profiler_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    write_json(output / "profile_manifest.json", lock)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {}
        for name, network in networks.items():
            for stage in network.edges.values():
                for edge in stage:
                    for fraction in spec["speed_fractions"]:
                        filename = trace_name(name, edge, fraction)
                        if fraction == 1:
                            path = reference / "traces" / f"{name}_profile_{edge.name}.npz"
                            (traces / filename).hardlink_to(path)
                            records[filename] = baseline[name][edge.name]
                        else:
                            settings = walking | {"speed": walking["speed"] * fraction}
                            future = pool.submit(walk_job, network, (edge,), settings, spec["edge_deadline_s"],
                                                 traces / filename)
                            jobs[future] = filename
        for job in as_completed(jobs):
            filename = jobs[job]
            record = walk_summary(job.result())
            records[filename] = record
            print(f"{filename}: {record['failure'] or 'completed'} ({record['elapsed_s']:.1f} s)", flush=True)
    write_json(output / "edge_profiles.json", dict(sorted(records.items())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/route_speed_study.json"))
    parser.add_argument("--reference", type=Path, default=Path("results/network_study"))
    parser.add_argument("--output", type=Path, default=Path("results/route_speed_study"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.reference, args.output, args.workers)


if __name__ == "__main__":
    main()
