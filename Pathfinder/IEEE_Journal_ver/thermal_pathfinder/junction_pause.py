"""Test an in-place crawl at a flat junction on the previously infeasible start."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
import json
from pathlib import Path

import numpy as np

from .connected_walk import walk_branch
from .margin_profiles import digest
from .mission_profiles import arguments, design
from .network_study import write_json
from .pilot import walk_summary
from .reactive_study import check_execution
from .route_speed_study import SpeedAction, SpeedSchedule
from .speed_policy import ThermalSlowdown
from .thermal import ThermalState
from .walking import SAMPLE_SECONDS, STAND_SECONDS


@dataclass
class JunctionPause:
    position_m: float
    duration_s: float
    started_s: float | None = field(init=False, default=None)
    resumed_s: float | None = field(init=False, default=None)

    def __post_init__(self):
        if not np.isfinite(self.duration_s) or self.duration_s < 0:
            raise ValueError("Pause duration must be finite and nonnegative")

    def __call__(self, time, x, speed):
        if self.duration_s == 0 or self.resumed_s is not None:
            return speed
        if self.started_s is None and x >= self.position_m:
            self.started_s = time
        if self.started_s is None:
            return speed
        if time < self.started_s + self.duration_s:
            return 0.0
        self.resumed_s = time
        return speed


def replay_pause(network, schedule, spec, deadline, walking, settings, initial, junction, pause_s, path):
    route = network.route(tuple(action.edge for action in schedule))
    planned = SpeedSchedule(tuple(network.junctions[1:-1]), tuple(action.fraction for action in schedule),
                            spec["transition_s"])
    reactive = ThermalSlowdown(**spec["reactive"])
    pause = JunctionPause(junction, pause_s)
    thermal = ThermalState(settings, initial)
    history = [thermal.temperature_c.copy()]

    def speed(time, x, nominal):
        requested = min(planned(time, x, nominal), reactive(time, nominal, thermal))
        return pause(time, x, requested)

    walk = walk_branch(route, **walking, deadline=deadline, thermal=thermal, temperature_history=history,
                       position_speed_policy=speed)
    temperatures = np.asarray(history)
    np.savez_compressed(path, torque_nm=walk.torques, body_xyz_m=walk.body_xyz_m,
                        temperature_c=temperatures, foot_contacts=walk.foot_contacts)
    hold = None
    if pause.started_s is not None:
        first_sample = int((STAND_SECONDS + pause.started_s) / SAMPLE_SECONDS + 1e-7)
        last_sample = (int((STAND_SECONDS + pause.resumed_s) / SAMPLE_SECONDS + 1e-7)
                       if pause.resumed_s is not None else len(walk.torques))
        before, after = temperatures[[first_sample, last_sample]]
        hottest = int(np.argmax(before))
        positions = walk.body_xyz_m[first_sample - 1:last_sample, :2]
        hold = {
            "started_s": STAND_SECONDS + pause.started_s,
            "resumed_s": STAND_SECONDS + pause.resumed_s if pause.resumed_s is not None else None,
            "peak_before_c": float(before.max()), "peak_after_c": float(after.max()),
            "hottest_at_entry_joint_index": hottest,
            "entry_hottest_motor_delta_c": float(after[hottest] - before[hottest]),
            "temperature_before_c": before.tolist(), "temperature_after_c": after.tolist(),
            "maximum_planar_displacement_m": float(np.linalg.norm(positions - positions[0], axis=1).max()),
        }
    return walk_summary(walk) | {
        "peak_c": float(thermal.peak_by_joint_c.max()), "trace": f"missions/{path.name}",
        "junction_events": planned.events, "slowdown_events": reactive.events, "pause": hold,
    }


def equal_traces(before, after):
    with np.load(before) as left, np.load(after) as right:
        return set(left.files) == set(right.files) and all(np.array_equal(left[key], right[key]) for key in left.files)


def run(config, transfer, audit, output, workers):
    study = json.loads(config.read_text())
    lock, networks, settings, starts, walking = design(config.with_name(study["source_config"]))
    spec = lock["study"]
    if json.loads((transfer / "manifest.json").read_text()) != json.loads(json.dumps(lock)):
        raise ValueError("Original simulation settings or sources changed")
    key = study["map"], study["setting"], study["start"]
    case, = [row for row in json.loads((audit / "summary.json").read_text())["cases"]
             if tuple(row[field] for field in ("map", "setting", "start")) == key]
    if case["outcomes"] != {"thermal_limit": len(case["schedules"])}:
        raise ValueError("Expected the original all-thermal-stop case")
    network = networks[key[0]]
    deadline = next(item["deadline_s"] for item in spec["maps"] if item["id"] == key[0])
    thermal, initial = settings[key[1]], starts[key[1]][key[2]]
    junction = float(network.junctions[study["junction_index"]])
    if not 0 < junction < network.junctions[-1]:
        raise ValueError("The pause must use an intermediate junction")
    durations = study["pause_s"]
    if sorted(set(durations)) != durations or not durations or durations[0] <= 0:
        raise ValueError("Pause durations must be unique, positive and sorted")

    actions = {action.name: action for edges in network.edges.values() for edge in edges
               for action in (SpeedAction(edge, fraction) for fraction in spec["speed_fractions"])}
    traces = {}
    rows, jobs = [], []
    zero_key = case["original_plans"]["reactive_calibrated"]["execution"]
    for row in case["schedules"]:
        schedule = tuple(actions[action] for action in row["schedule"])
        name = row["execution"]
        path = Path(row["trace"])
        if row["origin"] == "new":
            path = audit / path
        checksum = digest(path)
        if checksum != row["trace_sha256"]:
            raise ValueError(f"Archived trace changed for {name}")
        with np.load(path) as trace:
            replays_reach_junction = bool(trace["body_xyz_m"][:, 0].max() >= junction)
        traces[name] = {"path": str(path), "sha256": checksum, "reached_junction": replays_reach_junction}
        base = {"schedule": row["schedule"], "baseline_execution": name, "baseline_elapsed_s": row["elapsed_s"]}
        cells = [base | {"pause_s": duration} for duration in durations]
        if name == zero_key:
            zero = base | {"pause_s": 0.0}
            jobs.append((zero, schedule, output / "missions" / f"{name}_pause0.npz"))
        for cell in cells:
            if replays_reach_junction:
                target = output / "missions" / f"{name}_pause{cell['pause_s']:g}.npz"
                jobs.append((cell, schedule, target))
            else:
                # The command is identical to the original until the junction is reached.
                cell.update({"origin": "archived_pre_junction_stop", "failure": row["outcome"], "completed": False,
                             "peak_c": row["peak_c"], "elapsed_s": row["elapsed_s"], "pause": None})
        rows.extend(cells)
    if zero_key not in traces:
        raise ValueError("Missing zero-pause reference")

    folder = output / "missions"
    folder.mkdir(parents=True, exist_ok=False)
    write_json(output / "manifest.json", {
        "study": study, "sha256": {path.name: digest(path) for path in (config, Path(__file__))},
        "transfer_manifest_sha256": digest(transfer / "manifest.json"),
        "schedule_audit_sha256": digest(audit / "summary.json"),
        "junction_m": junction, "deadline_s": deadline, "limit_c": thermal.limit_c, "reference_traces": traces,
    })
    print(f"{len(rows)} cells; running {len(jobs) - 1} pause replays and a zero-pause control", flush=True)
    zero_check = None
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {
            pool.submit(replay_pause, network, schedule, spec, deadline, walking, thermal,
                        initial, junction, cell["pause_s"], path): (cell, path) for cell, schedule, path in jobs
        }
        for index, future in enumerate(as_completed(pending), 1):
            cell, path = pending[future]
            outcome = future.result()
            check_execution(path, outcome, initial, network, thermal, deadline, walking["goal_radius"])
            if cell["pause_s"] == 0:
                if not equal_traces(Path(traces[zero_key]["path"]), path):
                    raise ValueError("Zero-pause controller did not reproduce the original trace exactly")
                zero_check = {"execution": zero_key, "new_trace": outcome["trace"], "identical_arrays": True}
            else:
                cell.update(outcome | {"origin": "new", "trace_sha256": digest(path)})
            print(f"{index}/{len(jobs)} {path.stem}: {outcome['failure'] or 'completed'}", flush=True)

    by_duration = {}
    for duration in durations:
        group = [row for row in rows if row["pause_s"] == duration]
        active = [row for row in group if row["pause"] is not None]
        by_duration[f"{duration:g}"] = {
            "outcomes": dict(Counter(row["failure"] or "completed" for row in group)),
            "reached_pause": len(active),
            "peak_cooled_during_pause": sum(row["pause"]["peak_after_c"] < row["pause"]["peak_before_c"]
                                            for row in active),
            "maximum_pause_displacement_m": max((row["pause"]["maximum_planar_displacement_m"] for row in active),
                                                 default=None),
        }
    summary = {
        "archived_control_outcomes": case["outcomes"], "zero_pause_check": zero_check,
        "conditions": len(rows), "new_pause_replays": len(jobs) - 1, "by_duration_s": by_duration, "schedules": rows,
    }
    write_json(output / "summary.json", summary)
    print(json.dumps(by_duration, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=Path("experiments/junction_pause.json"), output=Path("results/junction_pause"))
    parser.add_argument("--transfer", type=Path, default=Path("results/reactive_margin_transfer"))
    parser.add_argument("--audit", type=Path, default=Path("results/schedule_audit"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args.config, args.transfer, args.audit, args.output, args.workers)


if __name__ == "__main__":
    main()
