"""Compare one speed governor with and without a junction pause on fresh courses."""

from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import json
from math import exp
from pathlib import Path
from time import perf_counter

import numpy as np

from .connected_walk import walk_branch
from .junction_pause import JunctionPause
from .margin_profiles import digest
from .mission_analysis import paired_result
from .mission_profiles import arguments, design, run as profile_courses
from .model import JOINT_NAMES
from .network_study import write_json
from .pause_confirmation import read
from .pilot import walk_summary
from .published_speed_baseline import controller, forecast, outcome, replay as replay_unpaused
from .reactive_forecast import ProgressForecast
from .reactive_study import check_execution, load_inputs
from .thermal import ThermalState
from .walking import SAMPLE_SECONDS, STAND_SECONDS

CONFIG = Path("experiments/matched_pause.json")
OUTPUT = Path("results/matched_pause")
HOLD_MODEL = Path("results/pause_forecast_confirmation/pause_model.json")
PROTOCOL = Path("docs/matched_pause_protocol.md")
METHODS = ("governor_only", "governor_with_optional_pause")


def forecast_paused(predictor, governor, initial, pause_s, hold_load, milestones):
    """Use the baseline progress and gait clocks while applying the fixed hold load."""
    settings = predictor.settings
    state = ThermalState(settings, initial)
    for torque in governor.responses[0].fast.stand_torque:
        state.advance(torque, SAMPLE_SECONDS)
    temperatures = state.temperature_c
    peak = float(state.peak_by_joint_c.max())
    time = position = 0.0
    pause = JunctionPause(predictor.junctions[1], pause_s)
    while position < predictor.goal_x:
        speed = governor.command(time, position, temperatures)
        holding = pause(time, position, speed) == 0
        if holding:
            if "entry_peak_c" not in milestones:
                milestones["entry_peak_c"] = float(temperatures.max())
                milestones["stage_one_peak_c"] = peak
                milestones["start_s"] = STAND_SECONDS + time
            duration = min(predictor.step, pause.started_s + pause_s - time)
            loads = hold_load
        else:
            if pause.resumed_s is not None and "exit_peak_c" not in milestones:
                milestones["exit_peak_c"] = float(temperatures.max())
                milestones["resume_s"] = STAND_SECONDS + time
            response, local_x = governor.branch(position)
            rate, loads = response.at(local_x, (speed - predictor.slow_fraction) / predictor.speed_span)
            duration = min(predictor.step, (predictor.goal_x - position) / rate)
            position = (min(predictor.goal_x, position + rate * duration)
                        if duration == predictor.step else predictor.goal_x)
        equilibrium = settings.ambient_c + predictor._heat_factor * loads
        decay = predictor._decay if duration == predictor.step else exp(-duration / settings.time_constant_s)
        temperatures = equilibrium + (temperatures - equilibrium) * decay
        peak = max(peak, float(temperatures.max()))
        time += duration
    if "exit_peak_c" not in milestones:
        raise ValueError("Expected the two-stage forecast to reach and complete its pause")
    return STAND_SECONDS + time, peak


def admissible(candidate, deadline, ceiling):
    return candidate["predicted_elapsed_s"] <= deadline and candidate["predicted_peak_c"] < ceiling


def rank(candidate):
    return (candidate["predicted_elapsed_s"], candidate["predicted_peak_c"],
            tuple(candidate["route"]), candidate["pause_s"])


def select(available, initial, predictor, deadline, ceiling, spec, hold_load):
    """Evaluate shared zero-pause options first and charge both arms for their forecasts."""
    start = perf_counter()
    options = []
    for duration in (0, spec["pause_s"]):
        for route in available:
            if perf_counter() - start >= spec["planning_budget_s"]:
                break
            governor = controller(predictor, route, ceiling)
            milestones = {}
            if duration:
                arrival, peak = forecast_paused(predictor, governor, initial, duration, hold_load, milestones)
            else:
                arrival, peak = forecast(predictor, governor, initial)
            options.append({"route": [edge.name for edge in route], "pause_s": duration,
                            "predicted_elapsed_s": arrival, "predicted_peak_c": peak,
                            "predicted_pause": milestones or None})
        elapsed = perf_counter() - start
        viable = [candidate for candidate in options if admissible(candidate, deadline, ceiling)]
        timeout = elapsed >= spec["planning_budget_s"]
        selected = None if timeout else min(viable, key=rank, default=None)
        failure = "planning_timeout" if timeout else ("no_route" if selected is None else None)
        yield {"selected": selected, "planning_s": elapsed, "planning_failure": failure,
               "candidates": list(options)}


