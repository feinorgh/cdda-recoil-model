#!/usr/bin/env python3

"""Demonstrates an alternative recoil model for CDDA"""

import math
import re
import sys

# All weights are in grams
# Velocity is in m/s

AMMO = {
    "9x19mm Parabellum": [
        {
            "name": "9x19mm 115 gr Federal FMJ",
            "type": "FMJ",
            "bullet_mass": 7.45,
            "propellant_mass": 0.27,
            "ref_barrel": 4.65,
            "v_muzzle": 360,
            "cartridge_mass": 4 + 7.45 + 0.27,
        },
        {
            "name": "9x19mm 124 gr Underwood FMJ +P",
            "type": "FMJ +P",
            "bullet_mass": 8.04,
            "propellant_mass": 0.30,
            "ref_barrel": 4.65,
            "v_muzzle": 373,
            "cartridge_mass": 4 + 8.04 + 0.30,
        }
    ],
    ".40 S&W": [
        {
            "name": ".40 S&W 165 gr Federal FMJ",
            "type": "FMJ",
            "bullet_mass": 10.69,
            "propellant_mass": 0.40,
            "ref_barrel": 4,
            "v_muzzle": 340,
            "cartridge_mass": 15.9,
        },
    ],
    "5.56x45mm NATO": [
        {
            "name": "5.56x45mm NATO M855A1",
            "type": "FMJBT",
            "bullet_mass": 4.02,
            "propellant_mass": 1.69,
            "ref_barrel": 20,
            "v_muzzle": 961,
            "cartridge_mass": 12.31,
        },
        {
            "name": ".223 Remington 36gr JHP",
            "type": "JHP",
            "bullet_mass": 2.33,
            "propellant_mass": 1.81,
            "ref_barrel": 24,
            "v_muzzle": 1140,
            "cartridge_mass": 6.0 + 2.33 + 1.81,
        },
    ],
    "7.62x51mm NATO": [
        {
            "name": "7.62x51mm NATO M80",
            "type": "FMJ",
            "bullet_mass": 9.53,
            "propellant_mass": 2.98,
            "ref_barrel": 24,
            "v_muzzle": 850,
            "cartridge_mass": 25.4,
        },
        {
            "name": "7.62x51mm NATO M80A1",
            "type": "FMJBT",
            "bullet_mass": 8.42,
            "propellant_mass": 2.90,
            "ref_barrel": 22,
            "v_muzzle": 931.2,
            "cartridge_mass": 23.72,
        },
        {
            "name": "7.62x51mm NATO MK319 MOD 0",
            "type": "OTBT",
            "bullet_mass": 8.42,
            "propellant_mass": 2.95,
            "ref_barrel": 22,
            "v_muzzle": 890,
            "cartridge_mass": 26.4,
        }
    ],
    "7x57mm": [
        {
            "name": "7x57mm Spitzer",
            "type": "Spitzer",
            "bullet_mass": 9.1,
            "propellant_mass": 2.75,
            "ref_barrel": 22,
            "v_muzzle": 823,
            "cartridge_mass": 23.3,
        },
    ],
    ".50 BMG": [
        {
            "name": "Cartridge, caliber .50, ball, M33",
            "type": "FMJ",
            "bullet_mass": 45.79,
            "propellant_mass": 15.23,
            "ref_barrel": 45,
            "v_muzzle": 890,
            "cartridge_mass": 114.18,
        },
    ],
}

WEAPONS = {
    "9x19mm Parabellum": [
        {
            "name": "Beretta M9A1",
            "type": "pistol",
            "barrel_length": 4.9,
            "mass": 961,
            "mag_mass": 113,
            "capacity": 15,
        },
        {
            "name": "Glock 19M",
            "type": "pistol",
            "barrel_length": 4.02,
            "mass": 600,
            "mag_mass": 70,
            "capacity": 15,
        },
        {
            "name": "Glock 17",
            "type": "pistol",
            "barrel_length": 4.49,
            "mass": 630,
            "mag_mass": 75,
            "capacity": 17,
        },
        {
            "name": "MP5-N",
            "type": "submachinegun",
            "barrel_length": 8.9,
            "mass": 2880,
            "mag_mass": 170,
            "capacity": 30,
        },
    ],
    "5.56x45mm NATO": [
        {
            "name": "M4A1",
            "type": "rifle",
            "barrel_length": 14.5,
            "mass": 2880,
            "mag_mass": 112,
            "capacity": 30,
        },
        {
            "name": "M27 IAR",
            "type": "rifle",
            "barrel_length": 16.5,
            "mass": 3700,
            "mag_mass": 112,
            "capacity": 30,
        },
        {
            "name": "HK 416 D20RS",
            "type": "rifle",
            "barrel_length": 20,
            "mass": 3885,
            "mag_mass": 80,
            "capacity": 30,
        },
    ],
    "7.62x51mm NATO": [
        {
            "name": "FN MK 17 CQC",
            "type": "rifle",
            "barrel_length": 13,
            "mass": 3490,
            "mag_mass": 266,
            "capacity": 20,
        },
        {
            "name": "M24",
            "type": "rifle",
            "barrel_length": 24,
            "mass": 5400,
            "mag_mass": 0,
            "capacity": 5,
        },
        {
            "name": "H&K G3",
            "type": "rifle",
            "barrel_length": 17.7,
            "mass": 4380,
            "mag_mass": 134,
            "capacity": 20,
        },
    ],
    ".40 S&W": [
        {
            "name": "Glock 22",
            "type": "pistol",
            "barrel_length": 4.49,
            "mass": 645,
            "mag_mass": 80,
            "capacity": 15,
        },
    ],
    "7x57mm": [
        {
            "name": "Mauser 1898",
            "type": "rifle",
            "barrel_length": 24,
            "mass": 4540,
            "mag_mass": 0,
            "capacity": 5,
        },
    ],
    ".50 BMG": [
        {
            "name": "M82A1",
            "type": "rifle",
            "barrel_length": 29,
            "mass": 14800,
            "mag_mass": 720,
            "capacity": 10,
        },
    ],
}

