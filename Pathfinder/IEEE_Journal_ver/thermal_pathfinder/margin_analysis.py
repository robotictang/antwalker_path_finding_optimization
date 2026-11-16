"""Audit thermal margin experiments and quantify the admission trade-off."""

from collections import Counter
from itertools import product
import json

import numpy as np

from .audit_network import require
from .margin_profiles import METHODS
from .margin_study import arguments, verified_design
from .network_study import write_json
from .walking import STAND_SECONDS


def admitted(plan, margin):
    peak = plan["predicted_peak_c"]
    return peak is not None and peak < plan["thermal_limit_c"] - margin


def margin_counts(plans, runs, margin):
    counts = Counter(scheduled=0, admitted=0, completed=0, thermal_stops=0,
                     other_failures=0, finishable_plans_rejected=0)
    for plan in plans:
        result = runs.get(plan["execution"])
        counts["scheduled"] += 1
        if admitted(plan, margin):
            counts["admitted"] += 1
            counts["completed"] += result["completed"]
            counts["thermal_stops"] += result["failure"] == "thermal_limit"
            counts["other_failures"] += not result["completed"] and result["failure"] != "thermal_limit"
        elif result and result["completed"]:
            counts["finishable_plans_rejected"] += 1
    return dict(counts)


def evaluate(config, development, reference, output):
    lock, networks, settings, starts, walking = verified_design(config, development, reference, output)
    spec = lock["study"]
    plans = json.loads((output / "plans.json").read_text())
    runs = json.loads((output / "executions.json").read_text())
    keyed = {(plan["map"], plan["setting"], plan["start"], plan["method"]): plan for plan in plans}
    require(len(plans) == len(keyed) and set(keyed) == set(product(networks, settings, starts, METHODS)),
            "Missing, repeated or unknown planning case")
    require(set(runs) == {plan["execution"] for plan in plans if plan["execution"]}, "Missing or unknown mission")
    dt = lock["sample_interval_s"]
    by_execution = {}
    for plan in plans:
        key = plan["execution"]
        require(bool(key) == admitted(plan, 0), "Invalid zero-margin plan")
        if not key:
            continue
        previous = by_execution.setdefault(key, plan)
        require(all(previous[field] == plan[field] for field in (
            "map", "setting", "start", "route", "speed_fractions", "predicted_peak_c"
        )), "Reused mission has inconsistent inputs")
        require(plan["predicted_elapsed_s"] <= spec["deadline_s"], "Predicted deadline violation")

    errors = []
    for key, plan in by_execution.items():
        result = runs[key]
        network = networks[plan["map"]]
        limit = settings[plan["setting"]].limit_c
        require(plan["thermal_limit_c"] == limit, f"Wrong thermal limit {key}")
        with np.load(output / result["trace"]) as trace:
            temp, body, torque, contact = (trace[k] for k in
                                           ("temperature_c", "body_xyz_m", "torque_nm", "foot_contacts"))
            require(len(temp) == len(body) + 1 == len(torque) + 1 == len(contact) + 1, f"Trace length {key}")
            require(np.array_equal(temp[0], starts[plan["start"]]) and np.isclose(temp.max(), result["peak_c"]),
                    f"Trace temperature {key}")
            require(np.isclose(len(body) * dt, result["elapsed_s"]), f"Trace time {key}")
            if result["completed"]:
                require(np.linalg.norm(body[-1, :2] - [network.junctions[-1], 0]) <= walking["goal_radius"]
                        and temp.max() < limit and result["elapsed_s"] <= spec["deadline_s"] + 1e-6
                        and len(result["junction_events"]) == len(network.sections) - 1, f"Invalid finish {key}")
            if result["failure"] == "thermal_limit":
                require(temp[-1].max() >= limit, f"Invalid thermal stop {key}")
            for number, event in enumerate(result["junction_events"], start=1):
                require(event["target_fraction"] == plan["speed_fractions"][number]
                        and event["x_m"] >= network.junctions[number]
                        and event["walking_time_s"] + STAND_SECONDS <= result["elapsed_s"] + dt,
                        f"Invalid junction transition {key}")
        errors.append({
            "execution": key, "map": plan["map"], "setting": plan["setting"], "start": plan["start"],
            "predicted_peak_c": plan["predicted_peak_c"], "observed_peak_c": result["peak_c"],
            "observed_minus_predicted_c": result["peak_c"] - plan["predicted_peak_c"],
            "predicted_headroom_c": limit - plan["predicted_peak_c"], "failure": result["failure"],
        })
    scenarios = {method: [plan for plan in plans if plan["method"] == method] for method in METHODS}
    scenarios["all_policies"] = plans
    sweep = {}
    for name, selected in scenarios.items():
        grid = [{"margin_c": margin, **margin_counts(selected, runs, margin)} for margin in spec["margin_grid_c"]]
        viable = [row["margin_c"] for row in grid if row["thermal_stops"] == 0 and row["completed"] > 0]
        sweep[name] = {"smallest_tested_margin_with_no_heat_stops_and_a_completion_c": min(viable, default=None),
                       "grid": grid}
    distinct = Counter(result["failure"] or "completed" for result in runs.values())
    return {
        "calibration": lock["calibration"], "decision_cases_checked": len(plans), "unique_traces_checked": len(runs),
        "unique_outcomes": dict(distinct), "peak_errors": sorted(errors, key=lambda row: -row["observed_minus_predicted_c"]),
        "margin_sweep": sweep,
    }


def main():
    args = arguments(__doc__).parse_args()
    result = evaluate(args.config, args.development, args.reference, args.output)
    write_json(args.output / "summary.json", result)
    print(json.dumps(result["margin_sweep"], indent=2))


if __name__ == "__main__":
    main()
