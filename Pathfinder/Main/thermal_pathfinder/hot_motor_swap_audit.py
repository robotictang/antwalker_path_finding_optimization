"""Independently check recorded physics for the hot-motor swap experiment."""

from pathlib import Path

import numpy as np

from .margin_profiles import digest
from .model import JOINT_NAMES
from .reactive_study import check_execution
from .walking import SAMPLE_SECONDS, STAND_SECONDS

TRACE_FIELDS = {"torque_nm", "body_xyz_m", "temperature_c", "foot_contacts"}
FAILURES = {None, "thermal_limit", "deadline", "fall_or_chassis_contact", "left_corridor"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_trace(output, record, initial, network, settings, deadline, goal_radius):
    """Validate a replay and return provenance and independently derived metrics."""
    output = Path(output).resolve()
    relative = Path(record["trace"])
    path = (output / relative).resolve()
    require(not relative.is_absolute() and path.is_relative_to(output) and path.suffix == ".npz",
            "Replay trace must be a relative NumPy archive inside the output directory")
    checksum = digest(path)
    for field in ("sha256", "trace_sha256"):
        require(field not in record or record[field] == checksum,
                f"Recorded trace checksum differs for {relative}")

    initial = np.asarray(initial, dtype=float)
    require(initial.shape == (len(JOINT_NAMES),) and np.isfinite(initial).all(),
            "Expected one finite initial temperature for every actuator")
    require(np.isfinite(deadline) and deadline > 0 and np.isfinite(goal_radius) and goal_radius > 0,
            "Expected a positive finite deadline and goal radius")
    with np.load(path, allow_pickle=False) as trace:
        require(set(trace.files) == TRACE_FIELDS, f"Unexpected recorded arrays for {relative}")
        torque, body, temperature, contacts = (trace[field] for field in
                                               ("torque_nm", "body_xyz_m", "temperature_c", "foot_contacts"))
    count = len(body)
    require(torque.shape == (count, len(JOINT_NAMES)) and body.shape == (count, 3)
            and temperature.shape == (count + 1, len(JOINT_NAMES)) and contacts.shape == (count,),
            f"Recorded array shapes differ for {relative}")
    require(all(np.issubdtype(array.dtype, np.number)
                and np.isfinite(array).all() for array in (torque, body, temperature, contacts)),
            f"Recorded arrays contain nonfinite or nonnumeric values for {relative}")
    require(np.array_equal(temperature[0], initial) and np.all(torque >= 0)
            and np.all((contacts >= 0) & (contacts <= 6) & (contacts == np.floor(contacts))),
            f"Invalid initial motor assignment, RMS torque, or contact count for {relative}")

    inferred = settings.advance(temperature[:-1], torque, SAMPLE_SECONDS)
    residual = float(np.max(np.abs(temperature[1:] - inferred), initial=0.0))
    require(residual < 1e-12, f"Temperature history disagrees with applied torque for {relative}")
    require(np.isfinite(record["elapsed_s"]) and np.isfinite(record["peak_c"])
            and np.isclose(record["elapsed_s"], count * SAMPLE_SECONDS, rtol=0, atol=1e-6)
            and record["elapsed_s"] <= deadline + 1e-6
            and record["peak_c"] == float(temperature.max()),
            f"Recorded duration or peak differs from the trace for {relative}")
    require(record["failure"] in FAILURES and record["completed"] == (record["failure"] is None),
            f"Inconsistent completion and termination fields for {relative}")
    if count:
        require(record["forward_m"] == float(body[-1, 0]), f"Final progress differs for {relative}")

    crossing = np.flatnonzero(np.any(temperature >= settings.limit_c, axis=1))
    first_crossing = int(crossing[0]) if crossing.size else None
    require((record["failure"] == "thermal_limit") == bool(crossing.size)
            and (first_crossing is None or first_crossing == count),
            f"Thermal trace did not stop at its first threshold crossing for {relative}")
    require(count <= int(deadline / SAMPLE_SECONDS),
            f"Replay contains more samples than its deadline allows for {relative}")
    if record["failure"] == "deadline":
        require(count == int(deadline / SAMPLE_SECONDS),
                f"Deadline replay terminated before its allotted sample count for {relative}")

    events = record["junction_events"]
    require(len(events) <= len(network.junctions) - 2,
            f"Too many junction events for {relative}")
    prior_time = 0.0
    for stage, event in enumerate(events, 1):
        time, x = event["walking_time_s"], event["x_m"]
        require(event["stage"] == stage and np.isfinite(time) and np.isfinite(x)
                and prior_time <= time <= max(0.0, record["elapsed_s"] - STAND_SECONDS) + 1e-6
                and x >= network.junctions[stage],
                f"Invalid junction event for {relative}")
        prior_time = time

    updates = record["speed_updates"]
    infeasible = record["no_feasible_speed_updates"]
    require(isinstance(updates, int) and isinstance(infeasible, int) and 0 <= infeasible <= updates,
            f"Invalid controller update counters for {relative}")
    check_execution(path, record, initial, network, settings, deadline, goal_radius)
    distance = float(np.linalg.norm(body[-1, :2] - [network.junctions[-1], 0])) if count else None
    return {
        "trace_sha256": checksum,
        "samples": count,
        "max_thermal_recurrence_residual_c": residual,
        "first_thermal_crossing_sample": first_crossing,
        "goal_distance_m": distance,
        "reached_goal": distance is not None and distance <= goal_radius,
        "junctions_reached": len(events),
    }
