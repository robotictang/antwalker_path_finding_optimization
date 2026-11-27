"""One MuJoCo scene with two banked branches and common flat landings."""

from dataclasses import dataclass, field
from math import isfinite, radians, sqrt, tan
from xml.etree import ElementTree as ET

import numpy as np

from .model import FOOT_RADIUS, _numbers


def smoothstep(value):
    value = np.clip(value, 0.0, 1.0)
    return value * value * value * (10.0 + value * (-15.0 + 6.0 * value))


@dataclass
class ConnectedTerrain:
    bank_deg: float = 8.0
    branch_offset_m: float = 2.0
    turn_length_m: float = 4.0
    bank_length_m: float = 3.0
    resolution_m: float = 0.10
    left_bank_deg: float | None = None
    right_bank_deg: float | None = None
    left_offset_m: float | None = None
    right_offset_m: float | None = None
    left_bank_shift_m: float = 0.0
    right_bank_shift_m: float = 0.0
    heights: np.ndarray = field(init=False, repr=False)
    x_grid: np.ndarray = field(init=False, repr=False)
    y_grid: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        if not (0 < self.bank_deg <= 16 and self.branch_offset_m >= 1.75
                and self.turn_length_m >= 3 and self.bank_length_m >= 2
                and 0.05 <= self.resolution_m <= 0.25):
            raise ValueError("Connected terrain parameters outside the supported development range")
        x_bounds = (-2.0, self.goal_x + 3.0)
        angles = [self.bank_angle(side) for side in (1, -1)]
        offsets = [self.branch_offset(side) for side in (1, -1)]
        shifts = (self.left_bank_shift_m, self.right_bank_shift_m)
        if not (all(0 < angle <= 16 for angle in angles)
                and all(isfinite(offset) and 1.75 <= offset <= 3 for offset in offsets)
                and all(abs(shift) <= 0.75 for shift in shifts)):
            raise ValueError("Invalid branch banks, offsets or bank shifts")
        y_extent = max(offsets) + 2.1
        self.x_grid = np.linspace(*x_bounds, round((x_bounds[1] - x_bounds[0]) / self.resolution_m) + 1)
        self.y_grid = np.linspace(-y_extent, y_extent, round(2 * y_extent / self.resolution_m) + 1)
        x, y = np.meshgrid(self.x_grid, self.y_grid)
        shift = np.where(y >= 0, *shifts)
        local_x = x - shift
        fade = smoothstep((local_x - self.turn_length_m + 1) / 1.5)
        fade *= smoothstep((self.turn_length_m + self.bank_length_m + 1 - local_x) / 1.5)
        abs_y = np.abs(y)
        lateral = smoothstep((abs_y - 0.1) / 0.55)
        slope = np.where(y >= 0, *(tan(radians(angle)) for angle in angles))
        offset = np.where(y >= 0, *offsets)
        self.heights = slope * (abs_y - offset) * lateral * fade

    def bank_angle(self, side):
        angle = self.left_bank_deg if side == 1 else self.right_bank_deg
        return self.bank_deg if angle is None else angle

    def branch_offset(self, side):
        offset = self.left_offset_m if side == 1 else self.right_offset_m
        return self.branch_offset_m if offset is None else offset

    @property
    def goal_x(self):
        return 2 * self.turn_length_m + self.bank_length_m + 1.0

    @property
    def x_center(self):
        return float((self.x_grid[0] + self.x_grid[-1]) / 2)

    def height(self, x, y):
        ix = (np.asarray(x) - self.x_grid[0]) * (len(self.x_grid) - 1) / np.ptp(self.x_grid)
        iy = (np.asarray(y) - self.y_grid[0]) * (len(self.y_grid) - 1) / np.ptp(self.y_grid)
        ix = np.clip(ix, 0, len(self.x_grid) - 1)
        iy = np.clip(iy, 0, len(self.y_grid) - 1)
        i = np.minimum(ix.astype(int), len(self.x_grid) - 2)
        j = np.minimum(iy.astype(int), len(self.y_grid) - 2)
        u, v = ix - i, iy - j
        low = self.heights[j, i] * (1 - u) + self.heights[j, i + 1] * u
        high = self.heights[j + 1, i] * (1 - u) + self.heights[j + 1, i + 1] * u
        return low * (1 - v) + high * v

    def foot_height(self, x, y):
        # Approximate the vertical offset for a sphere on the bank.
        return self.height(x, y) + FOOT_RADIUS * sqrt(1 + tan(radians(self.bank_deg))**2)

    def add_mjcf(self, root, world):
        low, high = float(self.heights.min()), float(self.heights.max())
        asset = ET.SubElement(root, "asset")
        rows, cols = self.heights.shape
        # Inline MJCF elevation rows run from positive world y to negative y.
        values = ((self.heights - low) / (high - low))[::-1].ravel()
        ET.SubElement(asset, "hfield", name="connected_banks", nrow=str(rows), ncol=str(cols),
                      size=_numbers((np.ptp(self.x_grid) / 2, np.ptp(self.y_grid) / 2, high - low, 0.25)),
                      elevation=_numbers(values))
        ET.SubElement(world, "geom", name="ground", type="hfield", hfield="connected_banks",
                      pos=_numbers((self.x_center, 0, low)), friction="1.1 0.01 0.001",
                      contype="1", conaffinity="2", rgba="0.60 0.66 0.60 1")
        center = self.turn_length_m + self.bank_length_m / 2
        ET.SubElement(world, "geom", name="divider", type="box",
                      pos=_numbers((center, 0, 0.26)), size=_numbers((self.bank_length_m / 2 - 0.4, 0.17, 0.53)),
                      contype="1", conaffinity="2", rgba="0.31 0.36 0.41 1")


@dataclass
class Branch:
    terrain: ConnectedTerrain
    side: int
    x: np.ndarray = field(init=False, repr=False)
    y: np.ndarray = field(init=False, repr=False)
    arc: np.ndarray = field(init=False, repr=False)
    yaw: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        if self.side not in (-1, 1):
            raise ValueError("Branch side must be -1 or 1")
        self.x = np.linspace(0, self.terrain.goal_x + 1.2, 1201)
        entry = smoothstep(self.x / self.terrain.turn_length_m)
        end_of_bank = self.terrain.turn_length_m + self.terrain.bank_length_m
        exit_ = smoothstep(1 - (self.x - end_of_bank) / self.terrain.turn_length_m)
        self.y = self.side * self.terrain.branch_offset(self.side) * entry * exit_
        self.arc = np.r_[0.0, np.cumsum(np.hypot(np.diff(self.x), np.diff(self.y)))]
        self.yaw = np.arctan(np.gradient(self.y, self.x))

    @property
    def goal_arc(self):
        return float(np.interp(self.terrain.goal_x, self.x, self.arc))

    def pose(self, arc):
        return np.array([np.interp(arc, self.arc, values) for values in (self.x, self.y, self.yaw)])

    def lateral_error(self, xy):
        return float(xy[1] - np.interp(xy[0], self.x, self.y))
