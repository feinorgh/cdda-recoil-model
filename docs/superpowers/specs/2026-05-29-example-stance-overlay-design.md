# Design: Per-Example 5-Shot Stance-Comparison SVGs in EXAMPLE.md

Date: 2026-05-29
Status: Approved

## Problem

`EXAMPLE.md` is the generated reference report (`python3 recoil.py > EXAMPLE.md`).
Each of its 26 weapon/ammo sections lists a Shooter Disturbance table broken
down by 4 shooters x 3 stances (standing/crouching/prone), but the recoil
behaviour is presented only as numbers. There is no visual illustration of how
a stance affects an actual string of shots.

We want each example to additionally show **one illustrative SVG of a 5-shot
series, overlaying all three stances, color-coded per stance**, so a reader can
visually compare how stance changes the group on a real target. The shooting
distance must be clearly noted.

## Decisions (from brainstorming)

- **One SVG per example** (26 total), overlaying all three stances in a single
  bullseye target, each stance color-coded with a legend.
- **Shooter depicted:** Commando Cassie (skill 8, STR 6) — a skilled shooter
  produces realistic, comparable groups.
- **Target backdrop:** paper bullseye (the existing `bullseye` `TARGET_DEFS`
  entry — neutral grouping target).
- **Embedding:** linked image files (`![...](targets/example/<slug>.svg)`) so
  the images render on GitHub. (GitHub markdown does not render inline `<svg>`.)
- **File location:** new subfolder `targets/example/`, separate from the
  curated `targets/` gallery.
- **Fixed comparison scenario** (identical across all examples for fair
  comparison): 5 shots, **25 m**, 5 s string time. Distance is shown in the SVG.
- **Integration approach A:** a new `examples.py` module renders the SVG and
  returns the relative link; `recoil.py`'s report code calls it via a lazy
  import and prints the link. The recoil **physics functions stay frozen** —
  only report output changes.

## Architecture

```
recoil.py (report generator, physics frozen)
   |  show_recoil()  -- lazy: import examples
   v
examples.py  --> simulation.simulate_string  --> recoil.calculate_* (frozen)
             --> scoring.score_string
             --> targets.render_overlay_svg   (new function)
```

### Module responsibilities

- **`targets.py`** — gains one new public function:
  `render_overlay_svg(target_def, series, run_meta)`.
  - `series`: ordered list of `{"label": str, "color": str, "shots": list,
    "score": dict}` (one entry per stance).
  - Draws the bullseye face once, then each series' shot markers in its own
    color, then a legend panel.
  - The existing `render_svg`/`_render_bullseye`/`_render_popper`/`_render_ipsc`
    and their tests are **unchanged**.
  - Add a `_shot_markers_colored(shots, target_def, color)` helper (or extend
    `_shot_markers` with an optional color arg) so single-color rendering is
    reused.
  - The legend panel header notes Gun, Ammo, Shooter, **Range**, and String
    (rounds/time). Then one row per stance: a colored swatch + stance label +
    group size (cm) + score (ring + X) + vertical walk (cm).

- **Stance colors:** `standing = #c0392b` (red), `crouching = #2471a3` (blue),
  `prone = #1e8449` (green). Defined as a constant in `examples.py`.

- **`examples.py`** (new) — illustrative example generator.
  - Constants: `EXAMPLE_SHOOTER = "Commando Cassie"`, `EXAMPLE_RANGE_M = 25`,
    `EXAMPLE_SHOT_COUNT = 5`, `EXAMPLE_TIME_LIMIT_S = 5.0`,
    `EXAMPLE_TARGET = "bullseye"`, `STANCES = ("standing", "crouching", "prone")`,
    `STANCE_COLORS = {...}`, `OUT_DIR = "targets/example"`.
  - `_slugify(text)` — filesystem-safe slug for filenames.
  - `_example_seed(slug)` — `zlib.crc32(slug.encode())`, stable across machines,
    so each example has deterministic but distinct random scatter.
  - `render_example_overlay(gun, ammo, shooter, shooter_name, out_dir=OUT_DIR)`:
    1. For each stance, build a scenario dict
       `{range_m, stance, shot_count, time_limit_s, seed}` (the only keys
       `simulate_string` reads) and call
       `simulation.simulate_string(gun, ammo, shooter, scenario)`.
    2. `scoring.score_string(shots, target_def, string_time_s=EXAMPLE_TIME_LIMIT_S)`,
       then add `vertical_walk_cm = shots[-1]["y_cm"] - shots[0]["y_cm"]`.
    3. Assemble `series` with label/color/shots/score per stance.
    4. Build `run_meta` (gun, ammo, shooter, range_m, shot_count, time_limit_s).
    5. `svg = targets.render_overlay_svg(target_def, series, run_meta)`.
    6. Write `<out_dir>/<slugify(gun+ammo)>.svg` (create dir as needed).
    7. Return the repo-root-relative link `targets/example/<slug>.svg`.

