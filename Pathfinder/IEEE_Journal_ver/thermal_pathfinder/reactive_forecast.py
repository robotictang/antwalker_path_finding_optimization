"""Forecast a scheduled crawl with the same thermal slowdown used in execution."""

from dataclasses import dataclass
from math import ceil, exp
from types import SimpleNamespace

import numpy as np

from .route_speed_study import SpeedSchedule
from .speed_policy import ThermalSlowdown
from .thermal import ThermalState
from .walking import SAMPLE_SECONDS, STAND_SECONDS


@dataclass(frozen=True)
class ProgressProfile:
    bin_m: float
    velocity_m_s: np.ndarray
    mean_squared_torque: np.ndarray
    stand_torque: np.ndarray

    @classmethod
    def from_trace(cls, trace, profiled_length_m, bin_m):
        torque = trace["torque_nm"]
        stand_samples = round(STAND_SECONDS / SAMPLE_SECONDS)
        x = trace["body_xyz_m"][stand_samples:, 0]
        squared = torque[stand_samples:] ** 2
        # The standalone walk finishes within the goal radius. Its final bin
        # also supplies the short flat approach to an intermediate junction.
        edges = np.linspace(0, profiled_length_m, ceil(profiled_length_m / bin_m) + 1)
        width = float(edges[1])
        indices = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)
        counts = np.bincount(indices, minlength=len(edges) - 1)
        if np.any(counts == 0):
            raise ValueError("A completed nominal trace did not cover all progress bins")
        sums = np.zeros((len(counts), squared.shape[1]))
        np.add.at(sums, indices, squared)
        return cls(width, width / (counts * SAMPLE_SECONDS), sums / counts[:, None], torque[:stand_samples])


@dataclass(frozen=True)
class BranchResponse:
    slow: ProgressProfile
    fast: ProgressProfile

    def at(self, local_x, blend):
        index = min(int(local_x / self.slow.bin_m), len(self.slow.velocity_m_s) - 1)
        slow_rate = self.slow.velocity_m_s[index]
        rate = slow_rate + blend * (self.fast.velocity_m_s[index] - slow_rate)
        slow_load = self.slow.mean_squared_torque[index]
        load = slow_load + blend * (self.fast.mean_squared_torque[index] - slow_load)
        return float(rate), load

    def __post_init__(self):
        if (self.slow.bin_m != self.fast.bin_m
                or self.slow.velocity_m_s.shape != self.fast.velocity_m_s.shape):
            raise ValueError("The speed profiles must use a common progress grid")


@dataclass(frozen=True)
class Prediction:
    peak_c: float
    elapsed_s: float
    first_trigger_s: float | None


class ProgressForecast:
    def __init__(self, network, profiles, settings, spec, goal_radius):
        self.junctions = tuple(float(x) for x in network.junctions)
        self.goal_x = self.junctions[-1] - goal_radius
        self.settings = settings
        self.step = spec["forecast_step_s"]
        self.reactive = spec["reactive"]
        self.transition_s = spec["transition_s"]
        self.slow_fraction = self.reactive["speed_fraction"]
        self.speed_span = 1 - self.slow_fraction
        if set(spec["speed_fractions"]) != {self.slow_fraction, 1.0} or self.step <= 0:
            raise ValueError("Forecast needs both speed endpoints and a positive time step")
        by_edge = {}
        for action, profile in profiles.items():
            by_edge.setdefault(action.edge, {})[action.fraction] = profile
        self.responses = {
            edge: BranchResponse(pair[self.slow_fraction], pair[1.0])
            for edge, pair in by_edge.items() if len(pair) == 2
        }
        self._decay = exp(-self.step / settings.time_constant_s)
        self._heat_factor = settings.rise_at_reference_c / settings.reference_torque_nm ** 2

    def predict(self, schedule, initial, with_slowdown):
        responses = tuple(self.responses[action.edge] for action in schedule)
        planned = SpeedSchedule(self.junctions[1:-1], tuple(action.fraction for action in schedule),
                                self.transition_s)
        reactive = ThermalSlowdown(**self.reactive) if with_slowdown else None
        thermal = ThermalState(self.settings, initial)
        first = responses[0].slow if schedule[0].fraction == self.slow_fraction else responses[0].fast
        for torque in first.stand_torque:
            thermal.advance(torque, SAMPLE_SECONDS)
        state = SimpleNamespace(temperature_c=thermal.temperature_c)
        peak = float(thermal.peak_by_joint_c.max())
        position = time = 0.0
        while position < self.goal_x:
            speed = planned(time, position, 1.0)
            if reactive is not None:
                speed = min(speed, reactive(time, 1.0, state))
            blend = (speed - self.slow_fraction) / self.speed_span
            local_x = position - self.junctions[planned.stage]
            rate, load = responses[planned.stage].at(local_x, blend)
            duration = min(self.step, (self.goal_x - position) / rate)
            decay = self._decay if duration == self.step else exp(-duration / self.settings.time_constant_s)
            equilibrium = self.settings.ambient_c + self._heat_factor * load
            state.temperature_c = equilibrium + (state.temperature_c - equilibrium) * decay
            peak = max(peak, float(state.temperature_c.max()))
            position = min(self.goal_x, position + rate * duration) if duration == self.step else self.goal_x
            time += duration
        trigger = reactive.events[0]["walking_time_s"] if reactive is not None and reactive.events else None
        return Prediction(peak, STAND_SECONDS + time, trigger)
