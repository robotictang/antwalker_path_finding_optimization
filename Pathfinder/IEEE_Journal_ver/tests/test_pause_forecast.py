import unittest
from types import SimpleNamespace

import numpy as np

from thermal_pathfinder.fan_network import FanEdge
from thermal_pathfinder.pause_forecast import PauseForecast, equivalent_squared_torque
from thermal_pathfinder.reactive_forecast import ProgressProfile
from thermal_pathfinder.route_speed_study import SpeedAction
from thermal_pathfinder.thermal import ThermalSettings


class PauseForecastTests(unittest.TestCase):
    def test_inverse_thermal_model_recovers_per_motor_loads(self):
        settings = ThermalSettings(25, 67, 70, 120, 45, 55, 0.75)
        before = np.array([68, 60, 48])
        rms_torque = np.array([48, 61, 20])
        after = settings.advance(before, rms_torque, 12)
        np.testing.assert_allclose(equivalent_squared_torque(before, after, 12, settings), rms_torque ** 2)

    def test_pause_cools_motor_and_adds_time_below_trigger(self):
        settings = ThermalSettings(25, 67, 70, 120, 45, 55, 0.75)
        edge1, edge2 = (FanEdge(stage, 0) for stage in range(2))
        schedule = tuple(SpeedAction(edge, 1.0) for edge in (edge1, edge2))
        profile = ProgressProfile(1.0, np.array([1.0]), np.array([[0.0]]), np.empty((0, 1)))
        profiles = {SpeedAction(edge, speed): profile for edge in (edge1, edge2) for speed in (1.0, 0.65)}
        spec = {
            "pause_s": 12, "forecast_step_s": 0.5, "transition_s": 2, "speed_fractions": [1.0, 0.65],
            "reactive": {"trigger_c": 67, "resume_c": 65.5, "speed_fraction": 0.65, "ramp_s": 2},
        }
        network = SimpleNamespace(junctions=[0.0, 5.0, 10.0])
        model = PauseForecast(network, profiles, settings, spec, 0.5, np.array([0.0]))
        paused = model.predict_pause(schedule, np.array([60.0]))
        baseline = model.predict(schedule, np.array([60.0]), True)
        self.assertAlmostEqual(paused.elapsed_s, baseline.elapsed_s + 12)
        self.assertLess(paused.pause_exit_peak_c, paused.junction_entry_peak_c)
        self.assertAlmostEqual(paused.peak_c, 60.0)
