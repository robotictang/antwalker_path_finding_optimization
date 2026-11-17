"""Adapt Trujillo and Cutkosky's gait-period thermal speed rule to the hexapod."""

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import product
import json
from math import exp, expm1
from pathlib import Path
from time import perf_counter

import numpy as np

from .connected_walk import walk_branch
from .margin_profiles import digest
from .mission_analysis import paired_result
from .mission_profiles import arguments, design
from .network_study import write_json
from .pause_confirmation import CONFIG, OUTPUT, confirmation_lock
from .pause_forecast_study import METHODS, read
from .pilot import walk_summary
from .reactive_forecast import ProgressForecast
from .reactive_study import check_execution, load_inputs
from .thermal import ThermalState
from .walking import PHASES, SAMPLE_SECONDS, STAND_SECONDS, WALK_PERIOD

METHOD = "published_gait_period_speed"
SOURCE = "https://doi.org/10.1109/ROBOT.2009.5152870"
DEFAULT_OUTPUT = Path("results/published_speed_baseline")


def squared_torque_budget(temperatures, ceiling, settings, horizon):
    """Invert the shared thermal update to bound average heat over one gait period."""
    weight = -expm1(-horizon / settings.time_constant_s)
    equilibrium = temperatures + (ceiling - temperatures) / weight
    return (equilibrium - settings.ambient_c) * settings.reference_torque_nm ** 2 / settings.rise_at_reference_c


def fastest_feasible_blend(slow_load, fast_load, budget):
    """Intersect the per-motor inequalities on the interpolated speed range."""
    change = fast_load - slow_load
    slack = budget - slow_load
    if np.any((change == 0) & (slack < 0)):
        return None
    upper = min(1.0, float(np.min(slack[change > 0] / change[change > 0], initial=1.0)))
    lower = max(0.0, float(np.max(slack[change < 0] / change[change < 0], initial=0.0)))
    if lower > upper:
        return None
    return upper


@dataclass
class SpeedRegulator:
    junctions_m: tuple
    responses: tuple
    settings: object
    ceiling_c: float
    slow_fraction: float
    horizon_s: float = WALK_PERIOD
    footfall_s: float = WALK_PERIOD / len(PHASES)

    def __post_init__(self):
        self.next_update_s = 0.0
        self.fraction = 1.0
        self.updates = 0
        self.infeasible_updates = 0
        self.stage = 0
        self.junction_events = []

    def branch(self, x):
        return self.responses[self.stage], max(0.0, x - self.junctions_m[self.stage])

    def command(self, time, x, temperatures):
        if self.stage + 1 < len(self.responses) and x >= self.junctions_m[self.stage + 1]:
            self.stage += 1
            self.junction_events.append({"stage": self.stage, "x_m": x, "walking_time_s": time})
        if time <= 0 or time + 1e-9 < self.next_update_s:
            return self.fraction
        self.next_update_s = (int((time + 1e-9) / self.footfall_s) + 1) * self.footfall_s
        self.updates += 1
        response, local_x = self.branch(x)
        _, slow = response.at(local_x, 0.0)
        _, fast = response.at(local_x, 1.0)
        budget = squared_torque_budget(temperatures, self.ceiling_c, self.settings, self.horizon_s)
        blend = fastest_feasible_blend(slow, fast, budget)
        if blend is None:
            self.infeasible_updates += 1
            blend = 0.0
        self.fraction = self.slow_fraction + (1 - self.slow_fraction) * blend
        return self.fraction


def controller(predictor, edges, ceiling):
    return SpeedRegulator(predictor.junctions, tuple(predictor.responses[e] for e in edges),
                          predictor.settings, ceiling, predictor.slow_fraction)


