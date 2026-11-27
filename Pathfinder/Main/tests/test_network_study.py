from types import SimpleNamespace
import unittest

import numpy as np

from thermal_pathfinder.network import Edge, RouteNetwork
from thermal_pathfinder.network_planning import EdgeThermalModel, fastest_route, thermal_route
from thermal_pathfinder.speed_policy import ThermalSlowdown
from thermal_pathfinder.thermal import ThermalSettings, ThermalState
from thermal_pathfinder.walking import SAMPLE_SECONDS


class NetworkStudyTests(unittest.TestCase):
    def test_mission_route_passes_through_every_junction(self):
        network = RouteNetwork([{"turn_length_m": 6}] * 3, 0.10)
        route = network.route((Edge(0, 1), Edge(1, -1), Edge(2, 1)))
        self.assertTrue(np.all(np.diff(route.x) > 0))
        for junction in network.junctions:
            np.testing.assert_allclose(np.interp(junction, route.x, route.y), 0)
        with self.assertRaises(ValueError):
            network.route((Edge(0, 1), Edge(2, -1)))

    def test_search_carries_temperature_and_preserves_incomparable_labels(self):
        network = SimpleNamespace(edges={i: (Edge(i, 1), Edge(i, -1)) for i in range(2)})
        walks = {edge: SimpleNamespace(completed=True, elapsed_s=1 if edge.side == 1 else 2)
                 for edges in network.edges.values() for edge in edges}
        self.assertEqual(fastest_route(network, walks, 4), (Edge(0, 1), Edge(1, 1)))
        del walks[Edge(1, -1)]
        settings = ThermalSettings(25, 67, 70, 100, 60, 55, 0.75)
        cool = SimpleNamespace(completed=True, elapsed_s=2, torques=np.zeros((100, 2)))
        heat = SimpleNamespace(completed=True, elapsed_s=1, torques=np.tile([100.0, 0], (50, 1)))
        alternate_heat = SimpleNamespace(completed=True, elapsed_s=2, torques=np.tile([0, 100.0], (100, 1)))
        profiles = {edge: EdgeThermalModel.from_walk(walk, settings) for edge, walk in (
            (Edge(0, 1), heat), (Edge(0, -1), alternate_heat), (Edge(1, 1), heat))}
        initial = np.array([67.0, 45.0])
        label = thermal_route(network, profiles, initial, 70, 4)
        self.assertEqual(label.edges, (Edge(0, -1), Edge(1, 1)))
        expected = ThermalState(settings, initial)
        for torque in np.concatenate((alternate_heat.torques, heat.torques)):
            expected.advance(torque, SAMPLE_SECONDS)
        np.testing.assert_allclose(label.terminal_c, expected.temperature_c)
        self.assertAlmostEqual(label.peak_c, expected.peak_by_joint_c.max())
        self.assertIsNone(thermal_route(network, profiles, initial, 70, 2))
        np.testing.assert_allclose(EdgeThermalModel.from_walk(cool, settings).propagate(initial)[0],
                                   settings.advance(initial, np.zeros(2), 2.0))

    def test_slowdown_hysteresis_and_slew_rate(self):
        policy = ThermalSlowdown(trigger_c=67, resume_c=65.5, speed_fraction=0.65, ramp_s=2)
        thermal = SimpleNamespace(temperature_c=np.array([68.0, 40.0]))
        self.assertAlmostEqual(policy(1, 0.12, thermal), 0.12 * 0.825)
        thermal.temperature_c[0] = 66.0
        self.assertAlmostEqual(policy(2, 0.12, thermal), 0.12 * 0.65)
        thermal.temperature_c[0] = 65.5
        self.assertAlmostEqual(policy(3, 0.12, thermal), 0.12 * 0.825)
        self.assertEqual([event["slowdown_active"] for event in policy.events], [True, False])


if __name__ == "__main__":
    unittest.main()
