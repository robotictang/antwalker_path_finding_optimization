import unittest

from thermal_pathfinder.reactive_margin import Margins, Observation, calibrate


class ReactiveMarginTests(unittest.TestCase):
    def test_temperature_is_strict_and_deadline_includes_boundary(self):
        margins = Margins(0.5, 3)
        self.assertFalse(margins.admits(69.5, 97, 70, 100))
        self.assertTrue(margins.admits(69.49, 97, 70, 100))
        self.assertFalse(margins.admits(69.49, 97.01, 70, 100))

    def test_deadline_gate_cannot_hide_a_leaking_temperature_margin(self):
        rows = [
            Observation("map", "stop", 69.95, 103, 70, 100, "thermal_limit"),
            Observation("map", "late", 69.2, 99.5, 70, 100, "deadline"),
            Observation("map", "finish", 69.8, 97.5, 70, 100, "completed"),
        ]
        chosen, sweep = calibrate(rows, {"temperature_grid_c": [0, 0.10, 0.5],
                                         "deadline_grid_s": [0, 1, 2, 3]})
        self.assertEqual(chosen["margins"], {"temperature_c": 0.10, "deadline_s": 2})
        first_safe_in_time = next(item for item in sweep if item["margins"] == {"temperature_c": 0, "deadline_s": 2})
        self.assertFalse(first_safe_in_time["feasible"])
        self.assertEqual(first_safe_in_time["thermal_stops_passing_temperature_gate"], 1)
