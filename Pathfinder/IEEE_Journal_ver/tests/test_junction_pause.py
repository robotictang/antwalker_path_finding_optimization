import unittest

from thermal_pathfinder.junction_pause import JunctionPause


class JunctionPauseTests(unittest.TestCase):
    def test_zero_duration_leaves_speed_and_events_unchanged(self):
        pause = JunctionPause(10.0, 0.0)
        self.assertEqual(pause(5.0, 11.0, 0.12), 0.12)
        self.assertIsNone(pause.started_s)
        self.assertIsNone(pause.resumed_s)

    def test_pause_continues_after_position_falls_back_and_only_triggers_once(self):
        pause = JunctionPause(10.0, 6.0)
        self.assertEqual(pause(19.0, 9.9, 0.10), 0.10)
        self.assertEqual(pause(20.0, 10.0, 0.10), 0.0)
        self.assertEqual(pause(25.999, 9.9, 0.08), 0.0)
        self.assertEqual(pause(26.0, 10.0, 0.08), 0.08)
        self.assertEqual(pause(29.0, 10.5, 0.10), 0.10)
        self.assertEqual((pause.started_s, pause.resumed_s), (20.0, 26.0))
