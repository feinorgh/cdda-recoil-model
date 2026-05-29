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


class TestSimulateStringClimb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()
        cls.gun = recoil.WEAPONS["9x19mm Parabellum"][2]  # Glock 17
        cls.ammo = recoil.AMMO["9x19mm Parabellum"][0]
        cls.shooter = dict(recoil.SHOOTER["Commando Cassie"])

    def _scenario(self, time_limit_s, range_m=25, shot_count=5):
        return {
            "range_m": range_m,
            "shot_count": shot_count,
            "time_limit_s": time_limit_s,
            "stance": "standing",
            "seed": 1,
        }

    def test_returns_one_shot_per_round(self):
        shots = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(10),
            flinch=False, scatter=False,
        )
        self.assertEqual(len(shots), 5)
        self.assertEqual([s["shot_index"] for s in shots], [0, 1, 2, 3, 4])

    def test_first_shot_is_on_point_of_aim_without_flinch_or_scatter(self):
        shots = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(10),
            flinch=False, scatter=False,
        )
        self.assertAlmostEqual(shots[0]["x_cm"], 0.0, places=6)
        self.assertAlmostEqual(shots[0]["y_cm"], 0.0, places=6)

    def test_rapid_fire_walks_up_more_than_slow_fire(self):
        slow = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(50),
            flinch=False, scatter=False,
        )
        rapid = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(2),
            flinch=False, scatter=False,
        )
        slow_walk = slow[-1]["y_cm"] - slow[0]["y_cm"]
        rapid_walk = rapid[-1]["y_cm"] - rapid[0]["y_cm"]
        self.assertGreater(rapid_walk, slow_walk)
        self.assertGreater(rapid_walk, 0.0)

    def test_longer_range_scales_offsets_linearly(self):
        near = simulation.simulate_string(
            self.gun, self.ammo, self.shooter,
            self._scenario(2, range_m=10), flinch=False, scatter=False,
        )
        far = simulation.simulate_string(
            self.gun, self.ammo, self.shooter,
            self._scenario(2, range_m=20), flinch=False, scatter=False,
        )
        # Same angles, double the range -> double the linear offset.
        self.assertAlmostEqual(far[-1]["y_cm"], near[-1]["y_cm"] * 2, places=4)

    def test_deterministic_with_seed(self):
        a = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(2)
        )
        b = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(2)
        )
        self.assertEqual(a, b)
