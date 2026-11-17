import unittest

from thermal_pathfinder.discordant_replays import selected_cases
from thermal_pathfinder.mission_completion import METHODS


class DiscordantReplayTests(unittest.TestCase):
    def test_selection_includes_rejections_but_excludes_agreement(self):
        plans = []
        for course, executions in (
            ("tie_success", ("finish", "finish")),
            ("tie_failure", (None, "stop")),
            ("baseline_only", ("finish", None)),
            ("per_motor_only", ("stop", "finish")),
        ):
            for method, execution in zip(METHODS, executions, strict=True):
                plans.append({
                    "method": method, "execution": execution, "map": course,
                    "setting": "slow_cooling", "start": "right_warm",
                })
        runs = {"finish": {"completed": True}, "stop": {"completed": False}}
        selected = list(selected_cases(plans, runs))
        self.assertEqual([key[0] for key, _ in selected], ["baseline_only", "per_motor_only"])
        self.assertEqual([pair[1]["execution"] for _, pair in selected], [None, "finish"])


if __name__ == "__main__":
    unittest.main()
