import unittest
from types import SimpleNamespace

import numpy as np

from thermal_pathfinder.fan_network import FanEdge
from thermal_pathfinder.reactive_forecast import ProgressForecast, ProgressProfile
from thermal_pathfinder.route_speed_study import SpeedAction
from thermal_pathfinder.thermal import ThermalSettings
from thermal_pathfinder.walking import STAND_SECONDS


class ReactiveForecastTests(unittest.TestCase):
    def make_predictor(self, load=0.0):
        fast = ProgressProfile(1.0, np.array([1.0]), np.array([[load]]), np.empty((0, 1)))
        slow = ProgressProfile(1.0, np.array([0.65]), np.array([[load]]), np.empty((0, 1)))
        edges = (FanEdge(0, 0), FanEdge(1, 0))
        schedule = tuple(SpeedAction(edge, 1.0) for edge in edges)
        profiles = {SpeedAction(edge, fraction): profile for edge in edges
                    for fraction, profile in ((1.0, fast), (0.65, slow))}
        spec = {
            "forecast_step_s": 0.5, "transition_s": 2, "speed_fractions": [1.0, 0.65],
            "reactive": {"trigger_c": 67, "resume_c": 65.5, "speed_fraction": 0.65, "ramp_s": 2},
        }
        network = SimpleNamespace(junctions=[0.0, 5.0, 10.0])
        settings = ThermalSettings(25, 67, 70, 120, 45, 1, 0.75)
        return ProgressForecast(network, profiles, settings, spec, 0.5), schedule

    def test_hot_start_slows_and_carries_state_across_junction(self):
        predictor, schedule = self.make_predictor()
        nominal = predictor.predict(schedule, np.array([68.0]), False)
        adaptive = predictor.predict(schedule, np.array([68.0]), True)
        self.assertAlmostEqual(nominal.elapsed_s, STAND_SECONDS + 9.5)
        self.assertEqual(adaptive.first_trigger_s, 0.5)
        self.assertIsInstance(adaptive.elapsed_s, float)
        self.assertGreater(adaptive.elapsed_s, nominal.elapsed_s)
        self.assertEqual(adaptive.peak_c, 68.0)

    def test_below_trigger_both_forecasts_agree(self):
        predictor, schedule = self.make_predictor(load=0.5)
        initial = np.array([45.0])
        self.assertEqual(predictor.predict(schedule, initial, True),
                         predictor.predict(schedule, initial, False))
