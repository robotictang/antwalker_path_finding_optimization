"""Plan edge speeds before departure and test them in continuous physics."""

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
import hashlib
from itertools import product
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from .connected_walk import walk_branch
from .network_planning import EdgeThermalModel, fastest_route, thermal_route
from .network_study import METHODS as BASELINES
from .network_study import write_json
from .pilot import walk_summary
from .route_speed_profiles import load_profiles_design, trace_name, validate_reference
from .thermal import ThermalState

NEW_METHODS = ("fastest_route_planned_speeds", "per_motor_route_and_speed")


@dataclass(frozen=True)
class SpeedAction:
    edge: object
    fraction: float

    @property
    def name(self):
        return f"{self.edge.name}_v{self.fraction:g}"


@dataclass
class SpeedSchedule:
    junctions: tuple[float, ...]
    fractions: tuple[float, ...]
    transition_s: float
    fraction: float = field(init=False)
    stage: int = field(init=False, default=0)
    time_s: float = field(init=False, default=0.0)
    events: list = field(init=False, default_factory=list)

    def __post_init__(self):
        if (len(self.fractions) != len(self.junctions) + 1 or self.transition_s <= 0
                or any(not 0 < fraction <= 1 for fraction in self.fractions)
                or any(left >= right for left, right in zip(self.junctions, self.junctions[1:]))):
            raise ValueError("Invalid edge speed schedule")
        self.fraction = self.fractions[0]

    def __call__(self, time, x, nominal):
        while self.stage < len(self.junctions) and x >= self.junctions[self.stage]:
            self.stage += 1
            self.events.append({"stage": self.stage + 1, "x_m": x, "walking_time_s": time,
                                "target_fraction": self.fractions[self.stage]})
        target = self.fractions[self.stage]
        increment = (time - self.time_s) / self.transition_s
        self.time_s = time
        self.fraction += max(-increment, min(target - self.fraction, increment))
        return nominal * self.fraction


def action_graph(network, actions, route=None):
    return SimpleNamespace(edges={
        stage: tuple(action for action in actions
                     if action.edge.stage == stage and (route is None or action.edge == route[stage]))
        for stage in network.edges
    })


def read_profiles(output, networks, fractions):
    records = json.loads((output / "edge_profiles.json").read_text())
    profiles, paths = {}, {}
    for name, network in networks.items():
        paths[name] = {}
        profiles[name] = {}
        for edges in network.edges.values():
            for edge, fraction in product(edges, fractions):
                action = SpeedAction(edge, fraction)
                filename = trace_name(name, edge, fraction)
                record = records[filename]
                with np.load(output / "profiles" / filename) as trace:
                    torque = trace["torque_nm"]
                profiles[name][action] = SimpleNamespace(completed=record["completed"],
                                                         elapsed_s=record["elapsed_s"], torques=torque)
                if fraction == 1:
                    paths[name][edge] = profiles[name][action]
    return profiles, paths


def replay(network, actions, spec, deadline, walking, settings, initial, output):
    route = network.route(tuple(action.edge for action in actions))
    policy = SpeedSchedule(tuple(network.junctions[1:-1]), tuple(action.fraction for action in actions),
                           spec["transition_s"])
    thermal = ThermalState(settings, initial)
    history = [thermal.temperature_c.copy()]
    walk = walk_branch(route, **walking, deadline=deadline, thermal=thermal, temperature_history=history,
                       position_speed_policy=policy)
    np.savez_compressed(output, torque_nm=walk.torques, temperature_c=np.asarray(history), body_xyz_m=walk.body_xyz_m,
                        foot_contacts=walk.foot_contacts, centerline_xy_m=np.column_stack((route.x, route.y)))
    return walk_summary(walk) | {
        "peak_c": float(thermal.peak_by_joint_c.max()), "junction_events": policy.events,
        "trace": f"missions/{output.name}",
    }


