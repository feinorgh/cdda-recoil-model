import os
import tempfile
import unittest

import recoil
import examples


class TestExampleOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()
        cls.gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        cls.ammo = recoil.AMMO["9x19mm Parabellum"][0]
        cls.shooter = recoil.SHOOTER["Commando Cassie"]

    def test_writes_file_and_returns_link(self):
        with tempfile.TemporaryDirectory() as d:
            link = examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            self.assertTrue(link.endswith(".svg"))
            self.assertTrue(os.path.exists(os.path.join(d, os.path.basename(link))))

    def test_three_stance_colors_in_output(self):
        with tempfile.TemporaryDirectory() as d:
            link = examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            with open(os.path.join(d, os.path.basename(link))) as fp:
                svg = fp.read()
            for color in ("#c0392b", "#2471a3", "#1e8449"):
                self.assertIn(color, svg)

    def test_deterministic_output(self):
        with tempfile.TemporaryDirectory() as d:
            link = examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            path = os.path.join(d, os.path.basename(link))
            with open(path) as fp:
                first = fp.read()
            examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            with open(path) as fp:
                second = fp.read()
            self.assertEqual(first, second)
