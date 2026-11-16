"""Build the pilot MJCF from explicitly recorded geometry and assumptions."""

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from xml.etree import ElementTree as ET

import mujoco
import numpy as np

LEG_NAMES = ("LF", "LM", "LR", "RF", "RM", "RR")
JOINT_NAMES = tuple(f"{leg}_{joint}" for leg in LEG_NAMES for joint in ("coxa", "femur", "tibia"))
HIP_POSITIONS = np.array([(x, side * 0.410, 0.0) for side in (1, -1) for x in (0.320, 0.0, -0.320)])
LINK_LENGTHS = (0.157, 0.550, 0.740)
FOOT_RADIUS = 0.055
JOINT_LIMITS = ((-0.80, 0.80), (-1.20, 1.30), (0.08, 2.45))
TORQUE_LIMITS = np.tile([90.0, 150.0, 130.0], 6)


@dataclass(frozen=True)
class Terrain:
    """A planar cross-slope, rising toward positive y for positive slope."""

    slope: float

    def foot_height(self, y):
        return self.slope * y + FOOT_RADIUS * sqrt(1 + self.slope**2)

    def add_mjcf(self, root, world):
        normal = np.array([0.0, -self.slope, 1.0])
        normal /= np.linalg.norm(normal)
        ET.SubElement(world, "geom", name="ground", type="plane", size="0 0 0.1",
                      zaxis=_numbers(normal), friction="1.1 0.01 0.001",
                      contype="1", conaffinity="2")


def _numbers(values):
    return " ".join(f"{v:.12g}" for v in values)


def build_xml(terrain):
    root = ET.Element("mujoco", model="cad_derived_hexapod_pilot")
    ET.SubElement(root, "compiler", angle="radian", autolimits="true")
    ET.SubElement(root, "option", timestep="0.002", gravity="0 0 -9.81", integrator="implicitfast", cone="elliptic")
    world = ET.SubElement(root, "worldbody")
    terrain.add_mjcf(root, world)
    base = ET.SubElement(world, "body", name="chassis")
    ET.SubElement(base, "freejoint", name="base")
    ET.SubElement(base, "geom", name="chassis_collision", type="box",
                  pos="0 0 0.025", size="0.42 0.50 0.14", mass="34",
                  contype="2", conaffinity="1", rgba="0.24 0.30 0.36 1")
    actuator = ET.SubElement(root, "actuator")
    for leg_id, (leg, hip) in enumerate(zip(LEG_NAMES, HIP_POSITIONS, strict=True)):
        side = 1 if leg_id < 3 else -1
        yaw = side * pi / 2
        parent = base
        for j, (segment, length, radius, mass) in enumerate(zip(
            ("coxa", "femur", "tibia"), LINK_LENGTHS, (0.050, 0.045, 0.042), (2.0, 3.5, 2.4), strict=True
        )):
            name = f"{leg}_{segment}"
            pos = hip if j == 0 else (LINK_LENGTHS[j - 1], 0, 0)
            body = ET.SubElement(parent, "body", name=name, pos=_numbers(pos))
            if j == 0:
                body.set("quat", _numbers((cos(yaw / 2), 0, 0, sin(yaw / 2))))
            ET.SubElement(body, "joint", name=name, axis="0 0 1" if j == 0 else "0 1 0",
                          range=_numbers(JOINT_LIMITS[j]), armature="0.07", damping="1.8")
            ET.SubElement(body, "geom", name=f"{name}_link", type="capsule",
                          fromto=_numbers((0, 0, 0, length - (0.045 if j == 2 else 0), 0, 0)),
                          size=str(radius), mass=str(mass), contype="2", conaffinity="1",
                          rgba="0.78 0.49 0.20 1" if side == 1 else "0.24 0.58 0.77 1")
            limit = TORQUE_LIMITS[3 * leg_id + j]
            ET.SubElement(actuator, "motor", name=name, joint=name, ctrlrange=_numbers((-limit, limit)))
            parent = body
        ET.SubElement(parent, "geom", name=f"{leg}_foot", type="sphere",
                      pos=_numbers((LINK_LENGTHS[2], 0, 0)), size=str(FOOT_RADIUS),
                      mass="0.10", contype="2", conaffinity="1",
                      friction="1.1 0.01 0.001", rgba="0.12 0.14 0.16 1")
    ET.indent(root)
    return ET.tostring(root, encoding="unicode")


def build_model(terrain):
    return mujoco.MjModel.from_xml_string(build_xml(terrain))