def forecast(predictor, regulator, initial):
    settings = predictor.settings
    state = ThermalState(settings, initial)
    for torque in regulator.responses[0].fast.stand_torque:
        state.advance(torque, SAMPLE_SECONDS)
    temperatures = state.temperature_c
    peak = float(state.peak_by_joint_c.max())
    time = position = 0.0
    while position < predictor.goal_x:
        fraction = regulator.command(time, position, temperatures)
        response, local_x = regulator.branch(position)
        rate, loads = response.at(local_x, (fraction - predictor.slow_fraction) / predictor.speed_span)
        duration = min(predictor.step, (predictor.goal_x - position) / rate)
        equilibrium = settings.ambient_c + predictor._heat_factor * loads
        decay = predictor._decay if duration == predictor.step else exp(-duration / settings.time_constant_s)
        temperatures = equilibrium + (temperatures - equilibrium) * decay
        peak = max(peak, float(temperatures.max()))
        position = min(predictor.goal_x, position + rate * duration) if duration == predictor.step else predictor.goal_x
        time += duration
    return STAND_SECONDS + time, peak


def choose_route(network, predictor, initial, deadline, ceiling, budget):
    start = perf_counter()
    candidates = [[edge for edge in edges if edge in predictor.responses] for edges in network.edges.values()]
    best = None
    examined = 0
    for route in product(*candidates):
        if perf_counter() - start >= budget:
            break
        regulator = controller(predictor, route, ceiling)
        arrival, peak = forecast(predictor, regulator, initial)
        examined += 1
        rank = (arrival, peak, tuple(edge.name for edge in route))
        if arrival <= deadline and peak < ceiling and (best is None or rank < best[0]):
            best = rank, route
    elapsed = perf_counter() - start
    if elapsed >= budget:
        return (), elapsed, examined, None, "planning_timeout"
    if best is None:
        return (), elapsed, examined, None, "no_route"
    return best[1], elapsed, examined, best[0][:2], None


def replay(network, route, regulator, initial, walking, deadline, path):
    state = ThermalState(regulator.settings, initial)
    temperatures = [state.temperature_c.copy()]

    def speed(time, x, nominal):
        return nominal * regulator.command(time, x, state.temperature_c)

    walk = walk_branch(network.route(route), **walking, deadline=deadline, thermal=state,
                       temperature_history=temperatures, position_speed_policy=speed)
    np.savez_compressed(path, torque_nm=walk.torques, body_xyz_m=walk.body_xyz_m,
                        temperature_c=np.array(temperatures), foot_contacts=walk.foot_contacts)
    return walk_summary(walk) | {
        "peak_c": float(state.peak_by_joint_c.max()), "trace": f"missions/{path.name}",
        "speed_updates": regulator.updates, "no_feasible_speed_updates": regulator.infeasible_updates,
        "junction_events": regulator.junction_events,
    }


def outcome(plan, replays):
    if not plan["execution"]:
        return plan["planning_failure"]
    return replays[plan["execution"]]["failure"] or "completed"


def summarize(plans, runs, original_plans, original_runs, seed):
    by_course = {}
    archived = defaultdict(dict)
    for original in original_plans:
        case = (original["map"], original["setting"], original["start"])
        archived[case][original["method"]] = outcome(original, original_runs)
    added = defaultdict(list)
    for plan in plans:
        case = (plan["map"], plan["setting"], plan["start"])
        values = archived[case] | {METHOD: outcome(plan, runs)}
        added[case[0]].append(values)
    for name, cases in added.items():
        by_course[name] = {m: dict(Counter(case[m] for case in cases)) for m in (METHOD, *METHODS)}
    comparison = paired_result([
        ([case[METHOD] == "completed" for case in cases], [case[METHODS[-1]] == "completed" for case in cases])
        for cases in added.values()
    ], seed)
    comparison["pause_only"] = comparison.pop("per_motor_only")
    comparison["published_only"] = comparison.pop("anonymous_only")
    total = {m: dict(Counter(case[m] for cases in added.values() for case in cases)) for m in (METHOD, *METHODS)}
    comparison["additional_thermal_stops_pause_minus_published"] = (
        total[METHODS[-1]].get("thermal_limit", 0) - total[METHOD].get("thermal_limit", 0)
    )
    return {
        "starts": len(plans), "physics_replays": len(runs), "outcomes": total, "by_course": by_course,
        "pause_minus_published": comparison, "maximum_selection_s": max(row["planning_s"] for row in plans),
        "no_feasible_speed_updates": sum(run["no_feasible_speed_updates"] for run in runs.values()),
    }


