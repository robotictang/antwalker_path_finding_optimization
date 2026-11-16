"""Verify speed-study decisions and continuous mission traces."""

import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
from statistics import median

import numpy as np

from .audit_network import require
from .network_study import METHODS as BASELINES, write_json
from .route_speed_profiles import load_profiles_design, trace_name, validate_reference
from .route_speed_study import NEW_METHODS
from .walking import STAND_SECONDS


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(config, reference, output):
    spec, network_manifest, networks, settings, starts, walking = load_profiles_design(config)
    validate_reference(reference, network_manifest)
    lock = json.loads((output / "manifest.json").read_text())
    require(lock["study"] == spec, "Study configuration changed")
    require(lock["network_manifest"] == json.loads(json.dumps(network_manifest)), "Network source changed")
    require(lock["reference_manifest_sha256"] == digest(reference / "manifest.json"), "Reference manifest changed")
    require(lock["reference_decisions_sha256"] == digest(reference / "decisions.json"), "Reference decisions changed")
    package = Path(__file__).parent
    require(lock["planner_sha256"] == digest(package / "route_speed_study.py"), "Planner source changed")
    require(lock["profiler_sha256"] == digest(package / "route_speed_profiles.py"), "Profiler source changed")

    profiles = json.loads((output / "edge_profiles.json").read_text())
    rows = json.loads((output / "decisions.json").read_text())
    baseline_rows = json.loads((reference / "decisions.json").read_text())
    runs = json.loads((output / "executions.json").read_text())
    baseline_runs = json.loads((reference / "executions.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    methods = (*BASELINES, *NEW_METHODS)
    cases = list(product(networks, settings, starts))
    dt = network_manifest["sample_interval_s"]
    deadline = network_manifest["study"]["deadline_s"]
    fractions = spec["speed_fractions"]
    profile_count = 0
    for name, network in networks.items():
        for edges in network.edges.values():
            for edge, fraction in product(edges, fractions):
                filename = trace_name(name, edge, fraction)
                record = profiles[filename]
                with np.load(output / "profiles" / filename) as trace:
                    torque, body = trace["torque_nm"], trace["body_xyz_m"]
                    require(len(torque) == len(body) and np.isclose(len(torque) * dt, record["elapsed_s"]),
                            f"Invalid edge trace {filename}")
                    if record["completed"]:
                        section = network.sections[edge.stage]
                        require(np.linalg.norm(body[-1, :2] - [section.goal_x, 0]) <= walking["goal_radius"],
                                f"Profile missed its edge goal {filename}")
                if fraction == 1:
                    require(digest(output / "profiles" / filename) ==
                            digest(reference / "traces" / f"{name}_profile_{edge.name}.npz"),
                            f"Reused profile differs {filename}")
                profile_count += 1
    require(len(profiles) == profile_count, "Wrong profile count")
    require(rows[:len(baseline_rows)] == [
        row | {"execution_source": "reference" if row["execution"] else None} for row in baseline_rows
    ], "Baseline decisions were changed")
    index = {(row["map"], row["setting"], row["start"], row["method"]): row for row in rows}
    require(len(index) == len(rows) == len(cases) * len(methods), "Wrong decision count")
    used_runs = set()
    for name, setting, start in cases:
        network, thermal = networks[name], settings[setting]
        base_key = name, setting, start
        for method in NEW_METHODS:
            row = index[(*base_key, method)]
            execution = row["execution"]
            speed_fractions = row["speed_fractions"]
            if execution is None:
                require(not row["completed"] and row["failure"] == "no_route" and not speed_fractions,
                        f"Invalid rejection {base_key}/{method}")
                continue
            require(len(speed_fractions) == len(network.sections) and all(v in fractions for v in speed_fractions),
                    f"Invalid speeds {base_key}/{method}")
            require(row["predicted_time_s"] <= deadline and row["predicted_peak_c"] < thermal.limit_c,
                    f"Invalid admitted plan {base_key}/{method}")
            if method == NEW_METHODS[0]:
                require(row["route"] == index[(*base_key, "fastest_fixed_speed")]["route"],
                        f"Speed-only method switched routes {base_key}")
            if row["execution_source"] == "reference":
                require(all(v == 1 for v in speed_fractions), f"Reference trace used with nonnominal speeds {base_key}")
                require(any(row["route"] == index[(*base_key, fixed)]["route"] and
                            execution == index[(*base_key, fixed)]["execution"]
                            for fixed in ("fastest_fixed_speed", "per_motor_fixed_speed")),
                        f"Reference execution does not match the selected route {base_key}")
                result = baseline_runs[execution]
            else:
                require(row["execution_source"] == "continuous_replay", f"Unknown trace source {base_key}")
                result = runs[execution]
                used_runs.add(execution)
                with np.load(output / result["trace"]) as trace:
                    temp, body, torque, contacts = (
                        trace[field] for field in ("temperature_c", "body_xyz_m", "torque_nm", "foot_contacts")
                    )
                    require(len(temp) == len(body) + 1 == len(torque) + 1 == len(contacts) + 1,
                            f"Invalid trace lengths {execution}")
                    require(np.array_equal(temp[0], starts[start]) and np.isclose(temp.max(), result["peak_c"]),
                            f"Invalid temperature trace {execution}")
                    require(np.isclose(len(body) * dt, result["elapsed_s"]), f"Invalid trace duration {execution}")
                    if result["completed"]:
                        goal = [network.junctions[-1], 0]
                        require(np.linalg.norm(body[-1, :2] - goal) <= walking["goal_radius"]
                                and temp.max() < thermal.limit_c and result["elapsed_s"] <= deadline + 1e-6,
                                f"Invalid completion {execution}")
                        require(len(result["junction_events"]) == len(network.sections) - 1,
                                f"Missing junction crossings {execution}")
                    if result["failure"] == "thermal_limit":
                        require(temp[-1].max() >= thermal.limit_c, f"Invalid heat stop {execution}")
                    for number, event in enumerate(result["junction_events"], start=1):
                        require(event["target_fraction"] == speed_fractions[number] and
                                event["x_m"] >= network.junctions[number] and
                                event["walking_time_s"] + STAND_SECONDS <= result["elapsed_s"] + dt,
                                f"Invalid speed change {execution}")
            require(row["completed"] == result["completed"] and row["failure"] == result["failure"],
                    f"Decision does not match replay {execution}")
    require(set(runs) == used_runs and len(runs) == summary["new_physics_replays"], "Wrong replay count")
    by_setting = {}
    for method in methods:
        outcomes = Counter(index[(*case, method)]["failure"] or "completed" for case in cases)
        require(summary["by_method"][method] == {"scheduled": len(cases), "outcomes": dict(outcomes)},
                f"Invalid summary {method}")
    for setting in settings:
        by_setting[setting] = {method: sum(index[(name, setting, start, method)]["completed"]
                                           for name, start in product(networks, starts)) for method in methods}
    comparisons = {}
    for method in NEW_METHODS:
        for reference_method in ("per_motor_fixed_speed", "fastest_reactive_slowdown", NEW_METHODS[0]):
            if method == reference_method:
                continue
            first, second = ([index[(*case, key)] for case in cases] for key in (method, reference_method))
            first_only = [a for a, b in zip(first, second, strict=True) if a["completed"] and not b["completed"]]
            second_only = [b for a, b in zip(first, second, strict=True) if b["completed"] and not a["completed"]]
            comparisons[f"{method}__vs__{reference_method}"] = {
                "first_only": first_only, "second_only": second_only,
            }
    speed_plans = {}
    for method in NEW_METHODS:
        selected = [index[(*case, method)] for case in cases]
        used_slow = [row for row in selected if any(fraction < 1 for fraction in row["speed_fractions"])]
        slowed_times = [runs[row["execution"]]["elapsed_s"] for row in used_slow if row["completed"]]
        speed_plans[method] = {
            "plans_using_lower_speed": len(used_slow),
            "completions_using_lower_speed": len(slowed_times),
            "median_lower_speed_completion_s": median(slowed_times) if slowed_times else None,
        }
    return {"profiles_checked": profile_count, "decisions_checked": len(rows), "new_missions_checked": len(runs),
            "completion_by_setting": by_setting, "speed_plans": speed_plans, "paired": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/route_speed_study.json"))
    parser.add_argument("--reference", type=Path, default=Path("results/network_study"))
    parser.add_argument("--output", type=Path, default=Path("results/route_speed_study"))
    args = parser.parse_args()
    report = audit(args.config, args.reference, args.output)
    write_json(args.output / "audit.json", report)
    print(f"Verified {report['profiles_checked']} profiles, {report['decisions_checked']} decisions and "
          f"{report['new_missions_checked']} new physics traces.")


if __name__ == "__main__":
    main()
