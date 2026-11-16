"""Joint-only position tracking for a slow, world-frame crawl gait."""

from dataclasses import dataclass

import mujoco
import numpy as np

from .model import FOOT_RADIUS, HIP_POSITIONS, JOINT_LIMITS, LEG_NAMES, LINK_LENGTHS, TORQUE_LIMITS, Terrain, build_model

BODY_HEIGHT = 0.70
NOMINAL_LATERAL_REACH = 0.68
WALK_PERIOD = 3.0
SWING_FRACTION = 0.135
SWING_LIFT = 0.09
STAND_SECONDS = 2.0
SAMPLE_SECONDS = 0.02
KP = np.tile([440.0, 620.0, 570.0], 6)
KD = np.tile([26.0, 38.0, 32.0], 6)
PHASES = np.array([0, 2, 4, 3, 5, 1]) / 6


def foot_targets(time, terrain, speed):
    feet = HIP_POSITIONS.copy()
    feet[:, 1] += np.sign(feet[:, 1]) * NOMINAL_LATERAL_REACH
    feet[:, 2] = terrain.foot_height(feet[:, 1])
    if time <= 0:
        return feet

    # Each foot is world-fixed between swings. Delay the first swing of
    # each leg by its phase offset and blend its first stride from rest.
    elapsed_cycles = time / WALK_PERIOD - PHASES
    completed = np.maximum(0, np.floor(elapsed_cycles)).astype(int)
    fraction = elapsed_cycles - completed
    swing_progress = np.clip(fraction / SWING_FRACTION, 0, 1)
    blend = swing_progress**3 * (10 + swing_progress * (-15 + 6 * swing_progress))
    stride = speed * WALK_PERIOD
    first_step = stride * (PHASES + 0.5 + SWING_FRACTION / 2)
    start = np.where(completed == 0, 0, first_step + (completed - 1) * stride)
    end = first_step + completed * stride
    feet[:, 0] += start + blend * (end - start)
    feet[:, 2] += SWING_LIFT * np.sin(np.pi * swing_progress)**2
    return feet


def joint_targets(feet, base_x):
    return local_joint_targets(feet - [base_x, 0, BODY_HEIGHT])


def local_joint_targets(feet_relative_to_base):
    local = feet_relative_to_base - HIP_POSITIONS
    side = np.sign(HIP_POSITIONS[:, 1])
    # Rotate world x/y into each outward-facing coxa frame.
    outward = local[:, 1] * side
    lateral = -local[:, 0] * side
    coxa, femur, tibia = LINK_LENGTHS
    radial = np.hypot(outward, lateral) - coxa
    down = -local[:, 2]
    cosine = (radial**2 + down**2 - femur**2 - tibia**2) / (2 * femur * tibia)
    knee = np.arccos(np.clip(cosine, -1, 1))
    thigh = np.arctan2(down, radial) - np.arctan2(tibia * np.sin(knee), femur + tibia * np.cos(knee))
    angles = np.column_stack((np.arctan2(lateral, outward), thigh, knee))
    lower, upper = np.asarray(JOINT_LIMITS).T
    return np.clip(angles, lower, upper).ravel()


@dataclass
class Walk:
    completed: bool
    failure: str | None
    elapsed_s: float
    forward_m: float
    max_lateral_m: float
    max_tilt_deg: float
    min_contacts: int
    torque_saturation_fraction: float
    torques: np.ndarray
    body_xyz_m: np.ndarray
    foot_contacts: np.ndarray
    leg_contact_samples: int


def simulate(slope, distance, speed, *, deadline=None, max_lateral=0.55, thermal=None, temperature_history=None):
    """Record RMS joint torque in fixed intervals, including the initial stand."""
    if distance <= 0 or speed <= 0 or max_lateral <= 0 or (deadline is not None and deadline <= 0):
        raise ValueError("Distance, speed, corridor limit and deadline must be positive")
    terrain = Terrain(slope)
    if deadline is None:
        deadline = STAND_SECONDS + distance / speed + 3.0
    return run_walk(
        terrain, joint_targets(foot_targets(0, terrain, speed), 0),
        [0, 0, BODY_HEIGHT + 0.004],
        lambda time, model, data: joint_pd(joint_targets(foot_targets(time, terrain, speed), time * speed), data),
        lambda xy: (abs(float(xy[1])), float(xy[0]) >= distance),
        deadline, max_lateral, thermal, temperature_history,
    )


