"""Freeze the pause planner comparison and audit the paired confirmation run."""

from collections import Counter
from itertools import product
import json
from pathlib import Path

from .margin_profiles import digest
from .mission_profiles import arguments, design
from .model import JOINT_NAMES
from .network_study import write_json
from .pause_forecast_study import METHODS, identify_load, summary as planner_summary
from .reactive_study import check_execution

CONFIG = Path("experiments/pause_forecast_confirmation.json")
OUTPUT = Path("results/pause_forecast_confirmation")
REFERENCES = Path("results")


def read(path):
    return json.loads(path.read_text())


def confirmation_lock(config, references):
    design_lock, networks, _, starts, _ = design(config)
    study = design_lock["study"]
    reference = references / "pause_forecast"
    reference_design = read(reference / "manifest.json")
    reference_model = read(reference / "pause_model.json")
    variable_fields = {"name", "maps", "bootstrap_seed"}
    if ({k: v for k, v in reference_design["study"].items() if k not in variable_fields}
            != {k: v for k, v in study.items() if k not in variable_fields}):
        raise ValueError("The planner or controller settings differ from the frozen reference")
    if design_lock["base"] != reference_design["base"] or design_lock["runtime"] != reference_design["runtime"]:
        raise ValueError("The base simulator settings or runtime differ from the reference")
    reference_sources = {
        name: checksum for name, checksum in reference_design["sha256"].items()
        if name not in ("pause_forecast.json", "connected_pilot.json")
    } | reference_model["sources_sha256"]
    if any(digest(Path(__file__).with_name(name)) != checksum for name, checksum in reference_sources.items()):
        raise ValueError("A frozen planner or simulator source changed")
    load, provenance = identify_load(config, references / "junction_pause", study["pause_s"])
    if (reference_model["squared_torque_nm2"] != dict(zip(JOINT_NAMES, load.tolist(), strict=True))
            or any(reference_model[key] != value for key, value in provenance.items())):
        raise ValueError("Hold loads or their development evidence changed")

    maps = study["maps"]
    archive_maps = [row for file in config.parent.glob("*.json") if file != config
                    for row in read(file).get("maps", []) if "stages" in row]
    geometries = [json.dumps(row["stages"], sort_keys=True) for row in maps]
    if (len(maps) != len(networks) or len(set(geometries)) != 12
            or any(row["id"] in networks or json.dumps(row["stages"], sort_keys=True) in geometries
                   for row in archive_maps)):
        raise ValueError("Expected 12 distinct courses outside the previous experiments")
    families = Counter(row["family"] for row in maps)
    if families != {"alternating": 4, "persistent": 4, "same_sign_stage": 4} or sum(map(len, starts.values())) != 6:
        raise ValueError("Expected four courses per terrain family and six starts per course")
    return {
        "config_sha256": digest(config), "reference_model_sha256": digest(reference / "pause_model.json"),
        "reference_manifest_sha256": digest(reference / "manifest.json"), "planner_sources_sha256": reference_sources,
        "base": design_lock["base"], "runtime": design_lock["runtime"],
        "primary_comparison": [METHODS[0], METHODS[-1]], "secondary_comparison": [METHODS[1], METHODS[-1]],
        "minimum_completion_gain_pp": study["minimum_gain_pp"], "maximum_additional_thermal_stops": 0,
        "expected_starts": 72, "methods": METHODS, "family_counts": dict(families),
        "report_by": ["course", "terrain_family", "thermal_setting"],
    }


def freeze(config, output, references):
    lock = json.loads(json.dumps(confirmation_lock(config, references)))
    path = output / "confirmation_lock.json"
    output.mkdir(parents=True, exist_ok=True)
    if (output / "missions").exists():
        raise ValueError("Freeze the comparison before running warm missions")
    if path.exists() and read(path) != lock:
        raise ValueError("Frozen design differs from this invocation")
    if not path.exists():
        with path.open("x") as file:
            file.write(json.dumps(lock, indent=2, allow_nan=False) + "\n")
    print(f"Frozen {lock['expected_starts']} starts and unchanged predictor: {path}")


def outcome(row, replays):
    if row["execution"] is None:
        return row["planning_failure"]
    return replays[row["execution"]]["failure"] or "completed"


def breakdown(cases, replays):
    counts = {method: Counter(outcome(case[method], replays) for case in cases) for method in METHODS}
    return {method: dict(values) for method, values in counts.items()}