SHOOTER = {
    "Alice Smallframe": {
        "weight": 45000,
        "height": 1570,
        "strength": 5,
        "skill": 1,
        "injured_hand": False,
    },
    "Burly Bob": {
        "weight": 82000,
        "height": 1950,
        "strength": 8,
        "skill": 5,
        "injured_hand": False,
    },
    "Commando Cassie": {
        "weight": 58000,
        "height": 1640,
        "strength": 6,
        "skill": 8,
        "injured_hand": False,
    },
    "Damaged Dan": {
        "weight": 75000,
        "height": 1780,
        "strength": 3,
        "skill": 5,
        "injured_hand": True,
    },
}


def calculate_recoil(gun, used_ammo, configuration):
    """Returns recoil force in Joules"""
    m_gun = gun.get("mass")
    m_prj = used_ammo.get("bullet_mass")
    m_prp = used_ammo.get("propellant_mass")
    v_prj = used_ammo.get("v_muzzle")
    barrel_difference = gun.get("barrel_length") - used_ammo.get("ref_barrel")
    # print(f"Barrel difference: {barrel_difference} in")
    delta_v = 0.333 * math.exp(0.00302 * v_prj) * barrel_difference
    # print(f"Delta V: {delta_v} m/s")
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
    print(f"\nShoulder height: {h_shoulder:.2f} m")
    # rifles have three point anchoring (two hands + shoulder)
    if (gun.get("type") == "rifle" and not shooterdata.get("injured_hand")):
        print("\nUsing rifle shooting stance")
        stance_factor = 3
    else:
        print("\nUsing one-handed pistol shooting stance")
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
        print(f"\nShooter backwards velocity: {v_shooter:.2f} m/s")
        print(f"\nShooter raw orbital angular momentum: "
              f"{orbital_angular_momentum:.2f} rad/s")

        print("\nSkill vs. Throw-off (radians | quarter degrees):\n")

        for skill in range(11):
            skill_factor = skill * 0.1  # 10 represents full handling
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
            print(f"* {skill}: {throwoff:.4f}|{throwoff_qd:.0f}; "
                  f"crouched {throwoff_c:.4f}|{throwoff_c_qd:.0f}; "
                  f"prone {throwoff_p:.4f}|{throwoff_p_qd:.0f}")


def show_recoil(gun, used_ammo):
    """Shows recoil energy of a gun/used_ammo combination"""
    print(f"## {gun['name']}: {used_ammo['name']} ({gun['barrel_length']}\""
          f"barrel, {gun['capacity']} rd. mag)")
    (recoil_full, v_p, v_a) = calculate_recoil(gun, used_ammo, "full")
    prp_prj_ratio = used_ammo.get("propellant_mass") / \
        used_ammo.get("bullet_mass")
    print(f"* Nominal Muzzle Velocity: {v_p:.1f} m/s")
    print(f"* Actual Muzzle Velocity: {v_a:.1f} m/s")
    e_bullet = 0.5 * (used_ammo.get("bullet_mass") / 1000) * v_p**2
    damage = int(math.sqrt(e_bullet))
    print(f"* Bullet Energy: {e_bullet:.1f} J, Damage Potential: {damage}")
    print(f"* Propellant to bullet ratio: {prp_prj_ratio:.2f}")
    print(f" - Fully loaded: {recoil_full:.2f} J")
    (recoil_empty, v_p, v_a) = calculate_recoil(gun, used_ammo, "empty")
    print(f" - Last shot: {recoil_empty:.2f} J")
    print("\n### Throwoff")
    for shooter in SHOOTER:
        calculate_throwoff(shooter, gun, recoil_full, recoil_empty)
    print("\n")


if __name__ == "__main__":
    print("# Example Data for Recoil Model\n")
    print("## Table of Contents\n")
    substitutions = re.compile(r"[\",.():]")
    for guntype in WEAPONS:
        reference = substitutions.sub("", guntype).lower().replace(" ", "-")
        print(f"### [{guntype}](#{reference})\n")
        for weapon in WEAPONS[guntype]:
            for ammo in AMMO[guntype]:
                title = f"{weapon['name']}: {ammo['name']} ({weapon['barrel_length']}\"" \
                       f"barrel, {weapon['capacity']} rd. mag)"
                #link = title.replace(" ", "-").replace(":", "").lower()
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