def run(config, reference, output, workers):
    spec, manifest, networks, settings, starts, walking = load_profiles_design(config)
    validate_reference(reference, manifest)
    profile_manifest = json.loads((output / "profile_manifest.json").read_text())
    reference_hash = hashlib.sha256((reference / "manifest.json").read_bytes()).hexdigest()
    if (profile_manifest["study"] != spec or profile_manifest["reference_manifest_sha256"] != reference_hash
            or profile_manifest["network_manifest"] != json.loads(json.dumps(manifest))):
        raise ValueError("Speed profiles do not match the current experiment")
    deadline = manifest["study"]["deadline_s"]
    walks, nominal = read_profiles(output, networks, spec["speed_fractions"])
    baseline = json.loads((reference / "decisions.json").read_text())
    old_runs = json.loads((reference / "executions.json").read_text())
    records = {(row["map"], row["setting"], row["start"], row["method"]): row for row in baseline}
    missions_dir = output / "missions"
    missions_dir.mkdir(exist_ok=False)
    write_json(output / "manifest.json", {
        **profile_manifest,
        "planner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_decisions_sha256": hashlib.sha256((reference / "decisions.json").read_bytes()).hexdigest(),
        "methods": [*BASELINES, *NEW_METHODS],
    })
    plans, runs, cases = [], {}, []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        for name, network in networks.items():
            fastest = fastest_route(network, nominal[name], deadline)
            for setting, thermal in settings.items():
                models = {action: EdgeThermalModel.from_walk(walk, thermal)
                          for action, walk in walks[name].items() if walk.completed}
                graphs = (action_graph(network, models, fastest) if fastest is not None else None,
                          action_graph(network, models))
                for start, initial in starts.items():
                    case = name, setting, start
                    cases.append(case)
                    for method, graph in zip(NEW_METHODS, graphs, strict=True):
                        label = thermal_route(graph, models, initial, thermal.limit_c, deadline) if graph else None
                        actions = label.edges if label is not None else ()
                        path = "_".join(action.edge.name for action in actions) or None
                        fractions = [action.fraction for action in actions]
                        identifier = "_".join((*case, *(action.name for action in actions))) if actions else None
                        source, key = None, identifier
                        if identifier and all(fraction == 1 for fraction in fractions):
                            matched = next((records[(*case, baseline_method)] for baseline_method in
                                            ("per_motor_fixed_speed", "fastest_fixed_speed")
                                            if records[(*case, baseline_method)]["route"] == path), None)
                            if matched is not None:
                                source, key = "reference", matched["execution"]
                        if key and source is None:
                            source = "continuous_replay"
                            if key not in pending:
                                pending[key] = pool.submit(replay, network, actions, spec, deadline, walking, thermal,
                                                           initial, missions_dir / f"{key}.npz")
                        plans.append({
                            "map": name, "setting": setting, "start": start, "method": method,
                            "route": path, "speed_fractions": fractions, "execution": key, "execution_source": source,
                            "predicted_peak_c": label.peak_c if label is not None else None,
                            "predicted_time_s": label.time_s if label is not None else None,
                            "predicted_junction_temperatures_c": (
                                [value.tolist() for value in label.junction_temperatures_c] if label else None
                            ),
                        })
        write_json(output / "plans.json", plans)
        print(f"Scheduled {len(plans)} speed-planning decisions and {len(pending)} new missions", flush=True)
        jobs = {future: key for key, future in pending.items()}
        for job in as_completed(jobs):
            key = jobs[job]
            runs[key] = job.result()
            print(f"{len(runs)}/{len(jobs)} {key}: {runs[key]['failure'] or 'completed'}", flush=True)
    rows = []
    for row in baseline:
        rows.append(row | {"execution_source": "reference" if row["execution"] else None})
    for plan in plans:
        key = plan["execution"]
        result = (old_runs if plan["execution_source"] == "reference" else runs)[key] if key else None
        rows.append(plan | {"completed": result["completed"] if result else False,
                            "failure": result["failure"] if result else "no_route"})
    summary = {}
    for method in (*BASELINES, *NEW_METHODS):
        selected = [row for row in rows if row["method"] == method]
        summary[method] = {"scheduled": len(selected),
                           "outcomes": dict(Counter(row["failure"] or "completed" for row in selected))}
    write_json(output / "decisions.json", rows)
    write_json(output / "executions.json", dict(sorted(runs.items())))
    write_json(output / "summary.json", {"by_method": summary, "new_physics_replays": len(runs)})
    print(json.dumps(summary, indent=2), flush=True)


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
