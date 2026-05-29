#!/usr/bin/env python3
"""Generates SVG practice targets for each scenario and a Markdown gallery."""

import json
import os
import re
import sys

import recoil
import scoring
import simulation
import targets

SCENARIOS = None


def load_all():
    """Load recoil data plus scenario definitions into module state."""
    recoil.load_data()
    global SCENARIOS
    with open("scenarios.json", "r") as fp:
        SCENARIOS = json.load(fp)


def resolve_records(scenario):
    """Return (gun, ammo, shooter) records referenced by a scenario.

    Raises ValueError with a clear message if any reference cannot be found.
    """
    caliber = scenario["caliber"]
    if caliber not in recoil.WEAPONS:
        raise ValueError(f"Unknown caliber '{caliber}' in guns.json")
    if caliber not in recoil.AMMO:
        raise ValueError(f"Unknown caliber '{caliber}' in ammo.json")

    gun = next((g for g in recoil.WEAPONS[caliber] if g["name"] == scenario["gun"]), None)
    if gun is None:
        raise ValueError(f"Unknown gun '{scenario['gun']}' for caliber '{caliber}'")

    ammo = next((a for a in recoil.AMMO[caliber] if a["name"] == scenario["ammo"]), None)
    if ammo is None:
        raise ValueError(f"Unknown ammo '{scenario['ammo']}' for caliber '{caliber}'")

    shooter = recoil.SHOOTER.get(scenario["shooter"])
    if shooter is None:
        raise ValueError(f"Unknown shooter '{scenario['shooter']}'")

    return gun, ammo, shooter


def _slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _augment_score(score, shots):
    """Add the vertical-walk metric used by the bullseye stats panel."""
    if shots:
        score = dict(score)
        score["vertical_walk_cm"] = shots[-1]["y_cm"] - shots[0]["y_cm"]
    return score


def run_scenarios(scenarios, out_dir):
    """Simulate, score, and render each scenario; write SVGs + TARGETS.md.

    Returns the number of scenarios successfully rendered. Scenarios that
    reference missing data are warned to stderr and skipped.
    """
    os.makedirs(out_dir, exist_ok=True)
    gallery = ["# Target Practice Gallery", ""]
    rendered = 0
    for scenario in scenarios:
        try:
            gun, ammo, shooter = resolve_records(scenario)
        except ValueError as exc:
            print(f"WARNING: skipping '{scenario.get('name')}': {exc}", file=sys.stderr)
            continue

        target_def = targets.TARGET_DEFS[scenario["target"]]
        shots = simulation.simulate_string(gun, ammo, shooter, scenario)
        score = scoring.score_string(
            shots, target_def, string_time_s=scenario["time_limit_s"]
        )
        score = _augment_score(score, shots)
        run_meta = {
            "scenario": scenario["name"],
            "gun": gun["name"],
            "ammo": ammo["name"],
            "shooter": scenario["shooter"],
            "range_m": scenario["range_m"],
            "shot_count": scenario["shot_count"],
            "time_limit_s": scenario["time_limit_s"],
        }
        svg = targets.render_svg(target_def, shots, score, run_meta)
        filename = f"{_slugify(scenario['name'])}.svg"
        with open(os.path.join(out_dir, filename), "w") as fp:
            fp.write(svg)
        gallery.append(f"## {scenario['name']}")
        gallery.append("")
        gallery.append(f"![{scenario['name']}]({filename})")
        gallery.append("")
        rendered += 1

    with open(os.path.join(out_dir, "TARGETS.md"), "w") as fp:
        fp.write("\n".join(gallery))
    return rendered


if __name__ == "__main__":
    load_all()
    output = sys.argv[1] if len(sys.argv) > 1 else "targets"
    n = run_scenarios(SCENARIOS, output)
    print(f"Rendered {n} scenario(s) to {output}/")