def joint_pd(target, data):
    return KP * (target - data.qpos[7:]) - KD * data.qvel[6:]


def run_walk(terrain, initial_joints, initial_xyz, control, route_status, deadline,
             max_lateral, thermal=None, temperature_history=None):
    """Run a free-body simulation with the specified joint and route references."""
    model = build_model(terrain)
    data = mujoco.MjData(model)
    body_id = model.body("chassis").id
    data.qpos[:3] = initial_xyz
    data.qpos[7:] = initial_joints
    mujoco.mj_forward(model, data)
    feet_ids = {model.geom(f"{leg}_foot").id for leg in LEG_NAMES}
    ground_ids = {i for i in range(model.ngeom) if model.geom_bodyid[i] == 0}
    base_geom = model.geom("chassis_collision").id
    steps_per_sample = round(SAMPLE_SECONDS / model.opt.timestep)
    if thermal is not None and thermal.exceeded:
        return Walk(False, "thermal_limit", 0.0, 0.0, 0.0, 0.0, 0, 0.0,
                    np.empty((0, model.nu)), np.empty((0, 3)), np.empty(0, dtype=int), 0)
    samples, positions, contact_counts = [], [], []
    leg_contact_samples = 0
    tilt = lateral = 0.0
    minimum_contacts = len(feet_ids)
    saturated = steps = 0
    completed = False
    failure = "deadline"
    for _ in range(int(deadline / SAMPLE_SECONDS)):
        sum_squared = np.zeros(model.nu)
        limits = TORQUE_LIMITS if thermal is None else thermal.torque_limits(TORQUE_LIMITS)
        chassis_contact = False
        for _ in range(steps_per_sample):
            time = max(0.0, data.time - STAND_SECONDS)
            request = control(time, model, data)
            data.ctrl[:] = np.clip(request, -limits, limits)
            saturated += np.count_nonzero(np.abs(request) > limits)
            steps += model.nu
            mujoco.mj_step(model, data)
            sum_squared += data.actuator_force**2
            chassis_contact |= any(
                (contact.geom[0] == base_geom and contact.geom[1] in ground_ids)
                or (contact.geom[1] == base_geom and contact.geom[0] in ground_ids)
                for contact in data.contact
            )
        torque = np.sqrt(sum_squared / steps_per_sample)
        samples.append(torque)
        positions.append(data.qpos[:3].copy())
        upright = float(data.xmat[body_id, 8])
        tilt = max(tilt, float(np.degrees(np.arccos(np.clip(upright, -1.0, 1.0)))))
        drift, reached_goal = route_status(data.qpos[:2])
        lateral = max(lateral, drift)
        ground_contacts = set()
        for contact in data.contact:
            first, second = contact.geom
            if first in ground_ids:
                ground_contacts.add(second)
            elif second in ground_ids:
                ground_contacts.add(first)
        contact_counts.append(len(ground_contacts & feet_ids))
        leg_contact_samples += bool(ground_contacts - feet_ids - {base_geom})
        if data.time >= STAND_SECONDS:
            minimum_contacts = min(minimum_contacts, contact_counts[-1])
        if thermal is not None:
            thermal.advance(torque, SAMPLE_SECONDS)
            if temperature_history is not None:
                temperature_history.append(thermal.temperature_c.copy())
            if thermal.exceeded:
                failure = "thermal_limit"
                break
        if upright < 0.65 or chassis_contact or data.qpos[2] < FOOT_RADIUS * 2:
            failure = "fall_or_chassis_contact"
            break
        if lateral > max_lateral:
            failure = "left_corridor"
            break
        if reached_goal:
            completed, failure = True, None
            break
    return Walk(
        completed, failure, float(data.time), float(data.qpos[0]), lateral,
        tilt, minimum_contacts if data.time >= STAND_SECONDS else 0, saturated / steps if steps else 0.0,
        np.asarray(samples).reshape(-1, model.nu), np.asarray(positions).reshape(-1, 3),
        np.asarray(contact_counts, dtype=int), leg_contact_samples,
    )
