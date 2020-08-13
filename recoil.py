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
    """Loads the data from the JSON files"""
    with open("ammo.json", "r") as in_fp:
        global AMMO
        AMMO = json.load(in_fp)
    with open("guns.json", "r") as in_fp:
        global WEAPONS
        WEAPONS = json.load(in_fp)
    with open("shooters.json", "r") as in_fp:
        global SHOOTER
        SHOOTER = json.load(in_fp)


def calculate_recoil(gun, used_ammo, configuration):
    """Returns recoil force in Joules"""
    m_gun = gun.get("mass")
    m_prj = used_ammo.get("bullet_mass")
    m_prp = used_ammo.get("propellant_mass")
    v_prj = used_ammo.get("v_muzzle")
    barrel_difference = gun.get("barrel_length") - used_ammo.get("ref_barrel")
    delta_v = 0.333 * math.exp(0.00302 * v_prj) * barrel_difference
    actual_v_prj = v_prj + delta_v
    if configuration == "full":
        m_ammo = gun.get("mag_mass") + gun.get("capacity") * \
            used_ammo.get("cartridge_mass")
    else:
        m_ammo = gun.get("mag_mass")
    v_gas_factor = 1.5
    if gun.get("type") == "rifle":
        v_gas_factor = 1.75
    # Long form (via firearm velocity calculation:)
    # v_recoil = (m_prj * v_prj + m_prp * v_prj * v_gas_factor) /
    #       (m_gun + m_ammo)
    # E_recoil = 0.5 * (m_gun + m_ammo)/1000 * v_recoil**2
    # Short form:
    recoil_energy = 0.5 * (((m_prj * actual_v_prj + m_prp * actual_v_prj *
                             v_gas_factor) / 1000)**2) / (m_gun + m_ammo) * \
        1000
    return (recoil_energy, v_prj, actual_v_prj)


def calculate_throwoff(shooter, gun, recoil_full, recoil_empty):
    """Calculates (and prints the "throwoff" in radians/quarter degrees)"""
    # Ek = 0.5 * m * v^2 = recoil energy
    # Ek = (p^2)/2m
    # Ek*2m = p^2
    # p = math.sqrt(Ek*2m)
    shooterdata = SHOOTER[shooter]
    h_shooter = shooterdata.get("height") / 1000  # m
    m_shooter = shooterdata.get("weight") / 1000  # kg
    s_shooter = shooterdata.get("strength")
    h_shoulder = h_shooter * 4 / 5               # shoulder height
    print(f"\n#### {shooter} ({h_shooter:.2f} m, {m_shooter:.2f} kg, "
          f"STR: {s_shooter})")
    # angular momentum is proportional to the moment of inertia and angular
    # spead in radians/s
    # L = Iω
    # L = rmv
    # the shooter is given a backwards rotation around the center of mass,
    # located at shooter's height / 2
    # where r = shooter's height / (4/5) (4 5ths being around shoulder height)
    print(f"\n* Shoulder height: {h_shoulder:.2f} m")
    # rifles have three point anchoring (two hands + shoulder)
    if (gun.get("type") == "rifle" and not shooterdata.get("injured_hand")):
        print("* Using rifle shooting stance")
        stance_factor = 3
    else:
        print("* Using one-handed pistol shooting stance")
        stance_factor = 1

    for recoil in [recoil_full, recoil_empty]:
        if recoil == recoil_full:
            print("\n##### Full Magazine")
        else:
            print("\n##### Empty Magazine")
        # (backwards) velocity given to the shooter:
        v_shooter = recoil / m_shooter
        # theoretically, it would be possible to place the pivot point
        # at the centre of mass in the shooter, i.e
        # shoulder height - shooter_height / 2, which would lessen the
        # effect of angular momentum
        orbital_angular_momentum = h_shoulder * m_shooter * v_shooter
        print(f"\n* Shooter backwards velocity: {v_shooter:.2f} m/s")
        print(f"* Shooter raw orbital angular momentum: "
              f"{orbital_angular_momentum:.2f} rad/s")

        # print("\nSkill vs. Throw-off (radians | quarter degrees):\n")
        print("\n##### Throw-off, radians (quarter degrees)\n")
        print("S = standing, C = crouching, P = prone, "
              "r = radians, ¼d = quarter degrees\n")
        print("| Skill | S (r) | S (¼d) | C (r) | C (¼d) | P (r) | P (¼d) |")
        print("|------:|------:|-------:|------:|-------:|------:|-------:|")

        for skill in range(11):
            skill_factor = skill * 0.1  # 10 represents full handling ability
            handling_factor = 1 + (s_shooter * skill_factor * stance_factor)
            # reaction time = 0.15 s for touch, we use this as a base
            # scaling factor to compensate for recoil management
            # this could theoretically be made worse being
            # dazed/injured/drugged/confused/less intelligent/dexterious
            throwoff = (orbital_angular_momentum / handling_factor) * 0.15
            throwoff_qd = ((throwoff*180)/math.pi)/4
            throwoff_c = throwoff / 2
            throwoff_c_qd = ((throwoff_c*180)/math.pi)/4
            throwoff_p = throwoff / 5
            throwoff_p_qd = ((throwoff_p*180)/math.pi)/4
            print(f"| {skill} | {throwoff:.4f} | {throwoff_qd:.0f} "
                  f"| {throwoff_c:.4f} | {throwoff_c_qd:.0f} "
                  f"| {throwoff_p:.4f} | {throwoff_p_qd:.0f} |")


def show_recoil(gun, used_ammo):
    """Shows recoil energy of a gun/used_ammo combination"""
    print(f"## {gun['name']}: {used_ammo['name']} ({gun['barrel_length']}\""
          f" barrel, {gun['capacity']} rd. mag)")
    (recoil_full, v_p, v_a) = calculate_recoil(gun, used_ammo, "full")
    prp_prj_ratio = used_ammo.get("propellant_mass") / \
        used_ammo.get("bullet_mass")
    print(f"* Nominal Muzzle Velocity: {v_p:.1f} m/s")
    print(f"* Actual Muzzle Velocity: {v_a:.1f} m/s")
    e_bullet = 0.5 * (used_ammo.get("bullet_mass") / 1000) * v_p**2
    damage = int(math.sqrt(e_bullet))
    print(f"* Bullet Energy: {e_bullet:.1f} J, Damage Potential: {damage}")
    print(f"* Propellant to bullet ratio: {prp_prj_ratio:.2f}")
    print("\n### Recoil Energy to Shooter")
    print(f" - Fully loaded: {recoil_full:.2f} J")
    (recoil_empty, v_p, v_a) = calculate_recoil(gun, used_ammo, "empty")
    print(f" - Last shot: {recoil_empty:.2f} J")
    print("\n### Throwoff")
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
                title = f"{weapon['name']}: {ammo['name']} "\
                        "({weapon['barrel_length']}\"" \
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
