from pathlib import Path
import tempfile
import unittest

import mujoco
import numpy as np

from thermal_pathfinder.benchmark import load_design, nominal_execution
from thermal_pathfinder.connected_terrain import Branch, ConnectedTerrain
from thermal_pathfinder.model import JOINT_NAMES, build_model
from thermal_pathfinder.walking import Walk


class AsymmetricBenchmarkTests(unittest.TestCase):
    def test_frozen_design_varies_heating_independently_of_cooling(self):
        config = Path(__file__).resolve().parents[1] / "experiments/asymmetric_benchmark.json"
        manifest, maps, _, settings, starts = load_design(config)
        self.assertEqual((len(maps), len(settings), len(starts)), (6, 9, 2))
        baseline = manifest["base"]["thermal"]
        baseline_rate = baseline["rise_at_reference_c"] / baseline["time_constant_s"]
        for (multiplier, tau), profile in settings.items():
            self.assertEqual(profile.time_constant_s, tau)
            self.assertAlmostEqual(profile.rise_at_reference_c / tau, baseline_rate * multiplier)
        np.testing.assert_array_equal(np.sort(starts["left_warm"]), np.sort(starts["right_warm"]))
        self.assertIn("connected_walk.py", manifest["source_sha256"])

    def test_asymmetric_mjcf_and_route_geometry_share_a_world(self):
        terrain = ConnectedTerrain(turn_length_m=6, left_bank_deg=11, right_bank_deg=6,
                                   left_offset_m=2.15, right_offset_m=1.85, right_bank_shift_m=0.4)
        left, right = [Branch(terrain, side) for side in (1, -1)]
        self.assertGreater(left.goal_arc, right.goal_arc)
        for route in (left, right):
            np.testing.assert_allclose(route.pose(route.goal_arc)[:2], [terrain.goal_x, 0], atol=1e-9)

        model = build_model(terrain)
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        geom = np.zeros(1, dtype=np.int32)
        self.assertGreater(terrain.height(7.5, 3) - terrain.height(7.5, 2),
                           terrain.height(7.5, -3) - terrain.height(7.5, -2))
        for x, y in ((7.5, 3.0), (7.5, -3.0)):
            ray = mujoco.mj_ray(model, data, np.array([x, y, 4.0]), np.array([0.0, 0.0, -1.0]),
                                None, 1, -1, geom)
            self.assertEqual(geom[0], model.geom("ground").id)
            self.assertAlmostEqual(4.0 - ray, terrain.height(x, y), places=6)

    def test_nominal_trace_reuse_stops_at_derating_threshold(self):
        config = Path(__file__).resolve().parents[1] / "experiments/asymmetric_benchmark.json"
        _, _, _, settings, _ = load_design(config)
        thermal = settings[0.55, 100]
        torques = np.zeros((1, len(JOINT_NAMES)))
        walk = Walk(False, "deadline", 0.02, 0, 0, 0, 0, 0, torques, np.zeros((1, 3)), np.array([6]), 0)
        initial = np.full(len(JOINT_NAMES), 66.0)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trace.npz"
            reused = nominal_execution(walk, thermal, initial, path)
            self.assertEqual(reused["failure"], "deadline")
            self.assertEqual(reused["execution"], "nominal_physics_reused")
            with np.load(path) as trace:
                self.assertEqual(len(trace["temperature_c"]), 2)
                np.testing.assert_array_equal(trace["temperature_c"][0], initial)
            torques[:] = 150.0
            near_derating = np.full(len(JOINT_NAMES), thermal.derate_start_c - 0.01)
            self.assertIsNone(nominal_execution(walk, thermal, near_derating, path))


if __name__ == "__main__":
    unittest.main()
