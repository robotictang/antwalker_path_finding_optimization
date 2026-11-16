"""Audit a fixed thermal margin on new courses and report results by network length."""

from collections import Counter
import json
from pathlib import Path

import numpy as np

from .audit_network import require
from .margin_analysis import evaluate, margin_counts
from .margin_profiles import METHODS
from .margin_study import arguments
from .network_study import write_json


def evaluate_transfer(config, development, reference, output):
    summary = evaluate(config, development, reference, output)
    spec = json.loads(config.read_text())
    runs = json.loads((output / "executions.json").read_text())
    plans = json.loads((output / "plans.json").read_text())
    profiles = json.loads((output / "edge_profiles.json").read_text())
    profile_outcomes = Counter()
    expected_profiles = set()
    for course in spec["maps"]:
        for stage in range(1, len(course["stages"]) + 1):
            for branch in ("left", "right"):
                for fraction in spec["speed_fractions"]:
                    from_name = f"{course['id']}_s{stage}_{branch}_speed{fraction:g}.npz"
                    expected_profiles.add(from_name)
    require(set(profiles) == expected_profiles, "Missing or extra profile records")
    for name, profile in profiles.items():
        with np.load(output / "profiles" / name) as trace:
            require(len(trace["torque_nm"]) == len(trace["body_xyz_m"]) == len(trace["foot_contacts"]),
                    f"Profile trace lengths differ for {name}")
        profile_outcomes[profile["failure"] or "completed"] += 1
    chosen = summary["calibration"]["selected_margin_c"]
    margins = spec["margin_grid_c"]
    categories = {"course": [course["id"] for course in spec["maps"]],
                  "setting": [setting["id"] for setting in spec["thermal_settings"]]}
    rows = {}
    for category, names in categories.items():
        field = "map" if category == "course" else category
        rows[category] = {
            name: {
                method: [{"margin_c": margin, **margin_counts(
                    [plan for plan in plans if plan[field] == name and plan["method"] == method], runs, margin
                )} for margin in margins]
                for method in METHODS
            }
            for name in names
        }
    summary["transfer"] = {
        "primary_margin_c": chosen,
        "nominal_profile_outcomes": dict(profile_outcomes),
        "by_course_and_setting": rows,
    }
    return summary


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=Path("experiments/thermal_margin_transfer.json"),
                        output=Path("results/thermal_margin_transfer"))
    args = parser.parse_args()
    result = evaluate_transfer(args.config, args.development, args.reference, args.output)
    write_json(args.output / "summary.json", result)
    print(json.dumps({"outcomes": result["unique_outcomes"], "all_policies": result["margin_sweep"]["all_policies"]},
                     indent=2))


if __name__ == "__main__":
    main()
