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

    def test_invalid_configuration_raises_clear_error(self):
        gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        ammo = recoil.AMMO["9x19mm Parabellum"][0]
        with self.assertRaises(ValueError) as context:
            recoil.calculate_free_recoil(gun, ammo, "half_full")
        self.assertIn("configuration", str(context.exception))
        self.assertIn("half_full", str(context.exception))


class TestDisturbanceModel(unittest.TestCase):
    def setUp(self):
        self.recoil_data = {
            "ejecta_momentum": 6.0,
            "free_recoil_energy": 10.0,
            "system_mass_kg": 3.5,
        }
        self.shooter = {
            "height": 1800,
            "weight": 80000,
            "strength": 6,
            "skill": 6,
            "injured_hand": False,
        }

    def test_stocked_support_reduces_aim_kick(self):
        pistol = {"type": "pistol", "support_class": "two_hand", "bore_offset": 0.05, "action_type": "locked_breech"}
        stocked = {"type": "rifle", "support_class": "stocked", "bore_offset": 0.05, "action_type": "locked_breech"}
        pistol_result = recoil.calculate_disturbance(self.shooter, pistol, self.recoil_data, "standing")
        stocked_result = recoil.calculate_disturbance(self.shooter, stocked, self.recoil_data, "standing")
        self.assertLess(stocked_result["aim_kick_rad"], pistol_result["aim_kick_rad"])

    def test_blowback_is_sharper_than_gas_for_same_impulse(self):
        blowback = {"type": "submachinegun", "support_class": "stocked", "bore_offset": 0.04, "action_type": "direct_blowback"}
        gas = {"type": "rifle", "support_class": "stocked", "bore_offset": 0.04, "action_type": "gas"}
        blowback_result = recoil.calculate_disturbance(self.shooter, blowback, self.recoil_data, "standing")
        gas_result = recoil.calculate_disturbance(self.shooter, gas, self.recoil_data, "standing")
        self.assertGreater(blowback_result["aim_kick_rad"], gas_result["aim_kick_rad"])

    def test_skill_improves_recovery_without_changing_free_recoil(self):
        novice = dict(self.shooter, skill=1)
        expert = dict(self.shooter, skill=8)
        gun = {"type": "rifle", "support_class": "stocked", "bore_offset": 0.06, "action_type": "gas"}
        novice_result = recoil.calculate_disturbance(novice, gun, self.recoil_data, "standing")
        expert_result = recoil.calculate_disturbance(expert, gun, self.recoil_data, "standing")
        self.assertLess(expert_result["recovery_seconds"], novice_result["recovery_seconds"])
