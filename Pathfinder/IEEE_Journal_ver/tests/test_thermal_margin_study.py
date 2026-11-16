import unittest

from thermal_pathfinder.margin_analysis import admitted, margin_counts


class ThermalMarginTests(unittest.TestCase):
    def test_admission_is_strict_at_margin_boundary(self):
        plan = {"predicted_peak_c": 69.25, "thermal_limit_c": 70}
        self.assertTrue(admitted(plan, 0.5))
        self.assertFalse(admitted(plan, 0.75))
        self.assertFalse(admitted(plan | {"predicted_peak_c": None}, 0))

    def test_finishable_rejections_and_heat_stops_have_separate_counts(self):
        plans = [
            {"execution": "hot", "predicted_peak_c": 69.8, "thermal_limit_c": 70},
            {"execution": "finish", "predicted_peak_c": 69.4, "thermal_limit_c": 70},
            {"execution": "cool", "predicted_peak_c": 68.9, "thermal_limit_c": 70},
            {"execution": None, "predicted_peak_c": None, "thermal_limit_c": 70},
        ]
        runs = {
            "hot": {"completed": False, "failure": "thermal_limit"},
            "finish": {"completed": True, "failure": None},
            "cool": {"completed": True, "failure": None},
        }
        self.assertEqual(margin_counts(plans, runs, 0), {
            "scheduled": 4, "admitted": 3, "completed": 2, "thermal_stops": 1,
            "other_failures": 0, "finishable_plans_rejected": 0,
        })
        self.assertEqual(margin_counts(plans, runs, 0.75), {
            "scheduled": 4, "admitted": 1, "completed": 1, "thermal_stops": 0,
            "other_failures": 0, "finishable_plans_rejected": 1,
        })


if __name__ == "__main__":
    unittest.main()
