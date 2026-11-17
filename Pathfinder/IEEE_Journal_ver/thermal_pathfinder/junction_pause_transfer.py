"""Test the same junction pause on other archived courses with paired schedules."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from .junction_pause import replay_pause
from .margin_profiles import digest
from .mission_profiles import arguments, design
from .network_study import write_json
from .reactive_forecast import ProgressForecast
from .reactive_study import check_execution, choose_progress, load_inputs
from .walking import SAMPLE_SECONDS


@dataclass
class Trial:
    case: dict
    mission: tuple
    trace_id: str
    archive: tuple | None


def load_trials(config, references, development):
    study = json.loads(config.read_text())
    pilot = json.loads((development / "summary.json").read_text())
    previous = json.loads((development / "manifest.json").read_text())
    if (digest(config.with_name(study["development_config"])) != previous["sha256"][study["development_config"]]
            or digest(Path(__file__).with_name("junction_pause.py")) != previous["sha256"]["junction_pause.py"]
            or pilot["by_duration_s"][f"{study['pause_s']:g}"]["outcomes"].get("completed", 0) == 0):
        raise ValueError("Transfer pause must match the completed development condition and controller")
    duration = study["pause_s"]
    references_sha = {}
    cases, trials = [], []
    for group in study["references"]:
        name = group["study"]
        archive = references / name
        lock, networks, settings, starts, walking = design(config.with_name(f"{name}.json"))
        spec = lock["study"]
        if json.loads((archive / "manifest.json").read_text()) != json.loads(json.dumps(lock)):
            raise ValueError(f"Archived course configurations or sources changed for {name}")
        provenance = "forecast_manifest.json" if name == "reactive_forecast" else "evaluation_manifest.json"
        walks, profiles, profile_hashes = load_inputs(networks, spec, archive, walking["goal_radius"])
        if profile_hashes != json.loads((archive / provenance).read_text())["nominal_profiles"]:
            raise ValueError(f"Archived nominal profiles changed for {name}")
        files = ("manifest.json", provenance, "plans.json", "executions.json", "edge_profiles.json")
        references_sha[name] = {file: digest(archive / file) for file in files}
        plans, executions = (json.loads((archive / file).read_text()) for file in ("plans.json", "executions.json"))
        fixed = {(row["map"], row["setting"], row["start"]): row for row in plans
                 if row["method"] == group["fixed_method"]}
        deadlines = {item["id"]: item["deadline_s"] for item in spec["maps"]}
        for course in group["maps"]:
            network = networks[course]
            if course == previous["study"]["map"] or len(network.junctions) != 3:
                raise ValueError("Use a two-stage course outside the pause development run")
            junction = float(network.junctions[study["junction_index"]])
            deadline = deadlines[course]
            actions = {action.name: action for action in walks[course]}
            for setting, thermal in settings.items():
                predictor = ProgressForecast(network, profiles[course], thermal, spec, walking["goal_radius"])
                for start, initial in starts[setting].items():
                    identity = course, setting, start
                    original = fixed[identity]
                    case = {"reference": name, "map": course, "setting": setting, "start": start,
                            "deadline_s": deadline, "original_planning_failure": original["planning_failure"]}
                    cases.append(case)
                    if original["execution"]:
                        schedule = tuple(actions[action] for action in original["actions"])
                        prediction = predictor.predict(schedule, initial, True)
                        peak, elapsed = prediction.peak_c, prediction.elapsed_s
                        reason = "original_admission"
                    else:
                        schedule, peak, elapsed, _, _, failure = choose_progress(
                            network, predictor, initial, deadline - duration, float("inf"),
                            spec["planning_budget_s"], walks[course], True,
                        )
                        reason = failure or "deadline_screened_fallback"
                    case.update({"selection": reason, "schedule": [action.name for action in schedule],
                                 "forecast_peak_c": peak, "forecast_without_pause_s": elapsed})
                    if not schedule:
                        continue
                    trace_id = "_".join((*identity, *(action.name for action in schedule)))
                    record = executions.get(trace_id)
                    reused = (record, archive / record["trace"]) if record else None
                    mission = (network, schedule, spec, deadline, walking, thermal, initial, junction)
                    trials.append(Trial(case, mission, trace_id, reused))
    return study, cases, trials, references_sha


def audit_trace(trial, result, path, origin):
    network, _, _, deadline, walking, thermal, initial, _ = trial.mission
    check_execution(path, result, initial, network, thermal, deadline, walking["goal_radius"])
    return {**result, "archive_path" if origin == "archive" else "trace": str(path),
            "origin": origin, "trace_sha256": digest(path)}


def check_pair(trial, without, paused):
    if paused["pause"] is None:
        if any(without[field] != paused[field] for field in ("completed", "failure", "elapsed_s", "peak_c")):
            raise ValueError(f"Pre-junction outcomes differ in {trial.trace_id}")
        prefix = None
    else:
        at = paused["pause"]["started_s"]
        prefix = int(at / SAMPLE_SECONDS + 1e-7)
    with (np.load(without.get("archive_path", without["trace"])) as zero_trace,
          np.load(paused["trace"]) as pause_trace):
        if any(not np.array_equal(zero_trace[key][:prefix], pause_trace[key][:prefix]) for key in zero_trace.files):
            raise ValueError(f"Physics diverged before pause on {trial.trace_id}")


def summarize(cases):
    paired = [row for row in cases if "pause" in row]
    baseline = [row["no_pause"]["failure"] or "completed" for row in paired]
    pause = [row["pause"]["failure"] or "completed" for row in paired]
    transitions = Counter(f"{left}/{right}" for left, right in zip(baseline, pause, strict=True))
    actual = [row["pause"]["pause"] for row in paired if row["pause"]["pause"] is not None]
    policy = Counter()
    original = Counter()
    for row in cases:
        if row["selection"] == "original_admission":
            outcome = row["no_pause"]["failure"] or "completed"
            original[outcome] += 1
            policy[outcome] += 1
        else:
            original[row["original_planning_failure"]] += 1
            policy[(row["pause"]["failure"] or "completed") if "pause" in row else row["selection"]] += 1
    return {
        "total_starts": len(cases), "paired_schedules": len(paired),
        "schedule_selection": dict(Counter(row["selection"] for row in cases)),
        "paired_outcomes": {"no_pause": dict(Counter(baseline)), "pause": dict(Counter(pause)),
                            "transitions": dict(transitions)},
        "pauses_reached": len(actual),
        "hottest_temperature_dropped": sum(hold["peak_after_c"] < hold["peak_before_c"] for hold in actual),
        "derived_policy_outcomes": {"original": dict(original), "pause_fallback": dict(policy)},
        "cases": cases,
    }


def run(config, references, development, output, workers):
    study, cases, trials, reference_hashes = load_trials(config, references, development)
    folder = output / "missions"
    folder.mkdir(parents=True, exist_ok=False)
    for trial in trials:
        if trial.archive:
            record, path = trial.archive
            trial.case["no_pause"] = audit_trace(trial, record | {"pause": None}, path, "archive")
    write_json(output / "manifest.json", {
        "study": study, "config_sha256": digest(config), "inputs_sha256": reference_hashes,
        "pause_pilot_summary_sha256": digest(development / "summary.json"),
        "sources_sha256": {name: digest(Path(__file__).with_name(name))
                           for name in ("junction_pause.py", "junction_pause_transfer.py")},
        "selected_cases": [{key: value for key, value in row.items() if key != "no_pause"} for row in cases],
        "reused_traces_sha256": {trial.trace_id: trial.case["no_pause"]["trace_sha256"]
                                 for trial in trials if trial.archive},
    })
    print(f"{len(cases)} starts, {len(trials)} paired schedules, "
          f"{sum(trial.archive is not None for trial in trials)} reused controls", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {}
        for trial in trials:
            arms = {"pause": study["pause_s"]}
            if not trial.archive:
                arms["no_pause"] = 0.0
            for arm, duration in arms.items():
                path = folder / f"{trial.trace_id}_{arm}.npz"
                jobs[pool.submit(replay_pause, *trial.mission, duration, path)] = trial, arm, path
        for count, future in enumerate(as_completed(jobs), 1):
            trial, arm, path = jobs[future]
            result = future.result()
            trial.case[arm] = audit_trace(trial, result, path, "new")
            print(f"{count}/{len(jobs)} {path.stem}: {result['failure'] or 'completed'}", flush=True)

    for trial in trials:
        check_pair(trial, trial.case["no_pause"], trial.case["pause"])
    report = summarize(cases)
    write_json(output / "summary.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=Path("experiments/junction_pause_transfer.json"),
                        output=Path("results/junction_pause_transfer"))
    parser.add_argument("--references", type=Path, default=Path("results"))
    parser.add_argument("--development", type=Path, default=Path("results/junction_pause"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.config, args.references, args.development, args.output, args.workers)


if __name__ == "__main__":
    main()
