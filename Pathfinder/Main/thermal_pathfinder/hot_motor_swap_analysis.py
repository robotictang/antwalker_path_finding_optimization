"""Summarize exhaustive warm-route replays and paired information comparisons."""

from collections import Counter
from itertools import product
from math import prod

from .mission_analysis import paired_result

SIDES = ("left_warm", "right_warm")
METHODS = ("aggregate", "per_motor")


def outcome(execution, runs):
    if execution is None:
        return "no_route"
    run = runs[execution]
    return "completed" if run["completed"] else run["failure"]


def describe_case(case, runs):
    routes = {tuple(row["route"]): row for row in case["routes"]}
    finishable = {
        side: {route for route, row in routes.items() if runs[row["starts"][side]["execution"]]["completed"]}
        for side in SIDES
    }
    left, right = (finishable[side] for side in SIDES)
    if left and right:
        classification = "overlapping" if left & right else "nonempty_disjoint"
    else:
        classification = "one_empty" if left or right else "both_empty"
    thermal_routes = {
        side: [route for route in sorted(finishable[side])
               if outcome(routes[route]["starts"][other]["execution"], runs) == "thermal_limit"]
        for side, other in (SIDES, SIDES[::-1])
    }
    witnesses = [
        {"left_warm_finish_right_warm_thermal": list(left_route),
         "right_warm_finish_left_warm_thermal": list(right_route)}
        for left_route, right_route in product(thermal_routes[SIDES[0]], thermal_routes[SIDES[1]])
    ]
    route_by_execution = {
        row["starts"][side]["execution"]: route for route, row in routes.items() for side in SIDES
    }
    selections = {}
    for method in METHODS:
        chosen = {}
        for side in SIDES:
            key = case["selections"][side][method]
            chosen[side] = {
                "execution": key,
                "route": list(route_by_execution[key]) if key is not None else None,
                "outcome": outcome(key, runs),
            }
        left_choice, right_choice = (chosen[side]["route"] for side in SIDES)
        selections[method] = {
            "starts": chosen,
            "switched_route": left_choice is not None and right_choice is not None and left_choice != right_choice,
            "both_completed": all(chosen[side]["outcome"] == "completed" for side in SIDES),
        }
    matrix = []
    for route, row in sorted(routes.items()):
        starts = {}
        for side in SIDES:
            prediction = row["starts"][side]
            key = prediction["execution"]
            replay = runs[key]
            starts[side] = prediction | {
                "outcome": outcome(key, runs), "observed_peak_c": replay["peak_c"],
                "observed_elapsed_s": replay["elapsed_s"],
            }
        matrix.append({"route": list(route), "starts": starts, "aggregate": row["aggregate"]})
    return {
        "map": case["map"], "family": case["family"], "setting": case["setting"],
        "supported_routes": [list(route) for route in sorted(routes)],
        "finishable_routes": {side: [list(route) for route in sorted(finishable[side])] for side in SIDES},
        "common_finishable_routes": [list(route) for route in sorted(left & right)],
        "classification": classification,
        "necessary_route_change": bool(left and right and not left & right),
        "unique_safe_route_swap": len(left) == len(right) == 1 and left != right,
        "thermal_crossover": bool(witnesses), "thermal_crossover_witnesses": witnesses,
        "hindsight_individual_finishes": int(bool(left)) + int(bool(right)),
        "hindsight_shared_route_finishes": max(
            (int(route in left) + int(route in right) for route in routes), default=0),
        "selections": selections, "route_outcomes": matrix,
    }


