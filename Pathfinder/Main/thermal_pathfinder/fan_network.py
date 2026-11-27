"""Connected courses with an optional middle branch between shared landings."""

from dataclasses import dataclass
from xml.etree import ElementTree as ET

import numpy as np

from .connected_terrain import smoothstep
from .model import _numbers
from .network import NetworkRoute, RouteNetwork


@dataclass(frozen=True)
class FanEdge:
    stage: int
    branch: int

    @property
    def name(self):
        return f"s{self.stage + 1}_b{self.branch + 1}"


class FanNetwork(RouteNetwork):
    def __init__(self, stages, resolution):
        self.sections = stages
        self.junctions = np.r_[0.0, np.cumsum([2 * s["turn_m"] + s["bank_m"] + 1 for s in stages])]
        self.edges = {i: tuple(FanEdge(i, j) for j in range(len(s["offsets_m"])))
                      for i, s in enumerate(stages)}
        end = float(self.junctions[-1]) + 3
        extent = max(abs(y) for s in stages for y in s["offsets_m"]) + 2
        self.x_grid = np.linspace(-2, end, round((end + 2) / resolution) + 1)
        self.y_grid = np.linspace(-extent, extent, round(2 * extent / resolution) + 1)
        x, y = np.meshgrid(self.x_grid, self.y_grid)
        self.heights = np.zeros_like(x)
        for stage, origin in zip(stages, self.junctions):
            for offset, angle, shift in zip(stage["offsets_m"], stage["banks_deg"], stage["shifts_m"], strict=True):
                dx = x - origin - shift
                start, end = stage["turn_m"], stage["turn_m"] + stage["bank_m"]
                envelope = smoothstep((dx - start + 1) / 1.5) * smoothstep((end + 1 - dx) / 1.5)
                dy = y - offset
                # The bank is planar across the foot span and tapers between branches.
                width = 1.65 if len(stage["offsets_m"]) == 3 else 2.05
                taper = smoothstep((width - np.abs(dy)) / 0.45)
                self.heights += np.tan(np.radians(angle)) * dy * taper * envelope

    def route(self, edges, *, local_start=False):
        if not edges or [edge.stage for edge in edges] != list(range(edges[0].stage, edges[-1].stage + 1)):
            raise ValueError("Expected contiguous edges")
        if any(edge not in self.edges.get(edge.stage, ()) for edge in edges) or (not local_start and edges[0].stage):
            raise ValueError("Invalid route edge or start")
        return FanRoute(self, tuple(edges))

    def add_mjcf(self, root, world, origin):
        low, high = float(self.heights.min()), float(self.heights.max())
        asset = ET.SubElement(root, "asset")
        rows, cols = self.heights.shape
        values = ((self.heights - low) / (high - low))[::-1].ravel()
        ET.SubElement(asset, "hfield", name="course", nrow=str(rows), ncol=str(cols),
                      size=_numbers((np.ptp(self.x_grid) / 2, np.ptp(self.y_grid) / 2, high - low, 0.25)),
                      elevation=_numbers(values))
        ET.SubElement(world, "geom", name="ground", type="hfield", hfield="course",
                      pos=_numbers(((self.x_grid[0] + self.x_grid[-1]) / 2 - origin, 0, low)),
                      friction="1.1 0.01 0.001", contype="1", conaffinity="2", rgba="0.60 0.66 0.60 1")
        for i, (stage, start) in enumerate(zip(self.sections, self.junctions)):
            offsets = stage["offsets_m"]
            for j, (left, right) in enumerate(zip(offsets, offsets[1:])):
                ET.SubElement(world, "geom", name=f"divider_{i}_{j}", type="box",
                              pos=_numbers((start + stage["turn_m"] + stage["bank_m"] / 2 - origin,
                                            (left + right) / 2, 0.26)),
                              size=_numbers((stage["bank_m"] / 2 - 0.5, 0.08, 0.53)),
                              contype="1", conaffinity="2", rgba="0.31 0.36 0.41 1")


class FanRoute(NetworkRoute):
    def __post_init__(self):
        x_parts, y_parts = [], []
        for index, edge in enumerate(self.edges):
            stage = self.network.sections[edge.stage]
            x = np.linspace(0, 2 * stage["turn_m"] + stage["bank_m"] + 1, 1201)
            turn = stage["turn_m"]
            entry = smoothstep(x / turn)
            exit_ = smoothstep((2 * turn + stage["bank_m"] - x) / turn)
            y = stage["offsets_m"][edge.branch] * entry * exit_
            x_parts.append((x + self.network.junctions[edge.stage] - self.origin)[bool(index):])
            y_parts.append(y[bool(index):])
        self.x = np.concatenate((*x_parts, [self.goal_x + 0.6, self.goal_x + 1.2]))
        self.y = np.concatenate((*y_parts, np.zeros(2)))
        self.arc = np.r_[0.0, np.cumsum(np.hypot(np.diff(self.x), np.diff(self.y)))]
        self.yaw = np.arctan(np.gradient(self.y, self.x))
