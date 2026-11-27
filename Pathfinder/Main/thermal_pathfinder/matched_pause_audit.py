"""Audit the frozen matched comparison without running any new physics."""

from collections import Counter
from itertools import product
import json
from pathlib import Path

import numpy as np

from .margin_profiles import digest
from .matched_pause import CONFIG, HOLD_MODEL, METHODS, OUTPUT, PROTOCOL, forecast_paused, lock, summarize
from .mission_profiles import arguments, design
from .model import JOINT_NAMES
from .network_study import write_json
from .pause_confirmation import read
from .published_speed_baseline import controller, forecast
from .reactive_forecast import ProgressForecast
from .reactive_study import check_execution, load_inputs
from .walking import SAMPLE_SECONDS, STAND_SECONDS

TRACE_FIELDS = {"torque_nm", "body_xyz_m", "temperature_c", "foot_contacts"}
RESULT_FILES = ("evaluation_lock.json", "manifest.json", "edge_profiles.json", "profile_checksums.json",
                "plans.json", "executions.json", "summary.json")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def candidate_rank(candidate):
    return (candidate["predicted_elapsed_s"], candidate["predicted_peak_c"],
            tuple(candidate["route"]), candidate["pause_s"])


def trace_key(case, route, duration):
    return "_".join((*case, *route, f"pause{duration:g}"))


def check_plans(plans, networks, thermal, starts, walking, profiles, spec, hold_load):
    cases = {(row["map"], row["setting"], row["start"]): row for row in plans}
    expected_cases = {(name, setting, start) for name, setting in product(networks, thermal)
                      for start in starts[setting]}
    require(len(plans) == len(cases) and set(cases) == expected_cases, "Incomplete matched start pairs")
    maps = {row["id"]: row for row in spec["maps"]}
    jobs, diagnostics = {}, []
    counts = Counter()
    for case, row in cases.items():
        name, setting, start = case
        network, settings, initial = networks[name], thermal[setting], starts[setting][start]
        predictor = ProgressForecast(network, profiles[name], settings, spec, walking["goal_radius"])
        route_options = product(*(tuple(edge for edge in edges if edge in predictor.responses)
                                  for edges in network.edges.values()))
        routes = {tuple(edge.name for edge in route): route for route in route_options}
        duration = spec["pause_s"]
        deadline, ceiling = maps[name]["deadline_s"], settings.limit_c - spec["thermal_margin_c"]
        require(row["family"] == maps[name]["family"] and row["deadline_s"] == deadline
                and row["ceiling_c"] == ceiling and set(row["methods"]) == set(METHODS),
                f"Wrong pairing, admission gates or terrain family for {case}")
        control, optional = (row["methods"][method] for method in METHODS)
        observed_zero = [entry for entry in optional["candidates"] if entry["pause_s"] == 0]
        require(control["candidates"] == observed_zero, f"Zero-pause candidate forecasts differ for {case}")
        for option in optional["candidates"]:
            route_name = tuple(option["route"])
            require(route_name in routes, f"Route uses unsupported branches for {case}")
            governor = controller(predictor, routes[route_name], ceiling)
            milestones = {}
            if option["pause_s"] == duration:
                arrival, peak = forecast_paused(predictor, governor, initial, duration, hold_load, milestones)
                counts["paused_forecasts"] += 1
            else:
                require(option["pause_s"] == 0, f"Unknown pause duration for {case}")
                arrival, peak = forecast(predictor, governor, initial)
                counts["original_governor_forecasts"] += 1
            require((arrival, peak, milestones or None) == (option["predicted_elapsed_s"],
                    option["predicted_peak_c"], option["predicted_pause"]), f"Forecast differs for {case}")

        for arm, allowed in ((control, (0,)), (optional, (0, duration))):
            candidates = arm["candidates"]
            expected_options = [(route, pause) for pause in allowed for route in routes]
            observed_options = [(tuple(item["route"]), item["pause_s"]) for item in candidates]
            elapsed = arm["planning_s"]
            timed_out = elapsed >= spec["planning_budget_s"]
            require(np.isfinite(elapsed) and elapsed >= 0, f"Invalid planning time for {case}")
            require(observed_options == (expected_options[:len(candidates)] if timed_out else expected_options),
                    f"Unexpected candidate set for {case}")
            admitted = [item for item in candidates if item["predicted_elapsed_s"] <= deadline
                        and item["predicted_peak_c"] < ceiling]
            best = None if timed_out else min(admitted, key=candidate_rank, default=None)
            failure = "planning_timeout" if timed_out else ("no_route" if best is None else None)
            key = trace_key(case, best["route"], best["pause_s"]) if best is not None else None
            require((best, failure, key) == (arm["selected"], arm["planning_failure"], arm["execution"]),
                    f"Admission, rank or physics key differs for {case}")
            if key is not None:
                jobs[key] = (case, best["pause_s"])

        choice = optional["selected"]
        if choice is not None and choice["pause_s"] == duration:
            key = trace_key(case, choice["route"], 0)
            require(row["same_route_zero_execution"] == key, f"Missing same-route diagnostic for {case}")
            jobs[key] = (case, 0)
            diagnostics.append((optional["execution"], key))
        else:
            require(row["same_route_zero_execution"] is None, f"Unexpected same-route diagnostic for {case}")
    return jobs, diagnostics, dict(counts)


