"""Per-joint lumped heating, cooling and torque derating for the pilot."""

from dataclasses import dataclass
from math import exp, isfinite

import numpy as np


@dataclass(frozen=True)
class ThermalSettings:
    ambient_c: float
    derate_start_c: float
    limit_c: float
    time_constant_s: float
    rise_at_reference_c: float
    reference_torque_nm: float
    torque_fraction_at_limit: float

    def __post_init__(self):
        if not all(isfinite(value) for value in vars(self).values()):
            raise ValueError("Thermal parameters must be finite")
        if not self.ambient_c < self.derate_start_c < self.limit_c:
            raise ValueError("Expected ambient < derating start < thermal limit")
        if min(self.time_constant_s, self.rise_at_reference_c, self.reference_torque_nm) <= 0:
            raise ValueError("Heating and cooling parameters must be positive")
        if not 0 < self.torque_fraction_at_limit <= 1:
            raise ValueError("Torque fraction at the limit must be in (0, 1]")

    def advance(self, temperature_c, rms_torque_nm, duration_s):
        # Exact for a constant mean squared torque over the interval.
        decay = exp(-duration_s / self.time_constant_s)
        equilibrium = self.ambient_c + self.rise_at_reference_c * (rms_torque_nm / self.reference_torque_nm)**2
        return equilibrium + (temperature_c - equilibrium) * decay


class ThermalState:
    def __init__(self, settings, initial_c):
        self.settings = settings
        self.temperature_c = np.asarray(initial_c, dtype=float).copy()
        if not self.temperature_c.size or self.temperature_c.ndim != 1 or not np.isfinite(self.temperature_c).all():
            raise ValueError("Expected a nonempty vector of finite joint temperatures")
        self.peak_by_joint_c = self.temperature_c.copy()

    @property
    def exceeded(self):
        return bool(np.any(self.temperature_c >= self.settings.limit_c))

    def torque_limits(self, nominal):
        fraction = np.clip((self.temperature_c - self.settings.derate_start_c) /
                           (self.settings.limit_c - self.settings.derate_start_c), 0, 1)
        return nominal * (1 - fraction * (1 - self.settings.torque_fraction_at_limit))

    def advance(self, rms_torque_nm, duration_s):
        self.temperature_c = self.settings.advance(self.temperature_c, rms_torque_nm, duration_s)
        np.maximum(self.peak_by_joint_c, self.temperature_c, out=self.peak_by_joint_c)