def replay(network, route, governor, initial, walking, deadline, path, pause_s):
    """Retain the original callback in the zero arm and mask forward speed only during the hold."""
    if pause_s == 0:
        return replay_unpaused(network, route, governor, initial, walking, deadline, path) | {"pause": None}
    pause = JunctionPause(network.junctions[1], pause_s)
    state = ThermalState(governor.settings, initial)
    history = [state.temperature_c.copy()]

    def speed(time, x, nominal):
        return pause(time, x, nominal * governor.command(time, x, state.temperature_c))

    walk = walk_branch(network.route(route), **walking, deadline=deadline, thermal=state,
                       temperature_history=history, position_speed_policy=speed)
    temperatures = np.array(history)
    np.savez_compressed(path, torque_nm=walk.torques, body_xyz_m=walk.body_xyz_m,
                        temperature_c=temperatures, foot_contacts=walk.foot_contacts)
    hold = None
    if pause.started_s is not None:
        start_s = STAND_SECONDS + pause.started_s
        end_s = STAND_SECONDS + pause.resumed_s if pause.resumed_s is not None else walk.elapsed_s
        first = int(start_s / SAMPLE_SECONDS + 1e-7)
        last = int(end_s / SAMPLE_SECONDS + 1e-7)
        before, after = temperatures[[first, last]]
        hottest = int(np.argmax(before))
        xy = walk.body_xyz_m[first - 1:last, :2]
        hold = {
            "started_s": start_s, "resumed_s": end_s if pause.resumed_s is not None else None,
            "samples": [first, last], "peak_before_c": float(before.max()), "peak_after_c": float(after.max()),
            "hottest_at_entry_joint": JOINT_NAMES[hottest], "entry_motor_delta_c": float(after[hottest] - before[hottest]),
            "max_drift_m": float(np.linalg.norm(xy - xy[0], axis=1).max()),
        }
    return walk_summary(walk) | {
        "peak_c": float(state.peak_by_joint_c.max()), "trace": f"missions/{path.name}",
        "speed_updates": governor.updates, "no_feasible_speed_updates": governor.infeasible_updates,
        "junction_events": governor.junction_events, "pause": hold,
    }


def lock(config, hold_model, protocol, manifest):
    reference = read(hold_model)
    spec = manifest["study"]
    variable_fields = {"name", "maps", "bootstrap_seed"}
    original = read(hold_model.with_name("manifest.json"))
    current_spec = {key: value for key, value in spec.items() if key not in variable_fields}
    original_spec = {key: value for key, value in original["study"].items() if key not in variable_fields}
    if current_spec != original_spec or any(
        manifest[field] != original[field] for field in ("base", "runtime", "thermal")
    ):
        raise ValueError("Fresh evaluation changed a frozen benchmark setting or runtime")
    old_courses = [row for path in config.parent.glob("*.json") if path != config
                   for row in read(path).get("maps", []) if "stages" in row]
    names = [row["id"] for row in spec["maps"]]
    geometries = [row["stages"] for row in spec["maps"]]
    if (len(names) != len(set(names)) or len({repr(stages) for stages in geometries}) != len(names)
            or any(row["id"] in names or row["stages"] in geometries for row in old_courses)):
        raise ValueError("Expected distinct courses outside all earlier configurations")
    family_counts = dict(Counter(row["family"] for row in spec["maps"]))
    if set(family_counts.values()) != {4} or set(family_counts) != {"alternating", "persistent", "same_sign_stage"}:
        raise ValueError("Expected 12 courses balanced over the three terrain families")
    hold_load = np.array([reference["squared_torque_nm2"][joint] for joint in JOINT_NAMES])
    if (np.any(hold_load < 0) or not np.isfinite(hold_load).all() or reference["pause_s"] != spec["pause_s"]
            or spec["pause_s"] % spec["forecast_step_s"] != 0
            or any(len(course["stages"]) != 2 for course in spec["maps"])):
        raise ValueError("Expected a valid frozen load for a two-stage pause in whole forecast steps")
    sources = dict(manifest["sha256"])
    sources.update({f"{stem}.py": digest(Path(__file__).with_name(f"{stem}.py")) for stem in (
        "matched_pause", "published_speed_baseline", "junction_pause", "pause_confirmation",
        "reactive_forecast", "reactive_study", "margin_profiles", "audit_network")})
    return {
        "protocol_sha256": digest(protocol), "hold_model_sha256": digest(hold_model),
        "design_and_sources_sha256": sources, "runtime": manifest["runtime"], "methods": list(METHODS),
        "expected_pairs": 72, "pause_s": spec["pause_s"], "terrain_families": family_counts,
        "minimum_gain_pp": spec["minimum_gain_pp"], "maximum_extra_thermal_stops": 0,
    }, hold_load


