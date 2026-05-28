#!/usr/bin/env python3

"""Demonstrates an alternative recoil model for CDDA"""

import json
import math
import re
import sys

# All weights are in grams
# Velocity is in m/s

AMMO = None
WEAPONS = None
SHOOTER = None

def load_data():
    with open("ammo.json", "r") as fp:
        global AMMO
        AMMO = json.load(fp)
    with open("guns.json", "r") as fp:
        global WEAPONS
        WEAPONS = json.load(fp)
    with open("shooters.json", "r") as fp:
        global SHOOTER
        SHOOTER = json.load(fp)


ACTION_GAS_FACTORS = {
    "bolt": 1.50,
    "revolver": 1.55,
    "locked_breech": 1.50,
    "direct_blowback": 1.60,
    "roller_delayed": 1.55,
    "gas": 1.75,
}

ACTION_SHARPNESS = {
    "bolt": 0.90,
    "revolver": 1.05,
    "locked_breech": 1.00,
    "direct_blowback": 1.15,
    "roller_delayed": 0.92,
    "gas": 0.85,
}

SUPPORT_FACTORS = {
    "one_hand": 0.70,
    "two_hand": 1.00,
    "braced": 1.15,
    "stocked": 1.35,
}

STANCE_FACTORS = {
    "standing": 1.00,
    "crouching": 1.20,
    "prone": 1.55,
}

TYPE_DEFAULTS = {
    "pistol": {"action_type": "locked_breech", "support_class": "two_hand", "bore_offset": 0.05},
    "submachinegun": {"action_type": "direct_blowback", "support_class": "stocked", "bore_offset": 0.04},
    "rifle": {"action_type": "gas", "support_class": "stocked", "bore_offset": 0.06},
}


def get_gun_defaults(gun):
    defaults = TYPE_DEFAULTS.get(gun.get("type"), TYPE_DEFAULTS["pistol"]).copy()
    defaults.update(gun)
    return defaults


def calculate_free_recoil(gun, used_ammo, configuration):
    gun_data = get_gun_defaults(gun)
    m_gun = gun_data["mass"]
    m_prj = used_ammo["bullet_mass"]
    m_prp = used_ammo["propellant_mass"]
    v_nominal = used_ammo["v_muzzle"]
    barrel_difference = gun_data["barrel_length"] - used_ammo["ref_barrel"]
    delta_v = 0.333 * math.exp(0.00302 * v_nominal) * barrel_difference
    actual_v = v_nominal + delta_v

    if configuration not in ("full", "empty"):
        raise ValueError(
            f"Invalid configuration '{configuration}'. "
            f"Valid configurations are: empty, full"
        )

    if configuration == "full":
        ammo_mass = gun_data["mag_mass"] + gun_data["capacity"] * used_ammo["cartridge_mass"]
    else:
        ammo_mass = gun_data["mag_mass"]

    system_mass_kg = (m_gun + ammo_mass) / 1000
    action_type = gun_data["action_type"]
    if action_type not in ACTION_GAS_FACTORS:
        valid_types = ", ".join(sorted(ACTION_GAS_FACTORS.keys()))
        raise ValueError(
            f"Invalid action_type '{action_type}'. "
            f"Valid action types are: {valid_types}"
        )
    gas_factor = ACTION_GAS_FACTORS[action_type]
    ejecta_momentum = ((m_prj * actual_v) + (m_prp * actual_v * gas_factor)) / 1000
    recoil_velocity = ejecta_momentum / system_mass_kg
    free_recoil_energy = ejecta_momentum ** 2 / (2 * system_mass_kg)

    return {
        "nominal_velocity": v_nominal,
        "actual_velocity": actual_v,
        "system_mass_kg": system_mass_kg,
        "gas_factor": gas_factor,
        "ejecta_momentum": ejecta_momentum,
        "recoil_velocity": recoil_velocity,
        "free_recoil_energy": free_recoil_energy,
    }


def resolve_support_class(shooterdata, gun_data):
    if shooterdata.get("injured_hand"):
        return "one_hand"
    return gun_data.get("support_class", "two_hand")


def calculate_disturbance(shooterdata, gun, recoil_data, stance):
    gun_data = get_gun_defaults(gun)
    support_class = resolve_support_class(shooterdata, gun_data)
    support_factor = SUPPORT_FACTORS[support_class]
    stance_factor = STANCE_FACTORS[stance]
    action_sharpness = ACTION_SHARPNESS[gun_data["action_type"]]
    strength = shooterdata["strength"]
    skill = shooterdata.get("skill", 0)
    bore_offset = gun_data["bore_offset"]
    system_mass_kg = recoil_data["system_mass_kg"]
    ejecta_momentum = recoil_data["ejecta_momentum"]

    control_factor = support_factor * stance_factor * (1 + strength * 0.08 + skill * 0.06)
    aim_kick_rad = (ejecta_momentum * bore_offset * action_sharpness) / (system_mass_kg * control_factor)
    aim_kick_qd = ((aim_kick_rad * 180) / math.pi) / 4
    recovery_seconds = max(
        0.05,
        (ejecta_momentum * action_sharpness) / (support_factor * stance_factor * (1 + strength * 0.10 + skill * 0.08)),
    )

    return {
        "support_class": support_class,
        "control_factor": control_factor,
        "action_sharpness": action_sharpness,
        "aim_kick_rad": aim_kick_rad,
        "aim_kick_qd": aim_kick_qd,
        "recovery_seconds": recovery_seconds,
    }


