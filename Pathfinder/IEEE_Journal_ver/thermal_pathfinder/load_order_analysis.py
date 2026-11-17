"""Audit the matched stage-order experiment and measure paired completion changes."""

import json
from pathlib import Path

import numpy as np

from .audit_network import require
from .mission_analysis import audit as audit_missions, paired_result
from .mission_completion import METHODS
from .mission_profiles import arguments, design
from .model import JOINT_NAMES
from .network_study import write_json
from .route_speed_profiles import trace_name

ORDERS = ("negative_first", "positive_first")


def matched_results(config, output):
    report = audit_missions(config, output)
    lock, networks, thermal, starts, _ = design(config)
    spec = lock["study"]
    plans = json.loads((output / "plans.json").read_text())
    runs = json.loads((output / "executions.json").read_text())
    profiles = json.loads((output / "edge_profiles.json").read_text())
    lookup = {(row["map"], row["setting"], row["start"], row["method"]): row for row in plans}
    matches = {}
    for course in spec["maps"]:
        group = matches.setdefault(course["family"], {})
        require(course["order"] in ORDERS and course["order"] not in group, "Unexpected matched course order")
        group[course["order"]] = course

    def completed(name, setting, start, method):
        row = lookup[name, setting, start, method]
        return bool(row["execution"] and runs[row["execution"]]["completed"])

    rows, templates = [], []
    for family, variants in matches.items():
        negative, positive = (variants[order] for order in ORDERS)
        require(negative["stages"] == positive["stages"][::-1]
                and negative["deadline_s"] == positive["deadline_s"], f"Unmatched course {family}")
        require(np.isclose(networks[negative["id"]].junctions[-1], networks[positive["id"]].junctions[-1]),
                f"Distance differs for {family}")
        results = [[] for _ in METHODS]
        for setting in thermal:
            for start in starts[setting]:
                matrix = [[completed(variants[order]["id"], setting, start, method) for method in METHODS]
                          for order in ORDERS]
                for outcome in matrix:
                    for values, value in zip(results, outcome, strict=True):
                        values.append(value)
                rows.append({
                    "template": family, "setting": setting, "start": start,
                    "completed_by_order": {order: dict(zip(METHODS, outcome, strict=True))
                                           for order, outcome in zip(ORDERS, matrix, strict=True)},
                    "advantage_change_pp": 100 * ((matrix[1][1] - matrix[1][0]) - (matrix[0][1] - matrix[0][0])),
                })
        templates.append(results)

    femurs = [[index for index, joint in enumerate(JOINT_NAMES)
               if joint.startswith(side) and joint.endswith("_femur")] for side in ("L", "R")]
    loading = []
    for name, network in networks.items():
        for stage, edges in network.edges.items():
            for edge in edges:
                filename = trace_name(name, edge, 1.0)
                if not profiles[filename]["completed"]:
                    continue
                with np.load(output / "profiles" / filename) as trace:
                    effort = [(trace["torque_nm"][:, group]**2).sum() * lock["sample_interval_s"] for group in femurs]
                loading.append({"map": name, "stage": stage + 1, "branch": edge.name,
                                "left_femur_torque_squared_integral": float(effort[0]),
                                "right_femur_torque_squared_integral": float(effort[1]),
                                "more_nominal_femur_effort": "left" if effort[0] > effort[1] else "right"})
    primary = paired_result(templates, spec["bootstrap_seed"])
    primary["meets_original_10_point_target"] = primary["mean_gain_pp"] >= spec["minimum_gain_pp"]
    return report | {
        "primary_comparison": primary, "matched_templates": len(templates),
        "completion_switches_with_order": {
            method: sum(row["completed_by_order"][ORDERS[0]][method] != row["completed_by_order"][ORDERS[1]][method]
                        for row in rows) for method in METHODS
        },
        "paired_order_rows": rows, "nominal_femur_loading": loading,
    }


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=Path("experiments/matched_load_order.json"),
                        output=Path("results/matched_load_order"))
    args = parser.parse_args()
    result = matched_results(args.config, args.output)
    write_json(args.output / "summary.json", result)
    keys = ("matched_templates", "by_method", "primary_comparison", "completion_switches_with_order")
    print(json.dumps({key: result[key] for key in keys}, indent=2))


if __name__ == "__main__":
    main()
