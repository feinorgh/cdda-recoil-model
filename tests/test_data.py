import json
import unittest


class TestDataFiles(unittest.TestCase):
    def test_every_shooter_has_handedness(self):
        with open("shooters.json", "r") as fp:
            shooters = json.load(fp)
        self.assertTrue(shooters, "shooters.json must not be empty")
        for name, data in shooters.items():
            self.assertIn("handedness", data, f"{name} missing handedness")
            self.assertIn(data["handedness"], ("right", "left"))

    def test_scenarios_have_required_fields(self):
        with open("scenarios.json", "r") as fp:
            scenarios = json.load(fp)
        self.assertTrue(scenarios, "scenarios.json must not be empty")
        required = {
            "name", "target", "range_m", "caliber",
            "gun", "ammo", "shooter", "shot_count", "time_limit_s",
            "stance", "seed",
        }
        for scenario in scenarios:
            missing = required - set(scenario.keys())
            self.assertFalse(missing, f"{scenario.get('name')} missing {missing}")
            self.assertIn(scenario["target"], ("bullseye", "ipsc_silhouette", "popper"))
            self.assertIn(scenario["stance"], ("standing", "crouching", "prone"))
