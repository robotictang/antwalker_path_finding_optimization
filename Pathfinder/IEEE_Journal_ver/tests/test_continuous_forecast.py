import unittest

from thermal_pathfinder.continuous_forecast import paired_error_metrics, screen


class ContinuousForecastTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"branch_predicted_peak_c": 69.6, "continuous_predicted_peak_c": 69.8,
             "observed_peak_c": 69.8, "outcome": "completed", "limit_c": 70},
            {"branch_predicted_peak_c": 69.6, "continuous_predicted_peak_c": 70.2,
             "observed_peak_c": 70.01, "outcome": "thermal_limit", "limit_c": 70},
            {"branch_predicted_peak_c": 68.0, "continuous_predicted_peak_c": None,
             "observed_peak_c": 68.2, "outcome": "completed", "limit_c": 70},
        ]

    def test_peak_metrics_use_only_paired_finishes(self):
        result = paired_error_metrics(self.rows)
        self.assertEqual(result["paired_finishes"], 1)
        self.assertAlmostEqual(result["branch"]["mean_absolute_error_c"], 0.2)
        self.assertEqual(result["continuous"]["mean_absolute_error_c"], 0)
        self.assertEqual(result["continuous_closer"], 1)

    def test_screen_counts_stops_and_missing_forecasts(self):
        result = screen(self.rows, [0, 0.5])
        self.assertEqual(result["branch"][0]["thermal_stops"], 1)
        self.assertEqual(result["continuous"][0]["thermal_stops"], 0)
        self.assertEqual(result["continuous"][0]["no_forecast"], 1)
        self.assertEqual(result["continuous"][0]["finishable_rejected"], 1)
        self.assertEqual(result["continuous"][1]["completed"], 0)


if __name__ == "__main__":
    unittest.main()
