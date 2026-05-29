"""Generates per-example 5-shot stance-comparison SVGs for EXAMPLE.md."""

import os
import re
import zlib

import scoring
import simulation
import targets

EXAMPLE_SHOOTER = "Commando Cassie"
EXAMPLE_RANGE_M = 25
EXAMPLE_SHOT_COUNT = 5
EXAMPLE_TIME_LIMIT_S = 5.0
EXAMPLE_TARGET = "bullseye"
STANCES = ("standing", "crouching", "prone")
STANCE_COLORS = {
    "standing": "#c0392b",
    "crouching": "#2471a3",
    "prone": "#1e8449",
}
OUT_DIR = "targets/example"


def _slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _example_seed(slug):
    """Stable per-example seed (zlib.crc32 is consistent across machines)."""
    return zlib.crc32(slug.encode("utf-8"))


def render_example_overlay(gun, ammo, shooter, shooter_name, out_dir=OUT_DIR):
    """Render the 3-stance comparison SVG for one gun/ammo example.

    Simulates a 5-shot string for Commando Cassie at 25 m in each of the
    standing/crouching/prone stances, scores each on the bullseye target, and
    writes one color-coded overlay SVG. Returns the written file's path as
    ``"<out_dir>/<slug>.svg"`` using forward slashes, suitable as a Markdown
    image link from the repo root.
    """
    target_def = targets.TARGET_DEFS[EXAMPLE_TARGET]
    slug = _slugify(f'{gun["name"]} {ammo["name"]}')
    seed = _example_seed(slug)

    series = []
    for stance in STANCES:
        scenario = {
            "range_m": EXAMPLE_RANGE_M,
            "stance": stance,
            "shot_count": EXAMPLE_SHOT_COUNT,
            "time_limit_s": EXAMPLE_TIME_LIMIT_S,
            "seed": seed,
        }
        shots = simulation.simulate_string(gun, ammo, shooter, scenario)
        score = scoring.score_string(
            shots, target_def, string_time_s=EXAMPLE_TIME_LIMIT_S
        )
        if shots:
            score = dict(score)
            score["vertical_walk_cm"] = shots[-1]["y_cm"] - shots[0]["y_cm"]
        series.append({
            "label": stance,
            "color": STANCE_COLORS[stance],
            "shots": shots,
            "score": score,
        })

    run_meta = {
        "gun": gun["name"],
        "ammo": ammo["name"],
        "shooter": shooter_name,
        "range_m": EXAMPLE_RANGE_M,
        "shot_count": EXAMPLE_SHOT_COUNT,
        "time_limit_s": EXAMPLE_TIME_LIMIT_S,
    }
    svg = targets.render_overlay_svg(target_def, series, run_meta)

    os.makedirs(out_dir, exist_ok=True)
    filename = f"{slug}.svg"
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8", newline="\n") as fp:
        fp.write(svg)
    return f"{out_dir.rstrip('/')}/{filename}"
