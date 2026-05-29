import unittest

import recoil
import simulation


class TestRoundRecoil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()
        cls.gun = recoil.WEAPONS["9x19mm Parabellum"][2]  # Glock 17, capacity 17
        cls.ammo = recoil.AMMO["9x19mm Parabellum"][0]

    def test_fewer_rounds_means_more_free_recoil_energy(self):
        full = simulation.round_recoil_data(self.gun, self.ammo, 17)
        nearly_empty = simulation.round_recoil_data(self.gun, self.ammo, 1)
        self.assertLess(full["system_mass_kg"], nearly_empty["system_mass_kg"] + 1)
        self.assertGreater(
            nearly_empty["free_recoil_energy"], full["free_recoil_energy"]
        )

    def test_ejecta_momentum_is_independent_of_round_count(self):
        full = simulation.round_recoil_data(self.gun, self.ammo, 17)
        nearly_empty = simulation.round_recoil_data(self.gun, self.ammo, 1)
        self.assertAlmostEqual(
            full["ejecta_momentum"], nearly_empty["ejecta_momentum"], places=9
        )

    def test_full_magazine_matches_recoil_full_configuration(self):
        ref = recoil.calculate_free_recoil(self.gun, self.ammo, "full")
        got = simulation.round_recoil_data(self.gun, self.ammo, self.gun["capacity"])
        self.assertAlmostEqual(got["system_mass_kg"], ref["system_mass_kg"], places=9)
        self.assertAlmostEqual(
            got["free_recoil_energy"], ref["free_recoil_energy"], places=9
        )

    def test_empty_magazine_matches_recoil_empty_configuration(self):
        ref = recoil.calculate_free_recoil(self.gun, self.ammo, "empty")
        got = simulation.round_recoil_data(self.gun, self.ammo, 0)
        self.assertAlmostEqual(got["system_mass_kg"], ref["system_mass_kg"], places=9)
        self.assertAlmostEqual(
            got["free_recoil_energy"], ref["free_recoil_energy"], places=9
        )
