"""Verify the mission traces and evaluate the prespecified completion criterion."""

from collections import Counter
from itertools import product
import json
from statistics import median

import numpy as np

from .audit_network import require
from .mission_completion import METHODS
from .mission_profiles import arguments, design
from .network_study import write_json
from .route_speed_profiles import trace_name


def paired_result(map_pairs, seed):
    effects = np.asarray([100 * (sum(right) - sum(left)) / len(left) for left, right in map_pairs])
    samples = np.random.default_rng(seed).choice(effects, size=(20000, len(effects)))
    return {"mean_gain_pp": float(effects.mean()),
            "descriptive_map_bootstrap_95_pp": np.quantile(samples.mean(axis=1), [.025, .975]).tolist(),
            "per_motor_only": sum(b and not a for left, right in map_pairs for a, b in zip(left, right, strict=True)),
            "anonymous_only": sum(a and not b for left, right in map_pairs for a, b in zip(left, right, strict=True))}


def audit(config, output):
    lock, networks, thermal, starts, walking = design(config)
    require(json.loads((output / "manifest.json").read_text()) == json.loads(json.dumps(lock)),
            "Frozen manifest mismatch")
    spec = lock["study"]
    maps = {item["id"]: item for item in spec["maps"]}
    dt = lock["sample_interval_s"]
    records = json.loads((output / "edge_profiles.json").read_text())
    checked_profiles = 0
    for name, network in networks.items():
        for stage in network.edges.values():
            for edge, fraction in product(stage, spec["speed_fractions"]):
                trace = trace_name(name, edge, fraction)
                record = records[trace]
                with np.load(output / "profiles" / trace) as data:
                    xyz = data["body_xyz_m"]
                    require(len(xyz) == len(data["torque_nm"]) and np.isclose(len(xyz) * dt, record["elapsed_s"]),
                            f"Malformed profile {trace}")
                    if record["completed"]:
                        length = network.junctions[edge.stage + 1] - network.junctions[edge.stage]
                        require(np.linalg.norm(xyz[-1, :2] - [length, 0]) <= walking["goal_radius"],
                                f"Profile missed its goal {trace}")
                checked_profiles += 1
    require(checked_profiles == len(records), "Unexpected branch profile")
    plans = json.loads((output / "plans.json").read_text())
    runs = json.loads((output / "executions.json").read_text())
    cases = [(name, setting, start) for name, setting in product(networks, thermal) for start in starts[setting]]
    index = {(p["map"], p["setting"], p["start"], p["method"]): p for p in plans}
    require(len(plans) == len(index) and set(index) == {(*case, method) for case, method in product(cases, METHODS)},
            "Incomplete paired decisions")
    for name, setting in product(networks, thermal):
        baseline = [index[name, setting, start, METHODS[0]] for start in starts[setting]]
        require(all(baseline[0][field] == baseline[1][field] for field in
                    ("route", "speed_fractions", "predicted_peak_c", "planning_failure")),
                "Anonymous planner leaked motor identities")
    replay_cases = {}
    for plan in plans:
        key = plan["execution"]
        if not key:
            require(plan["planning_failure"] in ("no_route", "planning_timeout") and not plan["route"],
                    "Missing execution without a planning failure")
            continue
        name, setting = plan["map"], plan["setting"]
        require(plan["planning_failure"] is None and plan["planning_s"] < spec["planning_budget_s"]
                and plan["predicted_peak_c"] < thermal[setting].limit_c - spec["thermal_margin_c"]
                and plan["predicted_elapsed_s"] <= maps[name]["deadline_s"], "Invalid admitted plan")
        identity = (name, setting, plan["start"], tuple(plan["route"]), tuple(plan["speed_fractions"]))
        require(replay_cases.setdefault(key, identity) == identity, "Execution shared across different plans")
    require(set(replay_cases) == set(runs), "Missing or extra physics runs")
    for key, (name, setting, start, route, speeds) in replay_cases.items():
        result = runs[key]
        network = networks[name]
        require(len(route) == len(speeds) == len(network.sections), f"Invalid route {key}")
        with np.load(output / result["trace"]) as trace:
            temp, body = trace["temperature_c"], trace["body_xyz_m"]
            require(len(temp) == len(body) + 1 == len(trace["torque_nm"]) + 1
                    and np.array_equal(temp[0], starts[setting][start])
                    and np.isclose(temp.max(), result["peak_c"])
                    and np.isclose(len(body) * dt, result["elapsed_s"]), f"Invalid trace {key}")
            if result["completed"]:
                require(np.linalg.norm(body[-1, :2] - [network.junctions[-1], 0]) <= walking["goal_radius"]
                        and temp.max() < thermal[setting].limit_c and result["elapsed_s"] <= maps[name]["deadline_s"] + 1e-6
                        and len(result["junction_events"]) == len(network.sections) - 1, f"Invalid completion {key}")
            if result["failure"] == "thermal_limit":
                require(temp[-1].max() >= thermal[setting].limit_c, f"Invalid thermal stop {key}")

    def outcome(plan):
        return (runs[plan["execution"]]["failure"] or "completed") if plan["execution"] else plan["planning_failure"]

    by_method = {}
    for method in METHODS:
        subset = [index[(*case, method)] for case in cases]
        by_method[method] = {
            "outcomes": dict(Counter(outcome(plan) for plan in subset)),
            "median_planning_s": median(plan["planning_s"] for plan in subset),
            "maximum_planning_s": max(plan["planning_s"] for plan in subset),
            "reactive_slowdown_triggered": sum(bool(runs[p["execution"]]["slowdown_events"])
                                               for p in subset if p["execution"]),
        }
    by_map = {name: [[outcome(index[(*case, method)]) == "completed" for case in cases if case[0] == name]
                     for method in METHODS] for name in networks}
    comparisons = paired_result(list(by_map.values()), spec["bootstrap_seed"])
    comparisons["meets_minimum_gain"] = comparisons["mean_gain_pp"] >= spec["minimum_gain_pp"]
    comparisons["interval_excludes_zero"] = comparisons["descriptive_map_bootstrap_95_pp"][0] > 0
    return {
        "paired_starts": len(cases), "decisions_checked": len(plans), "continuous_replays_checked": len(runs),
        "profiles_checked": checked_profiles, "profile_outcomes": dict(Counter(
            record["failure"] or "completed" for record in records.values()
        )),
        "by_method": by_method,
        "completed_by_map": {name: dict(zip(METHODS, map(sum, pairs), strict=True)) for name, pairs in by_map.items()},
        "primary_comparison": comparisons,
    }


def main():
    args = arguments(__doc__).parse_args()
    report = audit(args.config, args.output)
    write_json(args.output / "summary.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
