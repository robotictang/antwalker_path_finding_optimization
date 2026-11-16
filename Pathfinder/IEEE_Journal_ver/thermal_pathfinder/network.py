"""A connected heightfield with a sequence of branching route choices."""

from dataclasses import dataclass, field
from math import radians, sqrt, tan
from xml.etree import ElementTree as ET

import numpy as np

from .connected_terrain import ConnectedTerrain, smoothstep
from .model import FOOT_RADIUS, _numbers


@dataclass(frozen=True)
class Edge:
    stage: int
    side: int

    @property
    def name(self):
        return f"s{self.stage + 1}_{'left' if self.side == 1 else 'right'}"


class RouteNetwork:
    """A directed graph of flat junctions joined by two physical branches each."""

    def __init__(self, stages, resolution_m):
        if not 0.05 <= resolution_m <= 0.25 or len(stages) < 2:
            raise ValueError("Expected two or more stages and a supported resolution")
        options = [stage | {"resolution_m": resolution_m} for stage in stages]
        self.sections = [ConnectedTerrain(**stage) for stage in options]
        self.junctions = np.r_[0.0, np.cumsum([section.goal_x for section in self.sections])]
        self.edges = {index: (Edge(index, 1), Edge(index, -1)) for index in range(len(self.sections))}
        x_extent = self.junctions[-1] + 3
        y_extent = max(float(section.y_grid[-1]) for section in self.sections)
        self.x_grid = np.linspace(-2.0, x_extent, round((x_extent + 2) / resolution_m) + 1)
        self.y_grid = np.linspace(-y_extent, y_extent, round(2 * y_extent / resolution_m) + 1)
        self.heights = np.zeros((len(self.y_grid), len(self.x_grid)))
        for index, section in enumerate(self.sections):
            origin, end = self.junctions[index:index + 2]
            cells = (self.x_grid >= origin) & (self.x_grid < end)
            x, y = np.meshgrid(self.x_grid[cells] - origin, self.y_grid)
            self.heights[:, cells] = section.height(x, y)

    def route(self, edges, *, local_start=False):
        if not edges:
            raise ValueError("A route requires at least one edge")
        stages = list(range(edges[0].stage, edges[-1].stage + 1))
        if [edge.stage for edge in edges] != stages or any(edge.side not in (-1, 1) for edge in edges):
            raise ValueError("Route edges must be contiguous")
        if not local_start and stages[0] != 0:
            raise ValueError("Mission routes must begin at the start junction")
        return NetworkRoute(self, tuple(edges))

    def add_mjcf(self, root, world, origin):
        low, high = float(self.heights.min()), float(self.heights.max())
        asset = ET.SubElement(root, "asset")
        rows, cols = self.heights.shape
        values = ((self.heights - low) / (high - low))[::-1].ravel()
        ET.SubElement(asset, "hfield", name="banks", nrow=str(rows), ncol=str(cols),
                      size=_numbers((np.ptp(self.x_grid) / 2, np.ptp(self.y_grid) / 2, high - low, 0.25)),
                      elevation=_numbers(values))
        center_x = (self.x_grid[0] + self.x_grid[-1]) / 2 - origin
        ET.SubElement(world, "geom", name="ground", type="hfield", hfield="banks",
                      pos=_numbers((center_x, 0, low)), friction="1.1 0.01 0.001",
                      contype="1", conaffinity="2", rgba="0.60 0.66 0.60 1")
        for index, section in enumerate(self.sections):
            center = self.junctions[index] + section.turn_length_m + section.bank_length_m / 2 - origin
            ET.SubElement(world, "geom", name=f"divider_{index + 1}", type="box",
                          pos=_numbers((center, 0, 0.26)),
                          size=_numbers((section.bank_length_m / 2 - 0.4, 0.17, 0.53)),
                          contype="1", conaffinity="2", rgba="0.31 0.36 0.41 1")


@dataclass
class NetworkRoute:
    network: RouteNetwork
    edges: tuple[Edge, ...]
    x: np.ndarray = field(init=False, repr=False)
    y: np.ndarray = field(init=False, repr=False)
    arc: np.ndarray = field(init=False, repr=False)
    yaw: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        parts_x, parts_y = [], []
        for index, edge in enumerate(self.edges):
            section = self.network.sections[edge.stage]
            x = np.linspace(0, section.goal_x, 1201)
            entry = smoothstep(x / section.turn_length_m)
            end = section.turn_length_m + section.bank_length_m
            exit_ = smoothstep(1 - (x - end) / section.turn_length_m)
            side_y = edge.side * section.branch_offset(edge.side) * entry * exit_
            parts_x.append((x + self.network.junctions[edge.stage] - self.origin)[bool(index):])
            parts_y.append(side_y[bool(index):])
        parts_x.append(np.array([self.goal_x + 0.6, self.goal_x + 1.2]))
        parts_y.append(np.zeros(2))
        self.x = np.concatenate(parts_x)
        self.y = np.concatenate(parts_y)
        self.arc = np.r_[0.0, np.cumsum(np.hypot(np.diff(self.x), np.diff(self.y)))]
        self.yaw = np.arctan(np.gradient(self.y, self.x))

    @property
    def terrain(self):
        return self

    @property
    def origin(self):
        return float(self.network.junctions[self.edges[0].stage])

    @property
    def goal_x(self):
        return float(self.network.junctions[self.edges[-1].stage + 1] - self.origin)

    @property
    def x_grid(self):
        return self.network.x_grid - self.origin

    @property
    def y_grid(self):
        return self.network.y_grid

    @property
    def heights(self):
        return self.network.heights

    def height(self, x, y):
        return ConnectedTerrain.height(self, x, y)

    def foot_height(self, x, y):
        return self.height(x, y) + FOOT_RADIUS * sqrt(1 + tan(radians(8))**2)

    def add_mjcf(self, root, world):
        self.network.add_mjcf(root, world, self.origin)

    def pose(self, arc):
        return np.array([np.interp(arc, self.arc, values) for values in (self.x, self.y, self.yaw)])

    def lateral_error(self, xy):
        return float(xy[1] - np.interp(xy[0], self.x, self.y))