- **`recoil.py`** — in `show_recoil(gun, used_ammo)`, after the Shooter
  Disturbance loop:
  - Lazy `import examples`.
  - Resolve the Commando Cassie shooter dict from the `SHOOTER` global; if
    absent, warn to stderr and skip (do not crash the whole report).
  - Call `examples.render_example_overlay(...)`, then print:
    ```
    ### 5-Shot Stance Comparison (Commando Cassie, 25 m)

    ![5-shot stance comparison ...](targets/example/<slug>.svg)
    ```
  - Physics functions (`calculate_free_recoil`, `calculate_disturbance`,
    `get_gun_defaults`, etc.) remain byte-for-byte unchanged.

### Data flow / coordinate conventions

Unchanged from the existing renderer: simulation and scoring work in cm with
y-up; only `targets._to_px` flips y for SVG. The overlay reuses the same
`_to_px`, face geometry, and `_scale`.

### Why no circular import

`examples.py` imports `recoil` (and simulation/scoring/targets) at module load.
`recoil.py` imports `examples` **lazily inside `show_recoil`**, so at import
time there is no cycle. The functions `examples`/`simulation` use from `recoil`
(`calculate_free_recoil`, `calculate_disturbance`, `get_gun_defaults`) are pure
w.r.t. the `AMMO`/`WEAPONS`/`SHOOTER` module globals, so the `__main__`-vs-module
double-import of `recoil` does not cause empty-globals bugs.

## Error handling

- `examples.render_example_overlay` follows repo convention: raise `ValueError`
  with a clear message for an unknown stance/target (delegated to existing
  `simulate_string`/`score_string`/`TARGET_DEFS` lookups).
- `recoil.show_recoil` guards a missing Commando Cassie shooter with a stderr
  warning and skips the SVG, consistent with the existing
  "mismatches -> stderr warnings" convention.

## Testing (TDD, `python3 -m unittest` from repo root)

New `tests/test_examples.py`:
- `render_overlay_svg` output contains all three stance colors.
- Output contains all shot markers from every series (count == sum of series
  shot counts).
- Legend contains all three stance labels and the range string (`25 m`).
- Output is a single well-formed `<svg>...</svg>`.
- Determinism: two renders of the same inputs are byte-identical.
- `render_example_overlay` writes a file at the returned path and returns a
  `targets/example/...svg` link.

Extend `tests/test_targets.py` is optional; keep overlay tests in
`test_examples.py` to avoid disturbing existing target tests.

Integration: a light test that `recoil.show_recoil` (stdout captured, cwd set to
a tmp dir) emits a line containing `![` and `targets/example/`.

## Artifacts to regenerate / commit

- 26 SVGs under `targets/example/` (one per weapon/ammo combination).
- Regenerated `EXAMPLE.md`.
- New `examples.py`, `tests/test_examples.py`.
- `targets.py` (new function), `recoil.py` (report hook only).
- `.gitignore`: `targets/example/` stays tracked (committed), but any scratch
  output remains ignored as today.
- README: a sentence noting EXAMPLE.md now embeds per-example stance-overlay
  SVGs generated into `targets/example/`.

## Out of scope (YAGNI)

- Per-shooter or per-stance separate SVGs (one overlay per example only).
- Configurable distance/time via CLI (fixed constants are sufficient).
- Animation or interactivity.
