import os
import tempfile
import unittest

import practice


class TestPractice(unittest.TestCase):
    def test_resolve_records_finds_gun_ammo_shooter(self):
        practice.load_all()
        scenario = {
            "caliber": "9x19mm Parabellum",
            "gun": "Glock 17",
            "ammo": "9x19mm 115 gr Federal FMJ",
            "shooter": "Commando Cassie",
        }
        gun, ammo, shooter = practice.resolve_records(scenario)
        self.assertEqual(gun["name"], "Glock 17")
        self.assertEqual(ammo["name"], "9x19mm 115 gr Federal FMJ")
        self.assertEqual(shooter["strength"], 6)

    def test_resolve_records_raises_on_unknown_gun(self):
        practice.load_all()
        scenario = {
            "caliber": "9x19mm Parabellum",
            "gun": "No Such Gun",
            "ammo": "9x19mm 115 gr Federal FMJ",
            "shooter": "Commando Cassie",
        }
        with self.assertRaises(ValueError) as ctx:
            practice.resolve_records(scenario)
        self.assertIn("No Such Gun", str(ctx.exception))

    def test_run_scenarios_writes_svgs_and_gallery(self):
        practice.load_all()
        with tempfile.TemporaryDirectory() as out_dir:
            count = practice.run_scenarios(practice.SCENARIOS, out_dir)
            self.assertEqual(count, len(practice.SCENARIOS))
            svgs = [f for f in os.listdir(out_dir) if f.endswith(".svg")]
            self.assertEqual(len(svgs), len(practice.SCENARIOS))
            gallery = os.path.join(out_dir, "TARGETS.md")
            self.assertTrue(os.path.exists(gallery))
            with open(gallery, "r") as fp:
                text = fp.read()
            self.assertIn("# Target Practice Gallery", text)
            for svg in svgs:
                self.assertIn(svg, text)
