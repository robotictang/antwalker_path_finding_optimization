"""Exhaustively replay matched hot-side assignments under the same speed governor."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from fcntl import LOCK_EX, LOCK_NB, flock
from itertools import product
import json
from pathlib import Path
from statistics import mean

import numpy as np

from .hot_motor_swap_analysis import summarize
from .hot_motor_swap_audit import audit_trace
from .margin_profiles import digest
from .mission_profiles import arguments, design
from .network_study import write_json
from .pilot import mirrored_starts
from .published_speed_baseline import controller, forecast, replay
from .reactive_forecast import ProgressForecast
from .reactive_study import load_inputs

CONFIG = Path("experiments/hot_motor_swap.json")
OUTPUT = Path("results/hot_motor_swap")
PROTOCOL = Path("docs/hot_motor_swap_protocol.md")
SIDES = ("left_warm", "right_warm")


def freeze_json(path, data):
    """Preserve an existing lock, or create it before the first replay."""
    if path.exists():
        if json.loads(path.read_text()) != data:
            raise ValueError(f"Frozen input differs from {path}")
    else:
        save_json(path, data)


def save_json(path, data):
    staged = path.with_suffix(".tmp")
    write_json(staged, data)
    staged.replace(path)


def choose(candidates, deadline, ceiling):
    eligible = (choice for choice in candidates if choice["predicted_peak_c"] < ceiling
                and choice["predicted_elapsed_s"] <= deadline)
    return min(eligible, key=lambda row: (row["predicted_elapsed_s"], row["predicted_peak_c"], row["route"]),
               default=None)


def plan_cases(spec, networks, thermal, starts, walking, profiles):
    cases, jobs = [], {}
    for course in spec["maps"]:
        name, deadline = course["id"], course["deadline_s"]
        network = networks[name]
        for setting, settings in thermal.items():
            predictor = ProgressForecast(network, profiles[name], settings, spec, walking["goal_radius"])
            ceiling = settings.limit_c - spec["thermal_margin_c"]
            left = starts[setting][SIDES[0]]
            hot, average = float(left.max()), float(left.mean())
            hypotheses = mirrored_starts(
                {"starting_temperatures_c": {"warm": hot, "cool": 2 * average - hot}}, settings)
            if any(not np.array_equal(hypotheses[side], starts[setting][side]) for side in SIDES):
                raise ValueError("Aggregate inputs must describe the same nine-hot, nine-cool assignments")

            routes = []
            candidates = ([edge for edge in edges if edge in predictor.responses]
                          for edges in network.edges.values())
            for route in product(*candidates):
                route_names = [edge.name for edge in route]
                predictions = {}
                for side in SIDES:
                    key = "_".join((name, setting, side, *route_names))
                    elapsed, peak = forecast(predictor, controller(predictor, route, ceiling), hypotheses[side])
                    predictions[side] = {"execution": key, "predicted_elapsed_s": elapsed, "predicted_peak_c": peak}
                    jobs[key] = (network, route, predictor, ceiling, starts[setting][side], walking, deadline)
                routes.append({
                    "route": route_names, "starts": predictions,
                    "aggregate": {metric: mean(row[metric] for row in predictions.values())
                                  for metric in ("predicted_elapsed_s", "predicted_peak_c")},
                })
            aggregate_rows = (route["aggregate"] | {"route": route["route"], "starts": route["starts"]}
                              for route in routes)
            aggregate = choose(aggregate_rows, deadline, ceiling)
            choices = {}
            for side in SIDES:
                per_motor = choose((route["starts"][side] | {"route": route["route"]} for route in routes),
                                   deadline, ceiling)
                choices[side] = {
                    "per_motor": per_motor["execution"] if per_motor is not None else None,
                    "aggregate": aggregate["starts"][side]["execution"] if aggregate is not None else None,
                }
            cases.append({"map": name, "family": course["family"], "setting": setting,
                          "deadline_s": deadline, "routes": routes, "selections": choices,
                          "initial_temperature_mean_c": average, "initial_temperature_max_c": hot})
    return cases, jobs


def execute(output, jobs, workers):
    folder = output / "missions"
    folder.mkdir(exist_ok=True)
    checkpoint = output / "executions.partial.json"
    completed_path = output / "executions.json"
    ledger = completed_path if completed_path.exists() else checkpoint
    runs = json.loads(ledger.read_text()) if ledger.exists() else {}
    if not runs.keys() <= jobs.keys() or (ledger == completed_path and runs.keys() != jobs.keys()):
        raise ValueError(f"Replay IDs do not match the frozen jobs in {ledger}")
    for key, record in runs.items():
        network, _, predictor, _, initial, walking, deadline = jobs[key]
        if record["trace"] != f"missions/{key}.npz" or not record.get("trace_sha256"):
            raise ValueError(f"Invalid saved record for {key}")
        audit_trace(output, record, initial, network, predictor.settings, deadline, walking["goal_radius"])

    print(f"Replaying {len(jobs)} warm routes ({len(runs)} already audited)", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        for key, (network, route, predictor, ceiling, initial, walking, deadline) in jobs.items():
            if key not in runs:
                regulator = controller(predictor, route, ceiling)
                path = folder / f"{key}.npz"
                pending[pool.submit(replay, network, route, regulator, initial, walking, deadline, path)] = key
        for future in as_completed(pending):
            key = pending[future]
            network, _, predictor, _, initial, walking, deadline = jobs[key]
            record = future.result()
            checks = audit_trace(output, record, initial, network, predictor.settings, deadline, walking["goal_radius"])
            runs[key] = record | checks
            save_json(checkpoint, runs)
            print(f"{len(runs)}/{len(jobs)} {key}: {record['failure'] or 'completed'}", flush=True)
    save_json(completed_path, dict(sorted(runs.items())))
    checkpoint.unlink(missing_ok=True)
    return runs


def run(config, output, workers):
    manifest, networks, thermal, starts, walking = design(config)
    if json.loads((output / "manifest.json").read_text()) != manifest:
        raise ValueError("The nominal profiles use a different design or runtime")
    spec = manifest["study"]
    old_courses = [course for path in config.parent.glob("*.json") if path != config
                   for course in json.loads(path.read_text()).get("maps", []) if "stages" in course]
    if any(row["id"] in networks or any(row["stages"] == course["stages"] for course in spec["maps"])
           for row in old_courses):
        raise ValueError("An evaluation course duplicates an earlier design")
    if len(networks) != len(spec["maps"]):
        raise ValueError("Evaluation course identifiers must be unique")

    with (output / ".run.lock").open("a") as lock_file:
        flock(lock_file, LOCK_EX | LOCK_NB)
        _, profiles, provenance = load_inputs(networks, spec, output, walking["goal_radius"])
        sources = ("hot_motor_swap", "hot_motor_swap_analysis", "hot_motor_swap_audit", "published_speed_baseline",
                   "reactive_forecast", "reactive_study", "margin_profiles")
        freeze_json(output / "evaluation_lock.json", {
            "protocol_sha256": digest(PROTOCOL),
            "nominal_manifest_sha256": digest(output / "manifest.json"),
            "nominal_index_sha256": digest(output / "edge_profiles.json"),
            "nominal_profiles": provenance,
            "source_sha256": {f"{stem}.py": digest(Path(__file__).with_name(f"{stem}.py")) for stem in sources},
        })
        cases, jobs = plan_cases(spec, networks, thermal, starts, walking, profiles)
        freeze_json(output / "plans.json", cases)
        runs = execute(output, jobs, workers)
        report = summarize(cases, runs, spec)
        report["nominal_profile_outcomes"] = dict(Counter(row["outcome"] for row in provenance.values()))
        save_json(output / "summary.json", report)
        print(f"Results: {output / 'summary.json'}", flush=True)


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=CONFIG, output=OUTPUT)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.config, args.output, args.workers)


if __name__ == "__main__":
    main()
