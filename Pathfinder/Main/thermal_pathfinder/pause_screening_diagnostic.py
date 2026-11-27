"""Recompute pause forecast gates for the confirmation study's time-only fallback schedules."""

from collections import Counter
import json
from pathlib import Path

import numpy as np

from .margin_profiles import digest
from .mission_profiles import arguments, design
from .model import JOINT_NAMES
from .network_study import write_json
from .pause_confirmation import CONFIG, OUTPUT
from .pause_forecast import PauseForecast
from .pause_forecast_study import METHODS, read
from .reactive_study import load_inputs


def audit(config, output):
    lock, networks, thermal, starts, walking = design(config)
    if read(output / "manifest.json") != json.loads(json.dumps(lock)):
        raise ValueError("Confirmation configuration or source changed")
    model = read(output / "pause_model.json")
    frozen = read(output / "evaluation_manifest.json")
    if digest(output / "pause_model.json") != frozen["pause_model_sha256"] or any(
        digest(Path(__file__).with_name(name)) != checksum for name, checksum in model["sources_sha256"].items()
    ):
        raise ValueError("Paused forecast model differs from the executed benchmark")
    spec = lock["study"]
    walks, profiles, provenance = load_inputs(networks, spec, output, walking["goal_radius"])
    if provenance != frozen["profile_hashes"]:
        raise ValueError("Nominal profiles differ from the executed benchmark")
    replays = read(output / "executions.json")
    plans = read(output / "plans.json")
    proposed = {(row["map"], row["setting"], row["start"]): row for row in plans if row["method"] == METHODS[-1]}
    deadlines = {row["id"]: row["deadline_s"] for row in spec["maps"]}
    load = np.asarray([model["squared_torque_nm2"][joint] for joint in JOINT_NAMES])
    rows = []
    for plan in plans:
        if plan["method"] != METHODS[1] or not plan["execution"] or not plan["pause_s"]:
            continue
        name, setting, start = key = (plan["map"], plan["setting"], plan["start"])
        settings = thermal[setting]
        options = {action.name: action for action in walks[name]}
        schedule = tuple(options[action] for action in plan["schedule"])
        forecaster = PauseForecast(networks[name], profiles[name], settings, spec, walking["goal_radius"], load)
        prediction = forecaster.predict_pause(schedule, starts[setting][start])
        observed = replays[plan["execution"]]
        if digest(output / observed["trace"]) != observed["trace_sha256"]:
            raise ValueError(f"Physics replay changed for {key}")
        reason = []
        ceiling = settings.limit_c - spec["thermal_margin_c"]
        if prediction.peak_c >= ceiling:
            reason.append("temperature")
        if prediction.elapsed_s > deadlines[name]:
            reason.append("deadline")
        if not reason and not proposed[key]["execution"]:
            raise ValueError(f"An admissible candidate was not found by the searched planner for {key}")
        rows.append({
            "map": name, "setting": setting, "start": start, "execution": plan["execution"],
            "paired_planner_execution": proposed[key]["execution"],
            "predicted_peak_c": prediction.peak_c, "predicted_elapsed_s": prediction.elapsed_s,
            "ceiling_c": ceiling, "limit_c": settings.limit_c, "deadline_s": deadlines[name],
            "screen": "+".join(reason) or "admit", "actual_peak_c": observed["peak_c"],
            "actual_elapsed_s": observed["elapsed_s"], "actual_outcome": observed["failure"] or "completed",
            "pause_reached": observed["pause"] is not None,
        })
    missed = [row for row in rows if row["actual_outcome"] == "completed" and not row["paired_planner_execution"]]
    return {
        "post_hoc": True, "schedules": len(rows),
        "screen_by_observed_outcome": dict(Counter(f"{r['screen']}/{r['actual_outcome']}" for r in rows)),
        "zero_margin_screen_by_observed_outcome": dict(Counter(
            f"{'admit' if r['predicted_peak_c'] < r['limit_c'] and r['predicted_elapsed_s'] <= r['deadline_s'] else 'reject'}/{r['actual_outcome']}"
            for r in rows
        )),
        "missed_finishes": len(missed), "missed_finishes_by_screen": dict(Counter(r["screen"] for r in missed)),
        "missed_finishes_with_forecast_below_physical_limit": sum(r["predicted_peak_c"] < r["limit_c"] for r in missed),
        "thermal_stops_before_pause": sum(r["actual_outcome"] == "thermal_limit" and not r["pause_reached"] for r in rows),
        "source_sha256": {name: digest(output / name) for name in ("plans.json", "executions.json", "pause_model.json")},
        "cases": rows,
    }


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=CONFIG, output=OUTPUT)
    args = parser.parse_args()
    report = audit(args.config, args.output)
    write_json(args.output / "screening_diagnostic.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))


if __name__ == "__main__":
    main()