def run(config, archive, output, workers):
    locked = read(archive / "confirmation_lock.json")
    if locked != json.loads(json.dumps(confirmation_lock(config, archive.parent))):
        raise ValueError("Reference comparison no longer matches its design")
    manifest, networks, thermal, starts, walking = design(config)
    if read(archive / "manifest.json") != json.loads(json.dumps(manifest)):
        raise ValueError("Reference simulator configuration changed")
    spec = manifest["study"]
    _, profiles, provenance = load_inputs(networks, spec, archive, walking["goal_radius"])
    if provenance != read(archive / "evaluation_manifest.json")["profile_hashes"]:
        raise ValueError("Reference branch profiles changed")
    deadlines = {row["id"]: row["deadline_s"] for row in spec["maps"]}
    folder = output / "missions"
    folder.mkdir(parents=True, exist_ok=False)
    write_json(output / "manifest.json", {
        "method": METHOD, "paper": SOURCE, "paper_section": "III-D, Eq. (8)",
        "reference_hashes": {name: digest(archive / name) for name in (
            "confirmation_lock.json", "manifest.json", "evaluation_manifest.json", "plans.json", "executions.json")},
        "source_sha256": digest(Path(__file__)), "gait_horizon_s": WALK_PERIOD,
        "footfall_s": WALK_PERIOD / len(PHASES), "thermal_margin_c": spec["thermal_margin_c"],
        "planning_budget_s": spec["planning_budget_s"],
    })

    plans, jobs = [], {}
    for name, network in networks.items():
        for setting, settings in thermal.items():
            predictor = ProgressForecast(network, profiles[name], settings, spec, walking["goal_radius"])
            ceiling = settings.limit_c - spec["thermal_margin_c"]
            for start, initial in starts[setting].items():
                route, elapsed, examined, prediction, failure = choose_route(
                    network, predictor, initial, deadlines[name], ceiling, spec["planning_budget_s"])
                key = "_".join((name, setting, start)) if route else None
                row = {"map": name, "setting": setting, "start": start, "method": METHOD, "execution": key,
                       "route": [edge.name for edge in route], "planning_failure": failure, "planning_s": elapsed,
                       "routes_examined": examined, "predicted_elapsed_s": prediction[0] if prediction else None,
                       "predicted_peak_c": prediction[1] if prediction else None}
                plans.append(row)
                if route:
                    jobs[key] = (network, route, controller(predictor, route, ceiling), initial, walking,
                                 deadlines[name], folder / f"{key}.npz")
    write_json(output / "plans.json", plans)
    print(f"{len(plans)} paired decisions, {len(jobs)} published-controller replays", flush=True)

    runs = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(replay, *args): key for key, args in jobs.items()}
        for finish, future in enumerate(as_completed(pending), 1):
            key = pending[future]
            record = future.result()
            network, _, regulator, initial, _, deadline, path = jobs[key]
            check_execution(path, record, initial, network, regulator.settings, deadline, walking["goal_radius"])
            runs[key] = record | {"trace_sha256": digest(path)}
            print(f"{finish}/{len(jobs)} {key}: {record['failure'] or 'completed'}", flush=True)
    write_json(output / "executions.json", dict(sorted(runs.items())))
    report = summarize(plans, runs, read(archive / "plans.json"), read(archive / "executions.json"),
                       spec["bootstrap_seed"])
    write_json(output / "summary.json", report)
    print(report["outcomes"], report["pause_minus_published"], flush=True)


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=CONFIG, output=DEFAULT_OUTPUT)
    parser.add_argument("--archive", type=Path, default=OUTPUT)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.config, args.archive, args.output, args.workers)


if __name__ == "__main__":
    main()
