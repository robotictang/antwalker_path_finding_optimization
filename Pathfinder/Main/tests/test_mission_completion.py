from types import SimpleNamespace
import unittest

import numpy as np

from thermal_pathfinder.fan_network import FanEdge, FanNetwork
from thermal_pathfinder.mission_analysis import paired_result
from thermal_pathfinder.mission_completion import choose_route
from thermal_pathfinder.route_speed_study import SpeedAction


class MissionCompletionTests(unittest.TestCase):
    def test_fan_has_three_physical_choices_and_shared_landings(self):
        stage = {"turn_m": 8, "bank_m": 6, "offsets_m": [-3.2, 0, 3.2],
                 "banks_deg": [-8, 9, 8], "shifts_m": [0, 0, 0]}
        network = FanNetwork([stage], 0.12)
        routes = [network.route((edge,)) for edge in network.edges[0]]
        for route, y in zip(routes, stage["offsets_m"], strict=True):
            np.testing.assert_allclose(route.y[[0, -1]], [0, 0])
            self.assertAlmostEqual(np.interp(11, route.x, route.y), y)

    def test_anonymous_planner_is_invariant_to_warm_side(self):
        left, right = (SpeedAction(FanEdge(0, side), 1.0) for side in (0, 1))
        network = SimpleNamespace(edges={0: (left.edge, right.edge)})
        models = {
            left: SimpleNamespace(elapsed_s=1.0, propagate=lambda t: (t, float(t[0] + 3))),
            right: SimpleNamespace(elapsed_s=1.0, propagate=lambda t: (t, float(t[1] + 3))),
        }
        starts = (np.array([68, 45]), np.array([45, 68]))
        left_warm = choose_route(network, models, (starts[0],), 5, 69.5, 1)
        right_warm = choose_route(network, models, (starts[1],), 5, 69.5, 1)
        self.assertEqual(left_warm[0], (right,))
        self.assertEqual(right_warm[0], (left,))
        self.assertEqual(choose_route(network, models, starts, 5, 69.5, 1)[:3],
                         choose_route(network, models, starts[::-1], 5, 69.5, 1)[:3])
        self.assertEqual(choose_route(network, models, starts, 5, 69.5, 0)[-1], "planning_timeout")

    def test_paired_result_uses_maps(self):
        result = paired_result([([True, False], [True, True]), ([True, True], [True, True])], 10)
        self.assertEqual(result["mean_gain_pp"], 25)
        self.assertEqual(result["per_motor_only"], 1)
        self.assertEqual(result["anonymous_only"], 0)


if __name__ == "__main__":
    unittest.main()
