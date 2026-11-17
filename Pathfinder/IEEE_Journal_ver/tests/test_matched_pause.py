import unittest
from types import SimpleNamespace

import numpy as np

from thermal_pathfinder.fan_network import FanEdge
from thermal_pathfinder.matched_pause import forecast_paused, select
from thermal_pathfinder.published_speed_baseline import controller, forecast
from thermal_pathfinder.reactive_forecast import ProgressForecast, ProgressProfile
from thermal_pathfinder.route_speed_study import SpeedAction
from thermal_pathfinder.thermal import ThermalSettings


class MatchedPauseTests(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "pause_s": 12.0, "planning_budget_s": 2.0, "forecast_step_s": .5, "transition_s": 2.0,
            "reactive": {"speed_fraction": .65}, "speed_fractions": [1.0, .65],
        }
        self.settings = ThermalSettings(25, 67, 70, 120, 45, 55, .75)
        self.route = (FanEdge(0, 0), FanEdge(1, 0))
        profile = ProgressProfile(1.0, np.array([1.0]), np.array([[0.0]]), np.empty((0, 1)))
        profiles = {SpeedAction(edge, speed): profile for edge in self.route for speed in (1.0, .65)}
        network = SimpleNamespace(junctions=[0.0, 5.0, 10.0])
        self.predictor = ProgressForecast(network, profiles, self.settings, self.spec, .5)
        self.initial = np.array([60.0])
        self.ceiling = 69.5
        self.hold_load = np.array([400.0])

    def test_pause_applies_hold_heat_without_resetting_the_clock(self):
        without = controller(self.predictor, self.route, self.ceiling)
        with_pause = controller(self.predictor, self.route, self.ceiling)
        arrival, peak = forecast(self.predictor, without, self.initial)
        junction = {}
        paused_arrival, paused_peak = forecast_paused(
            self.predictor, with_pause, self.initial, self.spec["pause_s"], self.hold_load, junction
        )
        self.assertEqual(arrival + 12.0, paused_arrival)
        self.assertEqual(peak, paused_peak)
        self.assertEqual(without.junction_events, with_pause.junction_events)
        self.assertEqual(without.updates + 24, with_pause.updates)
        self.assertAlmostEqual(
            self.settings.advance(junction["entry_peak_c"], np.sqrt(self.hold_load), 12.0)[0],
            junction["exit_peak_c"],
        )

    def test_same_rank_keeps_an_equivalent_faster_zero_pause(self):
        zero, enabled = select((self.route,), self.initial, self.predictor, 100.0, self.ceiling,
                               self.spec, self.hold_load)
        self.assertEqual(zero["selected"], enabled["selected"])
        self.assertEqual(zero["candidates"], enabled["candidates"][:1])
        self.assertEqual(len(enabled["candidates"]), 2)
