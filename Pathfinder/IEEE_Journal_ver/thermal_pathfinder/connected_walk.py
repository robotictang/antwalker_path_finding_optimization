"""Crawl controller with joint actuation and stance force allocation."""

import mujoco
import numpy as np

from .connected_terrain import smoothstep
from .model import HIP_POSITIONS, LEG_NAMES
from .walking import NOMINAL_LATERAL_REACH, PHASES, SWING_FRACTION, SWING_LIFT, WALK_PERIOD
from .walking import joint_pd, local_joint_targets, run_walk

STANCE_HEIGHT = 0.56

HOME = HIP_POSITIONS[:, :2].copy()
HOME[:, 1] += np.sign(HOME[:, 1]) * NOMINAL_LATERAL_REACH


def branch_feet(branch, arc):
    x, y, yaw = branch.pose(arc)
    cosine, sine = np.cos(yaw), np.sin(yaw)
    foot_x = x + HOME[:, 0] * cosine - HOME[:, 1] * sine
    foot_y = y + HOME[:, 0] * sine + HOME[:, 1] * cosine
    return np.column_stack((foot_x, foot_y, branch.terrain.foot_height(foot_x, foot_y)))


def stance_forces(feet, center, force, moment):
    """Allocate the target body wrench across stance feet."""
    offsets = feet - center
    cross = np.cross(offsets[:, :, None], np.eye(3)[None, :, :], axisa=1, axisb=1, axisc=1)
    matrix = np.vstack((np.tile(np.eye(3), len(feet)), cross.transpose(1, 0, 2).reshape(3, -1)))
    wrench = np.r_[force, moment]
    forces = (matrix.T @ np.linalg.solve(matrix @ matrix.T + np.eye(6) * 0.02, wrench)).reshape(-1, 3)
    forces[:, 2] = np.maximum(forces[:, 2], 0.0)
    horizontal = np.linalg.norm(forces[:, :2], axis=1)
    forces[:, :2] *= np.minimum(1.0, 0.65 * forces[:, 2] / np.maximum(horizontal, 1e-9))[:, None]
    return forces


def walk_branch(branch, speed, deadline, max_lateral, goal_radius, thermal=None, temperature_history=None,
                speed_policy=None, position_speed_policy=None):
    terrain = branch.terrain
    initial_height = float(terrain.height(0, 0)) + STANCE_HEIGHT
    initial_feet = branch_feet(branch, 0)
    initial_joints = local_joint_targets(initial_feet - [0, 0, initial_height])
    landed, lift_off, touchdown = (initial_feet.copy() for _ in range(3))
    airborne = np.zeros(6, dtype=bool)
    jacobian = np.zeros((3, 24))
    foot_ids = None
    mass = None

    def control(time, model, data):
        nonlocal foot_ids, mass
        if foot_ids is None:
            foot_ids = np.array([model.geom(f"{leg}_foot").id for leg in LEG_NAMES])
            mass = float(model.body_mass.sum())
        command_speed = speed if speed_policy is None else speed_policy(time, speed, thermal)
        base = data.qpos[:3]
        if position_speed_policy is not None:
            command_speed = position_speed_policy(time, float(base[0]), command_speed)
        rotation = data.xmat[1].reshape(3, 3)
        arc = np.interp(base[0], branch.x, branch.arc)
        x, y, yaw = branch.pose(arc + command_speed * 0.45)
        yaw *= 0.65
        desired = np.array([x, y, float(terrain.height(x, y)) + STANCE_HEIGHT])
        cycles = time / WALK_PERIOD - PHASES
        progress = (cycles - np.floor(cycles)) / SWING_FRACTION
        swinging = (time > 0) & (cycles >= 0) & (progress < 1)
        starting = swinging & ~airborne
        if starting.any():
            lift_off[starting] = data.geom_xpos[foot_ids[starting]]
            touchdown[starting] = branch_feet(branch, arc + command_speed * WALK_PERIOD * 0.55)[starting]
        finishing = airborne & ~swinging
        landed[finishing] = touchdown[finishing]
        airborne[:] = swinging
        feet = landed.copy()
        blend = smoothstep(progress[swinging])[:, None]
        feet[swinging] = lift_off[swinging] + blend * (touchdown[swinging] - lift_off[swinging])
        feet[swinging, 2] += SWING_LIFT * np.sin(np.pi * progress[swinging])**2

        target = local_joint_targets((feet - base) @ rotation)
        torques = joint_pd(target, data)
        torques.reshape(6, 3)[~swinging] *= 0.12
        feet_xyz = data.geom_xpos[foot_ids]
        supported = ~swinging & (feet_xyz[:, 2] - terrain.foot_height(feet_xyz[:, 0], feet_xyz[:, 1]) < 0.024)
        if supported.sum() < 3:
            return torques

        drive = command_speed * np.array([np.cos(yaw), np.sin(yaw)]) if time > 0 else np.zeros(2)
        desired[:2] = [x, y] if time > 0 else [0, 0]
        force = np.array([350.0, 550.0, 1600.0]) * (desired - base)
        force += np.array([240.0, 350.0, 580.0]) * (np.r_[drive, 0.0] - data.qvel[:3])
        force[2] += mass * 9.81
        force[2] = np.clip(force[2], 0, 1.3 * mass * 9.81)
        world_angular_velocity = rotation @ data.qvel[3:6]
        yaw_error = np.arctan2(np.sin(yaw - np.arctan2(rotation[1, 0], rotation[0, 0])),
                               np.cos(yaw - np.arctan2(rotation[1, 0], rotation[0, 0])))
        moment = np.array([800.0 * rotation[1, 2], -800.0 * rotation[0, 2], 390.0 * yaw_error])
        moment -= np.array([185.0, 185.0, 130.0]) * world_angular_velocity
        indices = np.flatnonzero(supported)
        forces = stance_forces(feet_xyz[indices], data.subtree_com[1], force, moment)
        for leg, ground_force in zip(indices, forces, strict=True):
            mujoco.mj_jacGeom(model, data, jacobian, None, int(foot_ids[leg]))
            joint = slice(3 * leg, 3 * leg + 3)
            torques[joint] -= jacobian[:, 6 + joint.start:6 + joint.stop].T @ ground_force
        return torques

    def route_status(xy):
        return abs(branch.lateral_error(xy)), np.hypot(xy[0] - terrain.goal_x, xy[1]) <= goal_radius

    return run_walk(terrain, initial_joints, [0, 0, initial_height + 0.004], control, route_status,
                    deadline, max_lateral, thermal, temperature_history)