def plan_cases(manifest, networks, thermal, starts, walking, profiles, hold_load):
    spec = manifest["study"]
    plans, jobs = [], {}
    for case in spec["maps"]:
        name, deadline = case["id"], case["deadline_s"]
        network = networks[name]
        for setting, settings in thermal.items():
            predictor = ProgressForecast(network, profiles[name], settings, spec, walking["goal_radius"])
            ceiling = settings.limit_c - spec["thermal_margin_c"]
            available = tuple(product(*(tuple(edge for edge in edges if edge in predictor.responses)
                                        for edges in network.edges.values())))
            routes = {tuple(edge.name for edge in route): route for route in available}
            for start, initial in starts[setting].items():
                key = "_".join((name, setting, start))
                arms = dict(zip(METHODS, select(available, initial, predictor, deadline, ceiling, spec, hold_load),
                                strict=True))
                diagnostic = None

                def queue(selection):
                    route = routes[tuple(selection["route"])]
                    pause = selection["pause_s"]
                    execution = f"{key}_{'_'.join(selection['route'])}_pause{pause:g}"
                    jobs[execution] = (network, route, predictor, ceiling, initial, walking, deadline, pause)
                    return execution

                for arm in arms.values():
                    choice = arm["selected"]
                    arm["execution"] = queue(choice) if choice is not None else None
                    if choice is not None and choice["pause_s"]:
                        diagnostic = queue(choice | {"pause_s": 0})
                plans.append({"map": name, "family": case["family"], "setting": setting, "start": start,
                              "deadline_s": deadline, "ceiling_c": ceiling, "methods": arms,
                              "same_route_zero_execution": diagnostic})
    return plans, jobs