def check_traces(output, runs, jobs, networks, thermal, starts, walking, spec):
    require(set(runs) == set(jobs), "Missing or unexpected execution records")
    require({path.name for path in (output / "missions").glob("*.npz")} == {f"{key}.npz" for key in runs},
            "Missing or unexpected warm trace files")
    max_residual = 0.0
    deadlines = {row["id"]: row["deadline_s"] for row in spec["maps"]}
    for key, ((name, setting, start), duration) in jobs.items():
        record = runs[key]
        expected_path = f"missions/{key}.npz"
        path = output / expected_path
        require(record["trace"] == expected_path and digest(path) == record["sha256"],
                f"Replay provenance differs for {key}")
        network, settings, initial = networks[name], thermal[setting], starts[setting][start]
        deadline = deadlines[name]
        check_execution(path, record, initial, network, settings, deadline, walking["goal_radius"])
        with np.load(path) as trace:
            require(set(trace.files) == TRACE_FIELDS, f"Unexpected trace fields for {key}")
            temperature, torque, body, contacts = (trace[field] for field in
                                                    ("temperature_c", "torque_nm", "body_xyz_m", "foot_contacts"))
        require(torque.shape == (len(body), len(JOINT_NAMES)) and body.shape == (len(body), 3)
                and temperature.shape == (len(body) + 1, len(JOINT_NAMES)) and contacts.shape == (len(body),)
                and all(np.isfinite(array).all() for array in (temperature, torque, body, contacts))
                and np.all((contacts >= 0) & (contacts <= 6)), f"Invalid sampled values for {key}")
        inferred = settings.advance(temperature[:-1], torque, SAMPLE_SECONDS)
        residual = float(np.max(np.abs(temperature[1:] - inferred), initial=0))
        require(residual < 1e-12, f"Logged temperature disagrees with applied torque for {key}")
        max_residual = max(max_residual, residual)

        failure = record["failure"]
        thermal_hit = np.any(temperature[-1] >= settings.limit_c)
        require(failure in (None, "thermal_limit", "deadline", "fall_or_chassis_contact", "left_corridor")
                and record["peak_c"] == float(temperature.max())
                and (not len(body) or record["forward_m"] == float(body[-1, 0]))
                and record["completed"] == (failure is None) and (failure == "thermal_limit") == thermal_hit
                and np.all(temperature[:-1] < settings.limit_c) and record["elapsed_s"] <= deadline + 1e-6,
                f"Thermal stop, deadline or completion status differs for {key}")
        if failure == "deadline":
            require(len(body) == int(deadline / SAMPLE_SECONDS), f"Deadline trace ended early for {key}")
        hold = record["pause"]
        events = record["junction_events"]
        require(len(events) <= 1 and (hold is not None) == bool(duration and events),
                f"Unexpected junction or pause record for {key}")
        if events:
            event = events[0]
            require(event["stage"] == 1 and event["x_m"] >= network.junctions[1]
                    and 0 <= event["walking_time_s"] <= record["elapsed_s"] - STAND_SECONDS + 1e-6,
                    f"Invalid junction event for {key}")
        if hold is None:
            continue
        started, resumed = hold["started_s"], hold["resumed_s"]
        first, last = hold["samples"]
        require(started == STAND_SECONDS + events[0]["walking_time_s"]
                and 0 < first < last <= len(body)
                and first == int(started / SAMPLE_SECONDS + 1e-7) and
                last == (len(body) if resumed is None else int(resumed / SAMPLE_SECONDS + 1e-7)),
                f"Pause samples do not match junction callback for {key}")
        if resumed is not None:
            # The commanded duration can end between physics steps.
            require(-1e-9 <= resumed - started - duration <= 0.0021, f"Invalid pause duration for {key}")
        before, after = temperature[[first, last]]
        hottest = int(np.argmax(before))
        xy = body[first - 1:last, :2]
        require(np.allclose([hold["peak_before_c"], hold["peak_after_c"], hold["entry_motor_delta_c"],
                             hold["max_drift_m"]],
                            [before.max(), after.max(), after[hottest] - before[hottest],
                             np.linalg.norm(xy - xy[0], axis=1).max()], rtol=0, atol=1e-12)
                and hold["hottest_at_entry_joint"] == JOINT_NAMES[hottest], f"Pause measurements differ for {key}")
    return max_residual