def calculate_recoil(gun, used_ammo, configuration):
    """Returns recoil force in Joules"""
    result = calculate_free_recoil(gun, used_ammo, configuration)
    return (
        result["free_recoil_energy"],
        result["nominal_velocity"],
        result["actual_velocity"],
    )


def calculate_throwoff(shooter, gun, recoil_full, recoil_empty):
    shooterdata = SHOOTER[shooter]
    h_shooter = shooterdata.get("height") / 1000
    m_shooter = shooterdata.get("weight") / 1000
    print(f"\n#### {shooter} ({h_shooter:.2f} m, {m_shooter:.2f} kg, STR: {shooterdata['strength']})")

    for label, recoil_data in [("Full Magazine", recoil_full), ("Empty Magazine", recoil_empty)]:
        print(f"\n##### {label}\n")
        print("| Stance | Aim kick (rad) | Aim kick (¼d) | Recovery (s) | Support |")
        print("|-------:|---------------:|--------------:|-------------:|--------:|")
        for stance in ("standing", "crouching", "prone"):
            disturbance = calculate_disturbance(shooterdata, gun, recoil_data, stance)
            print(
                f"| {stance} | {disturbance['aim_kick_rad']:.4f} | "
                f"{disturbance['aim_kick_qd']:.1f} | {disturbance['recovery_seconds']:.2f} | "
                f"{disturbance['support_class']} |"
            )


def show_recoil(gun, used_ammo):
    print(f"## {gun['name']}: {used_ammo['name']} ({gun['barrel_length']}\" barrel, {gun['capacity']} rd. mag)")
    recoil_full = calculate_free_recoil(gun, used_ammo, "full")
    recoil_empty = calculate_free_recoil(gun, used_ammo, "empty")
    prp_prj_ratio = used_ammo["propellant_mass"] / used_ammo["bullet_mass"]
    e_bullet = 0.5 * (used_ammo["bullet_mass"] / 1000) * recoil_full["nominal_velocity"] ** 2
    damage = int(math.sqrt(e_bullet))
    print(f"* Nominal Muzzle Velocity: {recoil_full['nominal_velocity']:.1f} m/s")
    print(f"* Actual Muzzle Velocity: {recoil_full['actual_velocity']:.1f} m/s")
    print(f"* Bullet Energy: {e_bullet:.1f} J, Damage Potential: {damage}")
    print(f"* Propellant to bullet ratio: {prp_prj_ratio:.2f}")
    print("\n### Recoil Physics")
    print(f" - Fully loaded free recoil: {recoil_full['free_recoil_energy']:.2f} J")
    print(f" - Last-shot free recoil: {recoil_empty['free_recoil_energy']:.2f} J")
    print(f" - Fully loaded ejecta momentum: {recoil_full['ejecta_momentum']:.2f} kg m/s")
    print(f" - Last-shot ejecta momentum: {recoil_empty['ejecta_momentum']:.2f} kg m/s")
    print("\n### Shooter Disturbance")
    for shooter in SHOOTER:
        calculate_throwoff(shooter, gun, recoil_full, recoil_empty)
    print("\n")


if __name__ == "__main__":
    load_data()
    print("# Example Data for Recoil Model\n")
    print("## Table of Contents\n")
    substitutions = re.compile(r"[\",.():&+]")
    for guntype in WEAPONS:
        reference = substitutions.sub("", guntype).lower().replace(" ", "-")
        print(f"### [{guntype}](#{reference})\n")
        for weapon in WEAPONS[guntype]:
            for ammo in AMMO[guntype]:
                title = f"{weapon['name']}: {ammo['name']} ({weapon['barrel_length']}\"" \
                       f"barrel, {weapon['capacity']} rd. mag)"
                link = substitutions.sub("", title).lower().replace(" ", "-")
                print(f"- [{title}](#{link})\n")

    for guntype in WEAPONS:
        print(f"# {guntype}:")
        if guntype not in AMMO:
            print(f"WARNING: {guntype} not found in AMMO", file=sys.stderr)
            continue
        for weapon in WEAPONS[guntype]:
            for ammo in AMMO[guntype]:
                show_recoil(weapon, ammo)
