import unittest

import numpy as np

from thermal_pathfinder.published_speed_baseline import fastest_feasible_blend, squared_torque_budget
from thermal_pathfinder.thermal import ThermalSettings


class PublishedSpeedRuleTest(unittest.TestCase):
    def test_gait_budget_reaches_the_shared_ceiling(self):
        settings = ThermalSettings(25, 67, 70, 120, 31.68, 55, 0.75)
        temperature = np.array([47.0, 65.0, 69.2])
        ceiling, gait = 69.5, 3
        loads = squared_torque_budget(temperature, ceiling, settings, gait)
        np.testing.assert_allclose(settings.advance(temperature, np.sqrt(loads), gait), ceiling)

    def test_fastest_speed_respects_all_motor_constraints(self):
        slow, fast = np.array([2.0, 6.0]), np.array([6.0, 2.0])
        self.assertEqual(fastest_feasible_blend(slow, fast, np.array([5.0, 4.0])), 0.75)
        self.assertIsNone(fastest_feasible_blend(slow, fast, np.array([4.0, 3.0])))
        self.assertEqual(fastest_feasible_blend(slow, fast, np.array([7.0, 7.0])), 1.0)

    def test_constant_load_can_exhaust_the_budget_at_every_speed(self):
        self.assertIsNone(fastest_feasible_blend(np.array([5.0]), np.array([5.0]), np.array([4.0])))
