"""
Hexapod Robot Articulation Configuration for NVIDIA Isaac Lab
=============================================================
Single-file drop-in articulation configuration for importing the 18-DOF Hexapod into Isaac Lab.

Usage in Isaac Lab:
    from hexapod_cfg import HEXAPOD_CFG
"""

import os
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg

# Asset directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
USD_PATH = os.path.join(CURRENT_DIR, "hexapod.usd")
URDF_PATH = os.path.join(CURRENT_DIR, "hexapod.urdf")

HEXAPOD_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=USD_PATH if os.path.exists(USD_PATH) else URDF_PATH,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=8,
            solver_velocity_iteration_count=2,
            sleep_threshold=0.005,
            stabilization_threshold=0.001,
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        # Spawn at standing height above ground (meters)
        pos=(0.0, 0.0, 0.65),
        rot=(1.0, 0.0, 0.0, 0.0),  # (w, x, y, z)
        joint_pos={
            # Hip Yaw (abduction/adduction): neutral 0 rad
            ".*_hip_joint": 0.0,
            # Femur Pitch (thigh elevation): 0.45 rad (~26 deg)
            ".*_femur_joint": 0.45,
            # Tibia Pitch (knee flexion): -0.90 rad (~ -51 deg)
            ".*_tibia_joint": -0.90,
        },
        joint_vel={".*": 0.0},
    ),
    actuators={
        "legs": ImplicitActuatorCfg(
            joint_names_expr=[".*_hip_joint", ".*_femur_joint", ".*_tibia_joint"],
            effort_limit=60.0,        # RS04 peak torque: 60 N*m
            velocity_limit=20.0,      # Max velocity: 20 rad/s
            stiffness={
                ".*_hip_joint": 100.0,
                ".*_femur_joint": 120.0,
                ".*_tibia_joint": 120.0,
            },
            damping={
                ".*_hip_joint": 3.0,
                ".*_femur_joint": 4.0,
                ".*_tibia_joint": 4.0,
            },
            friction={".*": 0.1},
        ),
    },
    soft_joint_pos_limit_factor=0.90,
)