def summarize(plans, runs, spec):
    def counts(cases, method):
        return dict(Counter(outcome(case["methods"][method], runs) for case in cases))

    def grouped(by):
        group = defaultdict(list)
        for case in plans:
            group[case[by]].append(case)
        return {name: {method: counts(cases, method) for method in METHODS} for name, cases in group.items()}

    by_map = grouped("map")
    paired = []
    for name in by_map:
        paired.append([[outcome(case["methods"][method], runs) == "completed"
                        for case in plans if case["map"] == name] for method in METHODS])
    comparison = paired_result(paired, spec["bootstrap_seed"])
    comparison["optional_pause_only"] = comparison.pop("per_motor_only")
    comparison["governor_only"] = comparison.pop("anonymous_only")
    totals = {method: counts(plans, method) for method in METHODS}
    extra_stops = totals[METHODS[1]].get("thermal_limit", 0) - totals[METHODS[0]].get("thermal_limit", 0)
    comparison["extra_thermal_stops"] = extra_stops
    comparison["meets_practical_target"] = (
        comparison["mean_gain_pp"] >= spec["minimum_gain_pp"] and extra_stops <= 0
    )
    phases, reached_junction = defaultdict(Counter), Counter()
    pause_actions = Counter()
    same_route = []
    shared = 0
    for case in plans:
        arms = case["methods"]
        for method, plan in arms.items():
            if plan["execution"] is None:
                continue
            run = runs[plan["execution"]]
            reached_junction[method] += bool(run["junction_events"])
            if run["failure"] == "thermal_limit":
                if not run["junction_events"]:
                    where = "before_junction"
                elif run["pause"] is not None and run["pause"]["resumed_s"] is None:
                    where = "during_pause"
                else:
                    where = "after_junction"
                phases[method][where] += 1
        enabled = arms[METHODS[1]]
        pause_actions["admissible_starts"] += any(
            option["pause_s"] and admissible(option, case["deadline_s"], case["ceiling_c"])
            for option in enabled["candidates"]
        )
        shared += enabled["execution"] is not None and enabled["execution"] == arms[METHODS[0]]["execution"]
        key = case["same_route_zero_execution"]
        if key is not None:
            paused, unpaused = runs[enabled["execution"]], runs[key]
            pause_actions["selected"] += 1
            pause_actions["started"] += paused["pause"] is not None
            pause_actions["finished"] += paused["pause"] is not None and paused["pause"]["resumed_s"] is not None
            same_route.append({k: case[k] for k in ("map", "setting", "start")} | {
                "route": enabled["selected"]["route"], "warm_pause": paused["pause"],
                "enabled_outcome": paused["failure"] or "completed",
                "same_route_zero_outcome": unpaused["failure"] or "completed",
                "enabled_elapsed_s": paused["elapsed_s"], "same_route_zero_elapsed_s": unpaused["elapsed_s"],
                "enabled_peak_c": paused["peak_c"], "same_route_zero_peak_c": unpaused["peak_c"],
                "zero_execution": key, "paused_execution": enabled["execution"],
            })
    return {
        "paired_starts": len(plans), "physics_replays": len(runs), "shared_replays": shared,
        "outcomes": totals, "optional_pause_minus_governor": comparison, "by_map": by_map,
        "by_family": grouped("family"), "by_setting": grouped("setting"),
        "junction_reaches": dict(reached_junction), "thermal_stop_phases": dict(phases),
        "pause_actions": dict(pause_actions), "paused_same_route": same_route,
        "maximum_planning_s": {m: max(case["methods"][m]["planning_s"] for case in plans) for m in METHODS},
    }


def verify_plans(plans, jobs, spec):
    if len(plans) != 72 or len({(row["map"], row["setting"], row["start"]) for row in plans}) != 72:
        raise ValueError("Incomplete pairing")
    for case in plans:
        zero, enabled = (case["methods"][method] for method in METHODS)
        zero_options = [item for item in enabled["candidates"] if item["pause_s"] == 0]
        if zero_options != zero["candidates"]:
            raise ValueError("The zero-pause option sets diverged between the arms")
        for arm, durations in ((zero, {0}), (enabled, {0, spec["pause_s"]})):
            choice = arm["selected"]
            if (choice is None) != bool(arm["planning_failure"]) or (choice is None) != (arm["execution"] is None):
                raise ValueError("Inconsistent planner status")
            if arm["planning_failure"] == "planning_timeout":
                continue
            if arm["planning_s"] >= spec["planning_budget_s"]:
                raise ValueError("Planner exceeded budget without rejecting the case")
            for candidate in arm["candidates"]:
                if candidate["pause_s"] not in durations:
                    raise ValueError("Unavailable action entered selection")
            deadline = case["deadline_s"]
            ceiling = case["ceiling_c"]
            expected = min((c for c in arm["candidates"] if admissible(c, deadline, ceiling)), key=rank, default=None)
            if choice != expected or (choice is not None and arm["execution"] not in jobs):
                raise ValueError("Selected route does not match the frozen rank and gates")
        if (enabled["planning_failure"] != "planning_timeout" and zero["selected"] is not None
                and (enabled["selected"] is None or rank(enabled["selected"]) > rank(zero["selected"]))):
            raise ValueError("An optional pause displaced a better zero-pause plan")


