import math
import unittest

import recoil


class TestFreeRecoil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()

    def test_free_recoil_uses_momentum_identity(self):
        gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        ammo = recoil.AMMO["9x19mm Parabellum"][0]
        result = recoil.calculate_free_recoil(gun, ammo, "full")
        system_mass = result["system_mass_kg"]
        expected_energy = result["ejecta_momentum"] ** 2 / (2 * system_mass)
        self.assertAlmostEqual(result["free_recoil_energy"], expected_energy, places=6)

    def test_loaded_magazine_reduces_free_recoil_energy(self):
        gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        ammo = recoil.AMMO["9x19mm Parabellum"][0]
        full_mag = recoil.calculate_free_recoil(gun, ammo, "full")
        empty_mag = recoil.calculate_free_recoil(gun, ammo, "empty")
        self.assertLess(full_mag["free_recoil_energy"], empty_mag["free_recoil_energy"])

    def test_invalid_action_type_raises_clear_error(self):
        gun = recoil.WEAPONS["9x19mm Parabellum"][0].copy()
        gun["action_type"] = "invalid_action"
        ammo = recoil.AMMO["9x19mm Parabellum"][0]
        with self.assertRaises(ValueError) as context:
            recoil.calculate_free_recoil(gun, ammo, "full")
        self.assertIn("action_type", str(context.exception))
        self.assertIn("invalid_action", str(context.exception))
