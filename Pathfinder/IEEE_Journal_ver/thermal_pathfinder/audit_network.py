"""Check the network experiment and summarize its paired outcomes."""

import argparse
from collections import Counter
import json
from itertools import product
from pathlib import Path
from statistics import median

import numpy as np

from .network import RouteNetwork
from .network_study import METHODS, load_design, write_json
from .walking import STAND_SECONDS


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(config, output):
    manifest, maps, settings, starts, walking = load_design(config)
    saved = json.loads((output / "manifest.json").read_text())
    require(json.loads(json.dumps(manifest)) == saved, "Manifest differs from current source or configuration")
    spec = manifest["study"]
    profiles = json.loads((output / "edge_profiles.json").read_text())
    executions = json.loads((output / "executions.json").read_text())
    rows = json.loads((output / "decisions.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    networks = {key: RouteNetwork(stages, spec["resolution_m"]) for key, stages in maps.items()}
    unique = {}

    def case(row):
        return row["map"], row["setting"], row["start"]

    cases = list(product(maps, settings, starts))
    decisions = {(*case(row), row["method"]): row for row in rows}
    require(len(rows) == len(decisions) == len(cases) * len(METHODS), "Wrong decision count")
    for name, network in networks.items():
        edge_names = {edge.name for edges in network.edges.values() for edge in edges}
        require(set(profiles[name]) == edge_names, f"Wrong edge profile count for {name}")
        for edge in edge_names:
            with np.load(output / "traces" / f"{name}_profile_{edge}.npz") as trace:
                require(len(trace["torque_nm"]) == len(trace["body_xyz_m"]), f"Invalid nominal trace {name}/{edge}")

    for key in cases:
        for method, (aware, slow) in METHODS.items():
            row = decisions[(*key, method)]
            execution_id = row["execution"]
            if execution_id is None:
                require(row["failure"] == "no_route" and not row["completed"] and row["route"] is None,
                        f"Invalid rejection {key}/{method}")
                continue
            result = executions[execution_id]
            require(row["completed"] == result["completed"] and row["failure"] == result["failure"],
                    f"Execution outcome mismatch {key}/{method}")
            label = (*key, row["route"], slow)
            require(unique.setdefault(execution_id, label) == label, f"Inconsistent execution {execution_id}")
            if aware:
                require(row["predicted_peak_c"] < settings[key[1]].limit_c and
                        len(row["predicted_junction_temperatures_c"]) == len(networks[key[0]].sections),
                        f"Invalid thermal plan {key}/{method}")
        for first, second in (("fastest_fixed_speed", "fastest_reactive_slowdown"),
                              ("per_motor_fixed_speed", "per_motor_with_slowdown")):
            require(decisions[(*key, first)]["route"] == decisions[(*key, second)]["route"],
                    f"Slowdown pair changed planned route for {key}")
    require(set(unique) == set(executions), "Execution list does not match scheduled missions")

    per_execution = {}
    dt = manifest["sample_interval_s"]
    for execution_id, (name, setting, start, route, slow) in unique.items():
        result = executions[execution_id]
        thermal = settings[setting]
        with np.load(output / result["trace"]) as trace:
            torque, xyz, contacts, temp, centerline = (trace[key] for key in
                ("torque_nm", "body_xyz_m", "foot_contacts", "temperature_c", "centerline_xy_m"))
            require(len(torque) == len(xyz) == len(contacts) == len(temp) - 1,
                    f"Trace lengths disagree {execution_id}")
            require(np.array_equal(temp[0], starts[start]), f"Starting temperature mismatch {execution_id}")
            require(np.isclose(temp.max(), result["peak_c"]), f"Peak mismatch {execution_id}")
            require(np.isclose(len(torque) * dt, result["elapsed_s"]), f"Duration mismatch {execution_id}")
            goal = np.array([networks[name].junctions[-1], 0.0])
            require(centerline[-1, 0] > goal[0], f"Route does not span network {execution_id}")
            if result["completed"]:
                require(np.linalg.norm(xyz[-1, :2] - goal) <= walking["goal_radius"]
                        and temp.max() < thermal.limit_c and result["elapsed_s"] <= spec["deadline_s"] + 1e-6,
                        f"Invalid completion {execution_id}")
            if result["failure"] == "thermal_limit":
                require(temp[-1].max() >= thermal.limit_c, f"Invalid thermal stop {execution_id}")
            events = result["slowdown_events"]
            require(slow or (not events and result["slow_seconds"] == 0), f"Unexpected slowdown {execution_id}")
            for event in events:
                active = event["slowdown_active"]
                threshold = spec["slowdown"]["trigger_c" if active else "resume_c"]
                require(event["hottest_c"] >= threshold if active else event["hottest_c"] <= threshold,
                        f"Invalid slowdown trigger {execution_id}")
                sample = int((event["walking_time_s"] + STAND_SECONDS + 1e-7) / dt)
                require(np.isclose(temp[sample].max(), event["hottest_c"], atol=0.01),
                        f"Slowdown event does not match the recorded temperature {execution_id}")
            per_execution[execution_id] = float(xyz[:, 0].max())

    by_setting = {
        setting: {method: sum(decisions[name, setting, start, method]["completed"]
                              for name, start in product(maps, starts)) for method in METHODS}
        for setting in settings
    }
    by_map = {
        name: {method: sum(decisions[name, setting, start, method]["completed"]
                           for setting, start in product(settings, starts)) for method in METHODS}
        for name in maps
    }
    paired = {}
    comparisons = (
        ("per_motor_fixed_speed", "fastest_reactive_slowdown"),
        ("fastest_reactive_slowdown", "fastest_fixed_speed"),
        ("per_motor_with_slowdown", "per_motor_fixed_speed"),
        ("per_motor_with_slowdown", "fastest_reactive_slowdown"),
    )
    for first, second in comparisons:
        left = [decisions[(*key, first)] for key in cases]
        right = [decisions[(*key, second)] for key in cases]
        both = [(executions[a["execution"]], executions[b["execution"]])
                for a, b in zip(left, right, strict=True) if a["completed"] and b["completed"]]
        paired[f"{first}__vs__{second}"] = {
            "first_only": sum(a["completed"] and not b["completed"] for a, b in zip(left, right, strict=True)),
            "second_only": sum(b["completed"] and not a["completed"] for a, b in zip(left, right, strict=True)),
            "both_completed": len(both),
            "median_elapsed_difference_s": median(a["elapsed_s"] - b["elapsed_s"] for a, b in both) if both else None,
        }
    activation = {}
    for method in METHODS:
        subset = [decisions[(*key, method)] for key in cases]
        totals = Counter(row["failure"] or "completed" for row in subset)
        require(summary["by_method"][method] == {"scheduled": len(subset), "outcomes": dict(totals)},
                f"Wrong summary counts for {method}")
        active = [executions[row["execution"]] for row in subset if row["execution"]
                  and executions[row["execution"]]["slowdown_events"]]
        activation[method] = {"slowdown_activated": len(active),
                              "completed_after_activation": sum(run["completed"] for run in active),
                              "median_seconds_below_nominal": median(run["slow_seconds"] for run in active) if active else None}
    require(summary["unique_missions"] == len(executions), "Wrong number of distinct missions")
    return {"decisions_checked": len(rows), "missions_checked": len(executions),
            "nominal_edges_completed": sum(edge["completed"] for edges in profiles.values() for edge in edges.values()),
            "completion_by_setting": by_setting, "completion_by_map": by_map,
            "paired": paired, "slowdown": activation,
            "maximum_x_by_execution_m": per_execution}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/network_study.json"))
    parser.add_argument("--output", type=Path, default=Path("results/network_study"))
    args = parser.parse_args()
    audit_report = audit(args.config, args.output)
    write_json(args.output / "audit.json", audit_report)
    print(f"Verified {audit_report['decisions_checked']} decisions and {audit_report['missions_checked']} mission traces.")


if __name__ == "__main__":
    main()
