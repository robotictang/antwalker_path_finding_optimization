from types import SimpleNamespace
import unittest

import numpy as np

from thermal_pathfinder.network import Edge
from thermal_pathfinder.network_planning import EdgeThermalModel, thermal_route
from thermal_pathfinder.route_speed_study import SpeedAction, SpeedSchedule, action_graph
from thermal_pathfinder.thermal import ThermalSettings


class RouteSpeedStudyTests(unittest.TestCase):
    def test_schedule_ramps_at_junction_and_does_not_revert_on_backtrack(self):
        policy = SpeedSchedule((16.0, 32.0), (1.0, 0.65, 0.8), 2.0)
        self.assertEqual(policy(1.0, 15.9, 1.0), 1.0)
        self.assertAlmostEqual(policy(1.2, 16.01, 1.0), 0.9)
        self.assertAlmostEqual(policy(2.0, 15.9, 1.0), 0.65)
        self.assertAlmostEqual(policy(2.2, 32.01, 1.0), 0.75)
        self.assertAlmostEqual(policy(2.4, 32.1, 1.0), 0.8)
        self.assertEqual([event["stage"] for event in policy.events], [2, 3])

    def test_joint_search_can_use_speed_action_unavailable_to_fixed_speed_search(self):
        left, right, next_edge = Edge(0, 1), Edge(0, -1), Edge(1, 1)
        network = SimpleNamespace(edges={0: (left, right), 1: (next_edge,)})
        settings = ThermalSettings(25, 67, 70, 100, 60, 55, 0.75)

        def profile(elapsed, torque):
            walk = SimpleNamespace(completed=True, elapsed_s=elapsed,
                                   torques=np.full((int(elapsed / 0.02), 1), torque))
            return EdgeThermalModel.from_walk(walk, settings)

        fast, alternate, slow, finish = (
            SpeedAction(left, 1), SpeedAction(right, 1), SpeedAction(left, 0.65), SpeedAction(next_edge, 1)
        )
        actions = {fast: profile(2, 150), alternate: profile(2, 140),
                   slow: profile(3, 10), finish: profile(1, 10)}
        start = np.array([66.0])
        fixed = {action: model for action, model in actions.items() if action.fraction == 1}
        self.assertIsNone(thermal_route(action_graph(network, fixed), fixed, start, 70, 5))
        result = thermal_route(action_graph(network, actions, (left, next_edge)), actions, start, 70, 5)
        self.assertEqual(result.edges, (slow, finish))
        self.assertIsNone(thermal_route(action_graph(network, actions), actions, start, 70, 3))


if __name__ == "__main__":
    unittest.main()