def audit(config, output, references):
    expected = json.loads(json.dumps(confirmation_lock(config, references)))
    if read(output / "confirmation_lock.json") != expected:
        raise ValueError("Frozen confirmation design mismatch")
    lock, networks, thermal, starts, walking = design(config)
    if read(output / "manifest.json") != json.loads(json.dumps(lock)):
        raise ValueError("Nominal confirmation manifest mismatch")
    spec = lock["study"]
    model = read(output / "pause_model.json")
    reference_model = read(references / "pause_forecast" / "pause_model.json")
    if {key: value for key, value in model.items() if key != "held_out_config_sha256"} != {
        key: value for key, value in reference_model.items() if key != "held_out_config_sha256"
    }:
        raise ValueError("The executed pause model differs from the frozen reference")
    evaluation = read(output / "evaluation_manifest.json")
    if evaluation["pause_model_sha256"] != digest(output / "pause_model.json"):
        raise ValueError("Executed pause model hash mismatch")
    profiles = evaluation["profile_hashes"]
    if len(profiles) != 96 or any(digest(output / "profiles" / name) != item["sha256"] for name, item in profiles.items()):
        raise ValueError("Incomplete or changed nominal profiles")

    plans = read(output / "plans.json")
    replays = read(output / "executions.json")
    rows = {(p["map"], p["setting"], p["start"], p["method"]): p for p in plans}
    cases = [(name, setting, start) for name, setting in product(networks, thermal) for start in starts[setting]]
    if len(cases) != expected["expected_starts"] or len(plans) != len(rows) or set(rows) != {
        (*case, method) for case, method in product(cases, METHODS)
    }:
        raise ValueError("Incomplete paired results")
    lookups = {case: {method: rows[(*case, method)] for method in METHODS} for case in cases}
    deadlines = {item["id"]: item["deadline_s"] for item in spec["maps"]}
    families = {item["id"]: item["family"] for item in spec["maps"]}
    replay_identity = {}
    for identity, comparisons in lookups.items():
        name, setting, start = identity
        fixed = comparisons[METHODS[0]]
        if fixed["execution"] and any(plan["execution"] != fixed["execution"] for plan in comparisons.values()):
            raise ValueError("A fallback changed an original admission")
        for method, plan in comparisons.items():
            key = plan["execution"]
            if key is None:
                if plan["planning_failure"] not in ("no_route", "planning_timeout") or plan["schedule"]:
                    raise ValueError(f"Invalid rejection: {identity}")
                continue
            if (plan["planning_failure"] or plan["planning_s"] >= spec["planning_budget_s"]
                    or plan["predicted_elapsed_s"] > deadlines[name]):
                raise ValueError(f"Invalid admission: {key}")
            if (method != METHODS[1] or not plan["pause_s"]) and (
                plan["predicted_peak_c"] >= thermal[setting].limit_c - spec["thermal_margin_c"]
            ):
                raise ValueError(f"Thermal admission mismatch: {key}")
            if plan["pause_s"] not in (0.0, spec["pause_s"]) or (plan["pause_s"] and (method == METHODS[0] or fixed["execution"])):
                raise ValueError(f"Invalid pause condition: {key}")
            trace_case = (*identity, tuple(plan["schedule"]), plan["pause_s"])
            if replay_identity.setdefault(key, trace_case) != trace_case:
                raise ValueError(f"Replay key reused for a different mission: {key}")
    if set(replay_identity) != set(replays):
        raise ValueError("Missing or extra physics results")
    for key, record in replays.items():
        name, setting, start, _, pause = replay_identity[key]
        path = output / record["trace"]
        if digest(path) != record["trace_sha256"] or (record["pause"] is not None and not pause):
            raise ValueError(f"Trace or pause differs from recorded mission: {key}")
        check_execution(path, record, starts[setting][start], networks[name], thermal[setting],
                        deadlines[name], walking["goal_radius"])

    primary = planner_summary(plans, replays, spec)
    if primary != read(output / "summary.json"):
        raise ValueError("Saved summary disagrees with paired results")
    gained, lost = [], []
    for identity, comparison in lookups.items():
        fixed = outcome(comparison[METHODS[0]], replays)
        proposed = outcome(comparison[METHODS[-1]], replays)
        if (fixed == "completed") != (proposed == "completed"):
            collection = gained if proposed == "completed" else lost
            collection.append({"map": identity[0], "setting": identity[1], "start": identity[2],
                               "fixed": fixed, "pause_forecast": proposed})

    by_course = {name: breakdown([group for case, group in lookups.items() if case[0] == name], replays)
                 for name in networks}
    by_family = {family: breakdown([group for case, group in lookups.items() if families[case[0]] == family], replays)
                 for family in expected["family_counts"]}
    by_setting = {name: breakdown([group for case, group in lookups.items() if case[1] == name], replays)
                  for name in thermal}
    report = {
        "primary": primary,
        "nominal_profile_outcomes": dict(Counter(row["outcome"] for row in profiles.values())),
        "by_course": by_course, "by_family": by_family, "by_thermal_setting": by_setting,
        "additional_finishes": gained, "lost_finishes": lost,
        "courses_with_additional_finishes": len({row["map"] for row in gained}),
        "verified_replays": len(replays),
    }
    write_json(output / "confirmation_audit.json", report)
    print(json.dumps({key: report[key] for key in (
        "nominal_profile_outcomes", "additional_finishes", "lost_finishes", "verified_replays"
    )}, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=CONFIG, output=OUTPUT)
    parser.add_argument("action", choices=("freeze", "audit"))
    parser.add_argument("--references", type=Path, default=REFERENCES)
    args = parser.parse_args()
    action = freeze if args.action == "freeze" else audit
    action(args.config, args.output, args.references)


if __name__ == "__main__":
    main()
