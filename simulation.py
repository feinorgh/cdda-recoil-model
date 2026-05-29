"""Simulates strings of shots using the recoil model and shooter behaviour."""

import random

import recoil


def round_recoil_data(gun, ammo, rounds):
    """Free-recoil data for a magazine currently holding `rounds` cartridges.

    Ejecta momentum is independent of the system mass, so it is taken from a
    single full-magazine calculation; only the system mass (and therefore the
    free-recoil energy) changes as the magazine depletes.
    """
    base = recoil.calculate_free_recoil(gun, ammo, "full")
    gun_data = recoil.get_gun_defaults(gun)
    ammo_mass = gun_data["mag_mass"] + rounds * ammo["cartridge_mass"]
    system_mass_kg = (gun_data["mass"] + ammo_mass) / 1000.0
    ejecta_momentum = base["ejecta_momentum"]
    return {
        "system_mass_kg": system_mass_kg,
        "ejecta_momentum": ejecta_momentum,
        "free_recoil_energy": ejecta_momentum ** 2 / (2 * system_mass_kg),
    }