def verify_prefix(paused_path, unpaused_path, paused, expected_duration):
    """Prove physical states agree through the sample before the intervention."""
    pause = paused["pause"]
    with np.load(paused_path) as left, np.load(unpaused_path) as right:
        if pause is None:
            if any(not np.array_equal(left[k], right[k]) for k in left.files):
                raise ValueError("Physical trajectories diverged before the junction")
            return
        first, _ = pause["samples"]
        if len(right["torque_nm"]) < first or any(not np.array_equal(left[k][:first], right[k][:first])
                                                 for k in left.files):
            raise ValueError("Same-route physics differed before the pause")
        if pause["resumed_s"] is not None and not np.isclose(
            pause["resumed_s"] - pause["started_s"], expected_duration, atol=0.0021
        ):
            raise ValueError("Observed pause differs from the command")


def execute(output, workers, manifest, networks, thermal, starts, walking, hold_load):
    if read(output / "manifest.json") != manifest:
        raise ValueError("Nominal profiles use a different design or runtime")
    spec = manifest["study"]
    _, profiles, provenance = load_inputs(networks, spec, output, walking["goal_radius"])
    write_json(output / "profile_checksums.json", provenance)
    plans, jobs = plan_cases(manifest, networks, thermal, starts, walking, profiles, hold_load)
    verify_plans(plans, jobs, spec)
    folder = output / "missions"
    folder.mkdir(exist_ok=False)
    write_json(output / "plans.json", plans)
    print(f"{len(plans)} paired starts; {len(jobs)} unique physics replays", flush=True)
    runs = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        for key, (network, route, predictor, ceiling, initial, walking, deadline, duration) in jobs.items():
            path = folder / f"{key}.npz"
            args = (network, route, controller(predictor, route, ceiling), initial, walking, deadline, path, duration)
            pending[pool.submit(replay, *args)] = key
        for index, future in enumerate(as_completed(pending), 1):
            key = pending[future]
            network, _, predictor, _, initial, walking, deadline, _ = jobs[key]
            record = future.result()
            path = output / record["trace"]
            check_execution(path, record, initial, network, predictor.settings, deadline, walking["goal_radius"])
            runs[key] = record | {"sha256": digest(path)}
            print(f"{index}/{len(jobs)} {key}: {record['failure'] or 'completed'}", flush=True)
    for case in plans:
        if case["same_route_zero_execution"] is not None:
            paused = runs[case["methods"][METHODS[1]]["execution"]]
            unpaused = runs[case["same_route_zero_execution"]]
            verify_prefix(output / paused["trace"], output / unpaused["trace"], paused, spec["pause_s"])
    write_json(output / "executions.json", dict(sorted(runs.items())))
    report = summarize(plans, runs, spec)
    write_json(output / "summary.json", report)
    print(report["outcomes"], report["optional_pause_minus_governor"], flush=True)


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=CONFIG, output=OUTPUT)
    parser.add_argument("action", choices=("freeze", "profiles", "execute"))
    parser.add_argument("--hold-model", type=Path, default=HOLD_MODEL)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    manifest, *design_inputs = design(args.config)
    manifest = json.loads(json.dumps(manifest))
    frozen, hold_load = lock(args.config, args.hold_model, args.protocol, manifest)
    path = args.output / "evaluation_lock.json"
    if args.action == "freeze":
        args.output.mkdir(parents=True, exist_ok=True)
        if (args.output / "profiles").exists():
            raise ValueError("Freeze the design before generating fresh profiles")
        with path.open("x") as handle:
            json.dump(frozen, handle, indent=2, allow_nan=False)
            handle.write("\n")
    elif read(path) != frozen:
        raise ValueError("The experiment differs from its frozen protocol")
    elif args.action == "profiles":
        profile_courses(args.config, args.output, args.workers)
    else:
        execute(args.output, args.workers, manifest, *design_inputs, hold_load)


if __name__ == "__main__":
    main()
