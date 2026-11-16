"""Check benchmark artifacts and count actual branch reversals."""

import argparse
import csv
import json
from collections import Counter
from itertools import product
from pathlib import Path

import numpy as np

from .benchmark import ROUTES, load_design
from .pilot import METHODS


def audit(config_path, output):
    expected_manifest, maps, walking, settings, starts = load_design(config_path)
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest != json.loads(json.dumps(expected_manifest)):
        raise ValueError("Saved manifest differs from the source and configuration")
    executions = json.loads((output / "executions.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    with (output / "decisions.csv").open(newline="") as file:
        decisions = list(csv.DictReader(file))

    def case(row):
        return (row["map"], float(row["heating_rate_multiplier"]),
                float(row["cooling_time_constant_s"]), row["start"])

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    cases = [(name, heat, tau, start) for name, (heat, tau), start in product(maps, settings, starts)]
    by_route = {(*case(row), row["route"]): row for row in executions}
    by_method = {(*case(row), row["method"]): row for row in decisions}
    require(len(by_route) == len(executions) == len(cases) * len(ROUTES), "Wrong route record count")
    require(len(by_method) == len(decisions) == len(cases) * len(METHODS), "Wrong method record count")

    for key in cases:
        _, heat, tau, start = key
        thermal = settings[heat, tau]
        for route in ROUTES:
            row = by_route[(*key, route)]
            with np.load(output / row["trace"]) as trace:
                torque, body, contact, temp = (trace[field] for field in
                                               ("torque_nm", "body_xyz_m", "foot_contacts", "temperature_c"))
                require(len(torque) == len(body) == len(contact) == len(temp) - 1,
                        f"Trace lengths disagree for {key}/{route}")
                require(np.array_equal(temp[0], starts[start]), f"Incorrect start temperatures for {key}/{route}")
                require(np.isclose(temp.max(), row["peak_c"]), f"Peak temperature mismatch for {key}/{route}")
                require(np.isclose(len(torque) * manifest["sample_interval_s"], row["elapsed_s"]),
                        f"Trace duration mismatch for {key}/{route}")
                if row["completed"]:
                    options = maps[key[0]]
                    goal_x = 2 * options["turn_length_m"] + options["bank_length_m"] + 1
                    require(np.linalg.norm(body[-1, :2] - [goal_x, 0]) <= walking["goal_radius"],
                            f"Completed without reaching goal for {key}/{route}")
                    require(temp.max() < thermal.limit_c and row["failure"] is None,
                            f"Completed above the thermal limit for {key}/{route}")
                if row["failure"] == "thermal_limit":
                    require(temp[-1].max() >= thermal.limit_c, f"Thermal stop below the limit for {key}/{route}")
                if row["execution"] == "nominal_physics_reused":
                    require(temp.max() <= thermal.derate_start_c, f"Derating in reused trace for {key}/{route}")

    for method in METHODS:
        counts = Counter()
        for key in cases:
            row = by_method[(*key, method)]
            route = row["selected_route"]
            expected = by_route[(*key, route)] if route else None
            completed = row["completed"] == "True"
            require(completed == bool(expected and expected["completed"]), f"Decision mismatch for {key}/{method}")
            counts["completed"] += completed
            counts["no_route"] += not route
            counts["selected_route_failed"] += bool(route) and not completed
        require(summary["per_method"][method] == {"scheduled": len(cases), **counts},
                f"Aggregate counts differ for {method}")

    by_setting = []
    for heat, tau in settings:
        counts = Counter(maps=len(maps), actual_finishable_route_switches=0, successful_per_motor_switches=0,
                         planner_matches_both_finishable_routes=0, starts_with_a_finishable_route=0)
        for name in maps:
            finishable = [{route for route in ROUTES if by_route[name, heat, tau, start, route]["completed"]}
                          for start in starts]
            counts["starts_with_a_finishable_route"] += sum(bool(routes) for routes in finishable)
            unique_switch = all(len(routes) == 1 for routes in finishable) and finishable[0] != finishable[1]
            choices = [by_method[name, heat, tau, start, "per_joint"]["selected_route"] for start in starts]
            choices_complete = all(choice in routes for choice, routes in zip(choices, finishable, strict=True))
            counts["actual_finishable_route_switches"] += unique_switch
            counts["successful_per_motor_switches"] += choices_complete and choices[0] != choices[1]
            counts["planner_matches_both_finishable_routes"] += unique_switch and choices_complete
        by_setting.append({"heating_rate_multiplier": heat, "cooling_time_constant_s": tau, **counts})
    return {
        "warm_route_traces_checked": len(executions),
        "decisions_checked": len(decisions),
        "route_outcomes": dict(Counter(row["failure"] or "completed" for row in executions)),
        "switch_diagnostics_by_setting": by_setting,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/asymmetric_benchmark.json"))
    parser.add_argument("--output", type=Path, default=Path("results/asymmetric_benchmark"))
    args = parser.parse_args()
    diagnostics = audit(args.config, args.output)
    (args.output / "audit.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(f"Verified {diagnostics['warm_route_traces_checked']} warm traces and "
          f"{diagnostics['decisions_checked']} decisions.")


if __name__ == "__main__":
    main()
