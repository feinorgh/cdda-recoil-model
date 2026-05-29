"""Simulates strings of shots using the recoil model and shooter behaviour."""

import random

import recoil


# --- Behaviour tuning constants -------------------------------------------
# These are initial values. They are tuned during implementation so that a
# relaxed expert groups inside the bullseye 10-ring and shot zero sits on the
# point of aim. The TEST SUITE asserts only DIRECTIONAL/RELATIVE behaviour, so
# it remains valid as these constants are adjusted.

# Active compensation between shots: effectiveness in [0, 1] of cancelling the
# accumulated muzzle climb before the next shot.
COMP_BASE = 0.55  # baseline fraction of climb a shooter cancels
COMP_SKILL = 0.06  # additional effectiveness per skill point

# Anticipation / flinch: a systematic pre-shot push, down and toward the
# trigger hand. Scales with recoil energy and time pressure; reduced by skill
# and strength.
FLINCH_BASE = 0.0009  # rad per joule of free-recoil energy
FLINCH_LATERAL_FRAC = 0.5  # lateral push as a fraction of the downward push
SKILL_FLINCH = 0.10  # skill reduction per point
STR_FLINCH = 0.04  # strength reduction per point
PRESSURE_FLINCH = 0.5  # extra flinch per unit of time pressure

# Random scatter (inherent wobble), expressed as an angular sigma in radians.
SCATTER_BASE = 0.0006  # baseline sigma
SKILL_SCATTER = 0.18  # skill reduction per point
PRESSURE_SCATTER = 0.5  # extra sigma per unit of time pressure
RECOIL_SCATTER = 0.03  # extra sigma per joule of free-recoil energy


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
        "free_recoil_energy": ejecta_momentum**2 / (2 * system_mass_kg),
    }


def _inter_shot_interval(scenario):
    shot_count = scenario["shot_count"]
    time_limit = scenario["time_limit_s"]
    if shot_count <= 1:
        return float(time_limit)
    return float(time_limit) / (shot_count - 1)


def simulate_string(gun, ammo, shooter, scenario, flinch=True, scatter=True):
    """Simulate a string of shots and return their impacts on the target plane.

    Returns an ordered list of dicts:
    ``{"x_cm", "y_cm", "shot_index", "time_s"}`` relative to the point of aim,
    with x positive right and y positive up.

    `flinch` may be set to False to disable the systematic anticipation bias,
    and `scatter` to disable random wobble. With both False the result is the
    pure deterministic muzzle-climb trace (shot 0 lands on the point of aim).
    """
    gun_data = recoil.get_gun_defaults(gun)
    capacity = gun_data["capacity"]
    range_m = scenario["range_m"]
    stance = scenario.get("stance", "standing")
    shot_count = scenario["shot_count"]
    dt = _inter_shot_interval(scenario)

    strength = shooter["strength"]
    skill = shooter.get("skill", 0)
    handedness = shooter.get("handedness", "right")
    lateral_sign = -1.0 if handedness == "right" else 1.0

    rng = random.Random(scenario.get("seed", 0))

    theta_y = 0.0  # accumulated muzzle-climb angle (radians), positive = up
    shots = []
    for i in range(shot_count):
        rounds = max(1, capacity - i)
        rdata = round_recoil_data(gun, ammo, rounds)
        dist = recoil.calculate_disturbance(shooter, gun, rdata, stance)
        kick = dist["aim_kick_rad"]
        recovery = dist["recovery_seconds"]
        pressure = recovery / dt if dt > 0 else 0.0
        energy = rdata["free_recoil_energy"]

        impact_x = 0.0
        impact_y = theta_y

        if flinch and i > 0:  # the first shot shouldn't cause flinching
            flinch_mag = (
                FLINCH_BASE
                * energy
                * max(0.0, 1.0 - skill * SKILL_FLINCH)
                * (1.0 + pressure * PRESSURE_FLINCH)
                / (1.0 + strength * STR_FLINCH)
            )
            impact_x += lateral_sign * flinch_mag * FLINCH_LATERAL_FRAC
            impact_y += -flinch_mag

        if scatter:
            sigma = (
                SCATTER_BASE
                * (1.0 + pressure * PRESSURE_SCATTER)
                * (1.0 + energy * RECOIL_SCATTER)
                / (1.0 + skill * SKILL_SCATTER)
            )
            impact_x += rng.gauss(0.0, sigma)
            impact_y += rng.gauss(0.0, sigma)

        shots.append(
            {
                "shot_index": i,
                "time_s": i * dt,
                "x_cm": impact_x * range_m * 100.0,
                "y_cm": impact_y * range_m * 100.0,
            }
        )

        # Recoil drives the muzzle up, then the shooter compensates over dt.
        theta_y += kick
        effectiveness = min(1.0, (dt / recovery) * (COMP_BASE + skill * COMP_SKILL))
        theta_y *= 1.0 - effectiveness

    return shots
