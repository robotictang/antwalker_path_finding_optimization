import unittest

import mujoco
import numpy as np

from thermal_pathfinder.connected_terrain import Branch, ConnectedTerrain
from thermal_pathfinder.model import build_model


class ConnectedTerrainTests(unittest.TestCase):
    def test_branches_share_endpoints_and_diverge_around_divider(self):
        terrain = ConnectedTerrain(turn_length_m=6)
        left, right = (Branch(terrain, side) for side in (1, -1))
        np.testing.assert_allclose(left.pose(0)[:2], [0, 0])
        np.testing.assert_allclose(right.pose(0)[:2], [0, 0])
        np.testing.assert_allclose(left.pose(left.goal_arc)[:2], [terrain.goal_x, 0], atol=1e-9)
        np.testing.assert_allclose(right.pose(right.goal_arc)[:2], [terrain.goal_x, 0], atol=1e-9)
        np.testing.assert_allclose(left.y, -right.y)
        center = terrain.turn_length_m + terrain.bank_length_m / 2
        self.assertAlmostEqual(float(np.interp(center, left.x, left.y)), terrain.branch_offset_m)
        self.assertGreater(terrain.height(center, 3), terrain.height(center, 1))
        self.assertGreater(terrain.height(center, -3), terrain.height(center, -1))

    def test_mjcf_collision_height_agrees_with_controller_surface(self):
        terrain = ConnectedTerrain(turn_length_m=6)
        model = build_model(terrain)
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        geom = np.zeros(1, dtype=np.int32)
        center = terrain.turn_length_m + terrain.bank_length_m / 2
        for x, y in ((2.0, 2.0), (center, 1.0), (center, 3.0), (center, -3.0), (terrain.goal_x, 2.0)):
            ray = mujoco.mj_ray(model, data, np.array([x, y, 4.0]), np.array([0.0, 0.0, -1.0]),
                                None, 1, -1, geom)
            self.assertEqual(geom[0], model.geom("ground").id)
            self.assertAlmostEqual(4.0 - ray, terrain.height(x, y), places=6)