def aggregate_cases(cases):
    counts = Counter(case["classification"] for case in cases)
    reversals = {}
    for field in ("necessary_route_change", "unique_safe_route_swap", "thermal_crossover"):
        selected = [case for case in cases if case[field]]
        reversals[field] = {
            "pairs": len(selected), "courses": len({case["map"] for case in selected}),
            "fraction_of_all_pairs": len(selected) / len(cases) if cases else None,
            "occurs_on_multiple_courses": len({case["map"] for case in selected}) > 1,
        }
    best_individual = sum(case["hindsight_individual_finishes"] for case in cases)
    best_shared = sum(case["hindsight_shared_route_finishes"] for case in cases)
    methods = {}
    for method in METHODS:
        decisions = [(case, side, case["selections"][method]["starts"][side])
                     for case in cases for side in SIDES]
        outcomes = Counter(choice["outcome"] for _, _, choice in decisions)
        completed = outcomes["completed"]
        missed_feasible = [(case, side, choice) for case, side, choice in decisions
                           if case["finishable_routes"][side] and choice["outcome"] != "completed"]
        conditional = Counter(choice["outcome"] for case, side, choice in decisions
                              if case["finishable_routes"][side])
        methods[method] = {
            "starts": len(decisions), "outcomes": dict(outcomes),
            "completed": completed, "thermal_stops": outcomes["thermal_limit"],
            "rejections": outcomes["no_route"],
            "other_execution_failures": sum(count for label, count in outcomes.items()
                                            if label not in ("completed", "thermal_limit", "no_route")),
            "completion_rate": completed / len(decisions) if decisions else None,
            "hindsight_completion_gap": best_individual - completed,
            "finishable_starts": best_individual,
            "outcomes_on_finishable_starts": dict(conditional),
            "completion_rate_on_finishable_starts": completed / best_individual if best_individual else None,
            "finishable_starts_rejected": sum(choice["outcome"] == "no_route" for _, _, choice in missed_feasible),
            "finishable_starts_selected_failure": sum(choice["outcome"] != "no_route"
                                                      for _, _, choice in missed_feasible),
            "route_switch_pairs": sum(case["selections"][method]["switched_route"] for case in cases),
            "both_completed_pairs": sum(case["selections"][method]["both_completed"] for case in cases),
        }
    gains, losses = [], []
    for case in cases:
        for side in SIDES:
            before, after = (case["selections"][method]["starts"][side] for method in METHODS)
            if (before["outcome"] == "completed") != (after["outcome"] == "completed"):
                change = {
                    "map": case["map"], "family": case["family"], "setting": case["setting"], "start": side,
                    "aggregate": before, "per_motor": after,
                }
                (gains if after["outcome"] == "completed" else losses).append(change)
    return {
        "course_setting_pairs": len(cases), "starting_scenarios": 2 * len(cases),
        "classifications": {label: counts[label] for label in (
            "both_empty", "one_empty", "overlapping", "nonempty_disjoint")},
        "reversals": reversals,
        "hindsight": {
            "individual_route_completion_count": best_individual,
            "one_shared_route_per_pair_completion_count": best_shared,
            "value_of_assignment_specific_route_choices": best_individual - best_shared,
        },
        "planners": methods, "per_motor_only": gains, "aggregate_only": losses,
        "net_added_finishes": len(gains) - len(losses),
        "additional_thermal_stops": methods["per_motor"]["thermal_stops"] - methods["aggregate"]["thermal_stops"],
    }


def route_coverage(cases, spec):
    expected = {row["id"]: prod(len(stage["offsets_m"]) for stage in row["stages"]) for row in spec["maps"]}
    by_course = {}
    for name, count in expected.items():
        matching = [case for case in cases if case["map"] == name]
        supported = [len(case["supported_routes"]) for case in matching]
        by_course[name] = {
            "expected_geometric_routes": count,
            "supported_routes_by_setting": {case["setting"]: len(case["supported_routes"]) for case in matching},
            "all_geometric_routes_supported": bool(matching) and all(value == count for value in supported),
        }
    expected_pairs = sum(expected[case["map"]] for case in cases)
    observed_pairs = sum(len(case["supported_routes"]) for case in cases)
    return {
        "expected_route_setting_pairs": expected_pairs, "supported_route_setting_pairs": observed_pairs,
        "missing_route_setting_pairs": expected_pairs - observed_pairs,
        "expected_warm_route_outcomes": 2 * expected_pairs,
        "observed_warm_route_outcomes": 2 * observed_pairs,
        "all_geometric_routes_supported": all(item["all_geometric_routes_supported"] for item in by_course.values()),
        "by_course": by_course,
    }


def summarize(cases, runs, spec):
    """Report physical route reversals and paired planner outcomes on every start."""
    records = [describe_case(case, runs) for case in cases]
    report = aggregate_cases(records)
    by_course = {row["id"]: [case for case in records if case["map"] == row["id"]] for row in spec["maps"]}
    pairs = [
        tuple([case["selections"][method]["starts"][side]["outcome"] == "completed"
               for case in group for side in SIDES] for method in METHODS)
        for group in by_course.values() if group
    ]
    comparison = paired_result(pairs, spec["bootstrap_seed"])
    comparison["aggregate_only"] = comparison.pop("anonymous_only")
    comparison["additional_thermal_stops"] = report["additional_thermal_stops"]
    comparison["minimum_gain_pp"] = spec["minimum_gain_pp"]
    comparison["meets_minimum_gain"] = comparison["mean_gain_pp"] >= spec["minimum_gain_pp"]
    comparison["meets_no_additional_thermal_stops"] = report["additional_thermal_stops"] <= 0
    comparison["meets_practical_benchmark"] = (
        comparison["meets_minimum_gain"] and comparison["meets_no_additional_thermal_stops"])
    route_outcomes = Counter(start["outcome"] for case in records
                             for row in case["route_outcomes"] for start in row["starts"].values())
    necessary = [case for case in records if case["necessary_route_change"]]
    return report | {
        "physics_replays": len(runs), "exhaustive_route_outcomes": dict(route_outcomes),
        "route_coverage": route_coverage(records, spec), "per_motor_minus_aggregate": comparison,
        "conditional_on_necessary_route_change": aggregate_cases(necessary),
        "by_course": {name: aggregate_cases(group) for name, group in by_course.items()},
        "by_family": {name: aggregate_cases([case for case in records if case["family"] == name])
                      for name in sorted({case["family"] for case in records})},
        "by_thermal_setting": {name: aggregate_cases([case for case in records if case["setting"] == name])
                               for name in sorted({case["setting"] for case in records})},
        "cases": records,
    }
