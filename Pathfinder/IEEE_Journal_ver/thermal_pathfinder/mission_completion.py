"""Compare labeled and anonymous initial motor temperatures on the same graph."""

from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .connected_walk import walk_branch
from .mission_profiles import arguments, design
from .network_planning import EdgeThermalModel
from .network_study import write_json
from .pilot import walk_summary
from .route_speed_study import SpeedSchedule, read_profiles
from .speed_policy import ThermalSlowdown
from .thermal import ThermalState

METHODS = ("anonymous_route_speed_adaptive", "per_motor_route_speed_adaptive")


def forecast(schedule, models, initial):
    peak = float(initial.max())
    for action in schedule:
        initial, edge_peak = models[action].propagate(initial)
        peak = max(peak, edge_peak)
    return peak


def choose_route(network, models, initial_hypotheses, deadline, ceiling, budget):
    started = perf_counter()
    stages = [[action for action in models if action.edge.stage == stage] for stage in network.edges]
    best = None
    examined = 0
    for schedule in product(*stages):
        if perf_counter() - started >= budget:
            return (), None, None, perf_counter() - started, examined, "planning_timeout"
        elapsed = sum(models[action].elapsed_s for action in schedule)
        if elapsed > deadline:
            continue
        examined += 1
        peak = float(np.mean([forecast(schedule, models, start) for start in initial_hypotheses]))
        key = (peak, elapsed, tuple(action.name for action in schedule))
        if peak < ceiling and (best is None or key < best[0]):
            best = (key, schedule)
    duration = perf_counter() - started
    if duration >= budget:
        return (), None, None, duration, examined, "planning_timeout"
    if best is None:
        return (), None, None, duration, examined, "no_route"
    return best[1], best[0][0], best[0][1], duration, examined, None


def replay(network, schedule, spec, deadline, walking, settings, initial, path):
    route = network.route(tuple(action.edge for action in schedule))
    plan = SpeedSchedule(tuple(network.junctions[1:-1]), tuple(action.fraction for action in schedule),
                         spec["transition_s"])
    reactive = ThermalSlowdown(**spec["reactive"])
    thermal = ThermalState(settings, initial)
    history = [thermal.temperature_c.copy()]

    def speed(time, x, nominal):
        return min(plan(time, x, nominal), reactive(time, nominal, thermal))

    walk = walk_branch(route, **walking, deadline=deadline, thermal=thermal, temperature_history=history,
                       position_speed_policy=speed)
    np.savez_compressed(path, torque_nm=walk.torques, body_xyz_m=walk.body_xyz_m,
                        temperature_c=np.asarray(history), foot_contacts=walk.foot_contacts)
    return walk_summary(walk) | {
        "peak_c": float(thermal.peak_by_joint_c.max()), "trace": f"missions/{path.name}",
        "junction_events": plan.events, "slowdown_events": reactive.events,
    }


def run(config, output, workers):
    lock, networks, settings, starts, walking = design(config)
    saved = json.loads((output / "manifest.json").read_text())
    if saved != json.loads(json.dumps(lock)):
        raise ValueError("The frozen experiment does not match current source and settings")
    spec = lock["study"]
    walks, _ = read_profiles(output, networks, spec["speed_fractions"])
    deadlines = {item["id"]: item["deadline_s"] for item in spec["maps"]}
    folder = output / "missions"
    folder.mkdir(exist_ok=False)
    decisions, schedules = [], {}
    # Measure plan selection before physics workers start.
    for name, network in networks.items():
        for setting, thermal in settings.items():
            models = {action: EdgeThermalModel.from_walk(walk, thermal)
                      for action, walk in walks[name].items() if walk.completed}
            anonymous = tuple(starts[setting].values())
            aggregate_plan = choose_route(network, models, anonymous, deadlines[name],
                                          thermal.limit_c - spec["thermal_margin_c"], spec["planning_budget_s"])
            for start, initial in starts[setting].items():
                per_motor = choose_route(network, models, (initial,), deadlines[name],
                                         thermal.limit_c - spec["thermal_margin_c"], spec["planning_budget_s"])
                for method, decision in zip(METHODS, (aggregate_plan, per_motor), strict=True):
                    schedule, peak, duration, planning_s, examined, failure = decision
                    key = "_".join((name, setting, start, *(action.name for action in schedule))) if schedule else None
                    if key:
                        schedules[key] = (name, setting, start, schedule)
                    decisions.append({
                        "map": name, "setting": setting, "start": start, "method": method,
                        "execution": key, "route": [action.edge.name for action in schedule],
                        "speed_fractions": [action.fraction for action in schedule],
                        "predicted_peak_c": peak, "predicted_elapsed_s": duration,
                        "planning_s": planning_s, "schedules_examined": examined, "planning_failure": failure,
                    })
    write_json(output / "plans.json", decisions)
    print(f"Saved {len(decisions)} paired decisions; running {len(schedules)} distinct warm walks", flush=True)
    results = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {
            pool.submit(replay, networks[name], schedule, spec, deadlines[name], walking, settings[setting],
                        starts[setting][start], folder / f"{key}.npz"): key
            for key, (name, setting, start, schedule) in schedules.items()
        }
        for count, future in enumerate(as_completed(pending), 1):
            key = pending[future]
            results[key] = future.result()
            print(f"{count}/{len(pending)} {key}: {results[key]['failure'] or 'completed'}", flush=True)
    write_json(output / "executions.json", dict(sorted(results.items())))


def main():
    parser = arguments(__doc__)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.config, args.output, args.workers)


if __name__ == "__main__":
    main()
