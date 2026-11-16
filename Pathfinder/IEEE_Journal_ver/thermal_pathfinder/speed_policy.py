"""A reactive speed controller driven by the hottest motor."""

from dataclasses import dataclass, field
from math import isfinite


@dataclass
class ThermalSlowdown:
    trigger_c: float
    resume_c: float
    speed_fraction: float
    ramp_s: float
    active: bool = field(init=False, default=False)
    fraction: float = field(init=False, default=1.0)
    previous_s: float = field(init=False, default=0.0)
    events: list = field(init=False, default_factory=list)
    slow_seconds: float = field(init=False, default=0.0)

    def __post_init__(self):
        if not (all(isfinite(value) for value in (self.resume_c, self.trigger_c, self.speed_fraction, self.ramp_s))
                and self.resume_c < self.trigger_c and 0 < self.speed_fraction < 1 and self.ramp_s > 0):
            raise ValueError("Invalid slowdown thresholds, speed fraction or ramp duration")

    def __call__(self, time, speed, thermal):
        if time <= 0:
            return speed
        dt = time - self.previous_s
        self.previous_s = time
        if self.fraction < 1:
            self.slow_seconds += dt
        hottest = float(thermal.temperature_c.max())
        active = hottest > self.resume_c if self.active else hottest >= self.trigger_c
        if active != self.active:
            self.events.append({"walking_time_s": time, "hottest_c": hottest, "slowdown_active": active})
            self.active = active
        target = self.speed_fraction if self.active else 1.0
        increment = (1.0 - self.speed_fraction) * dt / self.ramp_s
        self.fraction = max(self.fraction - increment, min(target, self.fraction + increment))
        return speed * self.fraction
