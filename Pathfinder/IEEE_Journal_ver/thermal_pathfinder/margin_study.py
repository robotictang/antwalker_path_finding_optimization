"""Replay zero-margin plans and evaluate stricter thermal admission thresholds."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import json
from pathlib import Path

from .margin_profiles import METHODS, calibration, load_design
from .network_planning import EdgeThermalModel, fastest_route, thermal_route
from .network_study import write_json
from .route_speed_study import action_graph, read_profiles, replay


def verified_design(config, development, reference, output):
    lock, networks, settings, starts, walking = load_design(config)
    lock["calibration"] = calibration(development, reference, lock["study"]["margin_grid_c"])
    saved = json.loads((output / "manifest.json").read_text())
    if saved != json.loads(json.dumps(lock)):
        raise ValueError("Saved source lock or calibration inputs do not match")
    return saved, networks, settings, starts, walking


def make_plans(networks, walks, nominal, settings, starts, deadline):
    for name, network in networks.items():
        fastest = fastest_route(network, nominal[name], deadline)
        for setting, thermal in settings.items():
            actions = {action: EdgeThermalModel.from_walk(walk, thermal)
                       for action, walk in walks[name].items() if walk.completed}
            fixed = {action: model for action, model in actions.items() if action.fraction == 1}
            graphs = (action_graph(network, fixed),
                      action_graph(network, actions, fastest) if fastest else None,
                      action_graph(network, actions))
            for start, method in product(starts, METHODS):
                graph = graphs[METHODS.index(method)]
                label = thermal_route(graph, actions, starts[start], thermal.limit_c, deadline) if graph else None
                schedule = label.edges if label else ()
                key = "_".join((name, setting, start, *(action.name for action in schedule))) if schedule else None
                yield {
                    "map": name, "setting": setting, "start": start, "method": method, "execution": key,
                    "route": [action.edge.name for action in schedule],
                    "speed_fractions": [action.fraction for action in schedule],
                    "predicted_peak_c": label.peak_c if label else None,
                    "predicted_elapsed_s": label.time_s if label else None,
                    "thermal_limit_c": thermal.limit_c,
                }, schedule


def run(config, development, reference, output, workers):
    manifest, networks, settings, starts, walking = verified_design(config, development, reference, output)
    spec = manifest["study"]
    deadline = spec["deadline_s"]
    walks, nominal = read_profiles(output, networks, spec["speed_fractions"])
    folder = output / "missions"
    folder.mkdir(exist_ok=False)
    plans, runs = [], {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        for plan, schedule in make_plans(networks, walks, nominal, settings, starts, deadline):
            plans.append(plan)
            key = plan["execution"]
            if key and key not in pending:
                pending[key] = pool.submit(replay, networks[plan["map"]], schedule, spec, deadline, walking,
                                           settings[plan["setting"]], starts[plan["start"]], folder / f"{key}.npz")
        write_json(output / "plans.json", plans)
        print(f"{len(plans)} base decisions; {len(pending)} distinct continuous mission replays", flush=True)
        jobs = {future: key for key, future in pending.items()}
        for index, job in enumerate(as_completed(jobs), 1):
            key = jobs[job]
            runs[key] = job.result()
            print(f"{index}/{len(jobs)} {key}: {runs[key]['failure'] or 'completed'}", flush=True)
    write_json(output / "executions.json", dict(sorted(runs.items())))


def arguments(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", type=Path, default=Path("experiments/thermal_margin_study.json"))
    parser.add_argument("--development", type=Path, default=Path("results/route_speed_study"))
    parser.add_argument("--reference", type=Path, default=Path("results/network_study"))
    parser.add_argument("--output", type=Path, default=Path("results/thermal_margin_study"))
    return parser


def main():
    parser = arguments(__doc__)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.development, args.reference, args.output, args.workers)


if __name__ == "__main__":
    main()
