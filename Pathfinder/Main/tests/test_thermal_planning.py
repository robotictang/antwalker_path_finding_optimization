import unittest
from types import SimpleNamespace

import numpy as np

from thermal_pathfinder.planning import predict_peak, rank_routes
from thermal_pathfinder.thermal import ThermalSettings, ThermalState


class ThermalPlanningTests(unittest.TestCase):
    def setUp(self):
        self.settings = ThermalSettings(25, 67, 70, 20, 60, 50, 0.75)

    def test_zero_torque_cools_toward_ambient(self):
        cooled = self.settings.advance(np.array([55.0]), np.zeros(1), 20)
        self.assertAlmostEqual(cooled[0], 25 + 30 * np.exp(-1))
        self.assertEqual(predict_peak(self.settings, np.array([55.0]), np.zeros((2, 1)), 20), 55.0)

    def test_derating_applies_to_the_hot_joint_only(self):
        state = ThermalState(self.settings, [68.5, 45])
        np.testing.assert_allclose(state.torque_limits(np.array([100, 100])), [87.5, 100])
        state.advance(np.array([120.0, 0]), 20)
        self.assertTrue(state.exceeded)
        self.assertLess(state.peak_by_joint_c[1], 46.0)

    def test_per_joint_swaps_route_but_aggregate_decisions_are_invariant(self):
        profiles = {
            "left_load": SimpleNamespace(completed=True, elapsed_s=10, torques=np.array([[55, 10]])),
            "right_load": SimpleNamespace(completed=True, elapsed_s=11, torques=np.array([[10, 55]])),
        }
        left_warm = np.array([66.0, 45.0])
        right_warm = left_warm[::-1]
        self.assertEqual(rank_routes("per_joint", self.settings, left_warm, profiles, 10)[0], "right_load")
        self.assertEqual(rank_routes("per_joint", self.settings, right_warm, profiles, 10)[0], "left_load")
        for method in ("mean_only", "maximum_only", "time_only"):
            self.assertEqual(
                rank_routes(method, self.settings, left_warm, profiles, 10),
                rank_routes(method, self.settings, right_warm, profiles, 10),
            )

    def test_failed_nominal_route_is_excluded(self):
        profiles = {"blocked": SimpleNamespace(completed=False, failure="left_corridor")}
        selected, predictions = rank_routes("time_only", self.settings, np.array([45.0]), profiles, 10)
        self.assertIsNone(selected)
        self.assertEqual(predictions["blocked"]["failure"], "left_corridor")
