"""Estimate per-motor heat during a junction pause and forecast the complete walk."""

from dataclasses import dataclass
from math import exp, expm1
from types import SimpleNamespace

import numpy as np

from .reactive_forecast import ProgressForecast
from .route_speed_study import SpeedSchedule
from .speed_policy import ThermalSlowdown
from .thermal import ThermalState
from .walking import SAMPLE_SECONDS, STAND_SECONDS


def equivalent_squared_torque(before, after, duration_s, settings):
    """Solve the first-order thermal model for constant equivalent squared torque."""
    change_weight = -expm1(-duration_s / settings.time_constant_s)
    equilibrium = before + (after - before) / change_weight
    return (equilibrium - settings.ambient_c) * settings.reference_torque_nm ** 2 / settings.rise_at_reference_c


@dataclass(frozen=True)
class PausePrediction:
    peak_c: float
    elapsed_s: float
    junction_entry_peak_c: float | None
    pause_exit_peak_c: float | None


class PauseForecast(ProgressForecast):
    def __init__(self, network, profiles, settings, spec, goal_radius, hold_squared_torque):
        super().__init__(network, profiles, settings, spec, goal_radius)
        self.duration_s = spec["pause_s"]
        self.hold_squared_torque = np.asarray(hold_squared_torque)
        if (len(self.junctions) != 3 or self.duration_s <= 0
                or np.any(self.hold_squared_torque < 0) or not np.isfinite(self.hold_squared_torque).all()):
            raise ValueError("Expected two stages, a positive pause and finite nonnegative motor loads")

    def predict_pause(self, schedule, initial):
        responses = tuple(self.responses[action.edge] for action in schedule)
        planned = SpeedSchedule(self.junctions[1:-1], tuple(action.fraction for action in schedule),
                                self.transition_s)
        reactive = ThermalSlowdown(**self.reactive)
        thermal = ThermalState(self.settings, initial)
        first = responses[0].slow if schedule[0].fraction == self.slow_fraction else responses[0].fast
        for torque in first.stand_torque:
            thermal.advance(torque, SAMPLE_SECONDS)
        state = SimpleNamespace(temperature_c=thermal.temperature_c)
        peak = float(thermal.peak_by_joint_c.max())
        position = time = 0.0
        remaining = self.duration_s
        entry_peak = exit_peak = None
        while position < self.goal_x:
            speed = min(planned(time, position, 1.0), reactive(time, 1.0, state))
            holding = planned.stage == 1 and remaining > 0
            if holding:
                if entry_peak is None:
                    entry_peak = float(state.temperature_c.max())
                duration = min(self.step, remaining)
                remaining -= duration
                load = self.hold_squared_torque
            else:
                blend = (speed - self.slow_fraction) / self.speed_span
                rate, load = responses[planned.stage].at(position - self.junctions[planned.stage], blend)
                duration = min(self.step, (self.goal_x - position) / rate)
                position = min(self.goal_x, position + rate * duration) if duration == self.step else self.goal_x
            decay = self._decay if duration == self.step else exp(-duration / self.settings.time_constant_s)
            equilibrium = self.settings.ambient_c + self._heat_factor * load
            state.temperature_c = equilibrium + (state.temperature_c - equilibrium) * decay
            current_peak = float(state.temperature_c.max())
            peak = max(peak, current_peak)
            if holding and remaining == 0:
                exit_peak = current_peak
            time += duration
        return PausePrediction(peak, STAND_SECONDS + time, entry_peak, exit_peak)
