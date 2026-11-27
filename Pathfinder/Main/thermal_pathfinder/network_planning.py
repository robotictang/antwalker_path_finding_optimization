"""Search a directed route network while carrying motor temperatures across edges."""

from dataclasses import dataclass

import numpy as np

from .thermal import ThermalState
from .walking import SAMPLE_SECONDS


@dataclass(frozen=True)
class EdgeThermalModel:
    elapsed_s: float
    decays: np.ndarray
    offsets_c: np.ndarray

    @classmethod
    def from_walk(cls, walk, settings):
        if not walk.completed:
            raise ValueError("Cannot profile an edge that failed the nominal walk")
        # The RC model is affine in initial temperature at every sample.
        state = ThermalState(settings, np.zeros(walk.torques.shape[1]))
        offsets = [state.temperature_c.copy()]
        for torque in walk.torques:
            state.advance(torque, SAMPLE_SECONDS)
            offsets.append(state.temperature_c.copy())
        decay = np.exp(-np.arange(len(offsets)) * SAMPLE_SECONDS / settings.time_constant_s)
        return cls(walk.elapsed_s, decay[:, None], np.asarray(offsets))

    def propagate(self, initial_c):
        temperatures = self.decays * initial_c + self.offsets_c
        return temperatures[-1], float(temperatures.max())


@dataclass
class RouteLabel:
    edges: tuple
    time_s: float
    peak_c: float
    terminal_c: np.ndarray
    junction_temperatures_c: tuple = ()


def fastest_route(network, walks, deadline):
    choices = []
    elapsed = 0.0
    for edges in network.edges.values():
        feasible = [edge for edge in edges if walks[edge].completed]
        if not feasible:
            return None
        edge = min(feasible, key=lambda e: (walks[e].elapsed_s, e.name))
        choices.append(edge)
        elapsed += walks[edge].elapsed_s
    return tuple(choices) if elapsed <= deadline else None


def dominates(left, right):
    return (left.time_s <= right.time_s and left.peak_c <= right.peak_c
            and np.all(left.terminal_c <= right.terminal_c))


def thermal_route(network, profiles, initial_c, limit_c, deadline):
    labels = [RouteLabel((), 0.0, float(initial_c.max()), initial_c)]
    for edges in network.edges.values():
        next_labels = []
        for label in labels:
            for edge in edges:
                if edge not in profiles:
                    continue
                profile = profiles[edge]
                elapsed = label.time_s + profile.elapsed_s
                if elapsed > deadline:
                    continue
                end, peak = profile.propagate(label.terminal_c)
                peak = max(peak, label.peak_c)
                if peak >= limit_c:
                    continue
                candidate = RouteLabel((*label.edges, edge), elapsed, peak, end,
                                       (*label.junction_temperatures_c, end))
                if not any(dominates(previous, candidate) for previous in next_labels):
                    next_labels = [previous for previous in next_labels if not dominates(candidate, previous)]
                    next_labels.append(candidate)
        labels = next_labels
    return min(labels, key=lambda label: (label.peak_c, label.time_s), default=None)