def check_diagnostics(output, runs, diagnostics):
    prefix_lengths = {}
    for paused, zero in diagnostics:
        hold = runs[paused]["pause"]
        with np.load(output / runs[paused]["trace"]) as left, np.load(output / runs[zero]["trace"]) as right:
            first = hold["samples"][0] if hold is not None else len(left["torque_nm"])
            for field in TRACE_FIELDS:
                # Temperature has an initial sample in addition to interval end samples.
                count = first + (field == "temperature_c")
                paused_values, zero_values = left[field], right[field]
                require(np.array_equal(paused_values[:count], zero_values[:count]),
                        f"Trace prefix differs between {paused} and {zero} in {field}")
                if hold is None:
                    require(len(paused_values) == len(zero_values), f"Inactive pause changed trace length for {paused}")
        prefix_lengths[paused] = first
    return prefix_lengths


def pause_forecast_errors(plans, runs):
    errors = {}
    for row in plans:
        choice = row["methods"][METHODS[1]]
        if choice["selected"] is None or not choice["selected"]["pause_s"]:
            continue
        key = choice["execution"]
        predicted, observed = choice["selected"], runs[key]
        error = {
            "elapsed_s": predicted["predicted_elapsed_s"] - observed["elapsed_s"],
            "peak_c": predicted["predicted_peak_c"] - observed["peak_c"],
        }
        if observed["pause"] is not None:
            milestones, hold = predicted["predicted_pause"], observed["pause"]
            error["junction_entry_s"] = milestones["start_s"] - hold["started_s"]
            error["junction_entry_peak_c"] = milestones["entry_peak_c"] - hold["peak_before_c"]
            if hold["resumed_s"] is not None:
                error["pause_exit_peak_c"] = milestones["exit_peak_c"] - hold["peak_after_c"]
        errors[key] = error
    return errors


def audit(config, output, hold_model, protocol):
    manifest, networks, thermal, starts, walking = design(config)
    manifest = json.loads(json.dumps(manifest))
    expected_lock, hold_load = lock(config, hold_model, protocol, manifest)
    require(read(output / "evaluation_lock.json") == expected_lock, "Frozen evaluation lock changed")
    require(read(output / "manifest.json") == manifest, "Frozen nominal manifest changed")
    spec = manifest["study"]
    _, profiles, provenance = load_inputs(networks, spec, output, walking["goal_radius"])
    profile_files = {path.name for path in (output / "profiles").glob("*.npz")}
    require(provenance == read(output / "profile_checksums.json") and profile_files == set(provenance),
            "Nominal records, profile files or checksums differ")
    plans, runs = read(output / "plans.json"), read(output / "executions.json")
    require(len(plans) == expected_lock["expected_pairs"], "Pair count disagrees with the frozen protocol")
    jobs, diagnostics, forecasts = check_plans(plans, networks, thermal, starts, walking, profiles, spec, hold_load)
    thermal_residual = check_traces(output, runs, jobs, networks, thermal, starts, walking, spec)
    prefixes = check_diagnostics(output, runs, diagnostics)
    summary = summarize(plans, runs, spec)
    require(summary == read(output / "summary.json"), "Stored summary disagrees with the audited records")
    return {
        "audit_source_sha256": digest(Path(__file__)),
        "audited_sha256": {name: digest(output / name) for name in RESULT_FILES},
        "verified_start_pairs": len(plans),
        "verified_planning_decisions": len(plans) * len(METHODS),
        "verified_profile_outcomes": dict(Counter(record["outcome"] for record in provenance.values())),
        "verified_forecasts": forecasts,
        "verified_physics_replays": len(runs),
        "max_logged_thermal_update_residual_c": thermal_residual,
        "verified_same_route_prefix_samples": prefixes,
        "selected_pause_forecast_minus_observed": pause_forecast_errors(plans, runs),
        "outcomes": summary["outcomes"],
        "paired_comparison": summary["optional_pause_minus_governor"],
    }


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=CONFIG, output=OUTPUT)
    parser.add_argument("--hold-model", type=Path, default=HOLD_MODEL)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    args = parser.parse_args()
    report = audit(args.config, args.output, args.hold_model, args.protocol)
    write_json(args.output / "audit.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
