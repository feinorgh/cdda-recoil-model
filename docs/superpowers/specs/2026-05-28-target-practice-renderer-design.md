# Target Practice Renderer — Design Spec

**Date:** 2026-05-28
**Status:** Approved design, ready for implementation planning
**Sub-project:** 1 of 2 (the CDDA gun-definition importer is a separate follow-on project)

## Purpose

Add a feature to the CDDA recoil model that **renders authentic-looking SVG shooting targets** showing simulated shot strings, so the effects of recoil, shooter skill, weapon, ammunition, and firing cadence can be *visibly compared* against real-world shooting formats.

Two target types are supported:
- **Paper bullseye** — for precision/qualification formats (slow, timed, rapid fire).
- **IPSC popper** (and IPSC scoring silhouette) — for practical/action shooting speed strings.

The renderings are anchored on real shooting formats (fixed ranges, shot counts, time limits) so results can be compared to real-life situations.

## Scope

**In scope (this sub-project):**
- A configurable scenario engine that simulates a string of shots and renders an SVG target per scenario.
- A curated default set of scenarios that demonstrate differences between shooters, weapons, ammunition, and cadence.
- Scoring for bullseye (ring score), IPSC silhouette (A/C/D + hit factor), and popper (knock-down).
- Works against the project's **existing local data format** (`guns.json`, `ammo.json`, `shooters.json`) plus new scenario data.

**Out of scope (deferred to sub-project 2):**
- Importing gun definitions from the upstream CDDA repository (`copy-from` resolution, magazine/ammo lookup, unit parsing, filling missing physics fields). This is a substantial separate subsystem and will feed this renderer once built.

**Non-goals:**
- Raster image output (we use SVG only — zero new dependencies).
- Changing the existing `recoil.py` physics or its Markdown report.

## Architecture

Small, single-responsibility modules around the unchanged `recoil.py` physics engine. Each is a pure function over data and independently testable.

| File | Responsibility | Depends on |
|------|----------------|------------|
| `recoil.py` *(unchanged)* | Free-recoil + disturbance physics (`aim_kick_rad`, `recovery_seconds`). | — |
| `simulation.py` *(new)* | `simulate_string(gun, ammo, shooter, scenario, seed) -> list[Shot]`. Turns recoil + shooter behaviour into shot impact coordinates over time. | `recoil.py` |
| `scoring.py` *(new)* | `score_string(shots, target_def) -> ScoreResult`. One scorer per target type. | — |
| `targets.py` *(new)* | `render_svg(target_def, shots, score, run_meta) -> str`. Authentic target faces + side stats panel. | — |
| `scenarios.json` *(new)* | Scenario definitions. | — |
| `shooters.json` *(edit)* | Add `handedness` field (default `"right"`). | — |
| `practice.py` *(new entry point)* | Orchestrates: load data -> simulate -> score -> render -> write SVG files + Markdown gallery. | all above |

### Data flow

`practice.py` reads the four JSON files. For each scenario it resolves the gun/ammo/shooter, calls `simulation.simulate_string` to get impacts (in **cm on the target plane**), calls `scoring.score_string`, calls `targets.render_svg`, writes the SVG to the output directory, and appends an entry to a generated Markdown gallery. The existing `recoil.py` report is untouched.

## Data model

### `scenarios.json` (new)

A list of scenario objects. Proposed fields:

| Field | Meaning |
|-------|---------|
| `name` | Human-readable scenario title (used in gallery + filenames). |
| `target` | Target type / definition key: `"bullseye"`, `"ipsc_silhouette"`, or `"popper"`. |
| `range_m` | Distance to target, metres. |
| `caliber` | Caliber key shared by `guns.json` and `ammo.json` (e.g. `"9x19mm Parabellum"`). |
| `gun` | The `name` of a gun record within that caliber's list (e.g. `"Glock 17"`). |
| `ammo` | The `name` of an ammo record within that caliber's list. |
| `shooter` | A shooter display-name key from `shooters.json` (e.g. `"Commando Cassie"`). |
| `shot_count` | Number of shots in the string. |
| `time_limit_s` | String time limit; with `shot_count` yields inter-shot cadence `dt`. |
| `stance` | `"standing"` / `"crouching"` / `"prone"` (default `"standing"`). |
| `seed` | RNG seed for reproducible output. |

Comparison sets are expressed as groups of scenarios that vary one dimension (shooter, gun, or cadence).

### `shooters.json` (edit)

Add `handedness`: `"right"` (default) or `"left"`. Drives the lateral direction of the flinch bias.

### Target definitions

Target geometry (physical dimensions in cm, ring radii / zone polygons / popper outline, and scoring values) lives in `targets.py` (or a small data block it owns). Real target dimensions are used so angular kick projects to physically meaningful spread.

## Simulation model (`simulation.py`)

`simulate_string` walks the string shot-by-shot, tracking the muzzle's angular error `theta = (theta_x, theta_y)` from the point of aim, starting at the origin.

**Per-shot recoil inputs:** as the magazine depletes, system mass drops, so free recoil is recomputed for the *remaining* round count — later shots kick slightly harder. This produces each shot's `aim_kick_rad` and `recovery_seconds` from `recoil.py`.

**Cadence / time pressure:** the scenario's `shot_count` and `time_limit_s` give the inter-shot interval `dt`. Pressure ratio `p = recovery_seconds / dt` (`p <= 1` relaxed, `p > 1` rushing).

**Three behavioural effects**, modulated by `skill`, `strength`, `handedness`, and `p`:

1. **Anticipation / flinch** — a pre-shot push applied at the moment of firing, directed **down + toward the trigger-hand side** (right-handed -> low-left, left-handed -> low-right). Magnitude grows with recoil energy and pressure `p`; shrinks with skill and strength. This is the systematic bias.
2. **Random scatter** — a 2D Gaussian wobble; sigma shrinks with skill, grows with `p` and residual recoil.
3. **Muzzle climb + active compensation** — the shot fires at the current `theta`; recoil then adds `+aim_kick_rad` to `theta_y`; over `dt` the shooter drives the muzzle back with an effectiveness that rises with skill and available time. Skilled shooters cancel most climb even when rushing; intermediate shooters under-cancel (group walks up) or over-cancel under pressure; novices lag badly.

**Impact** = `theta_current + flinch_bias + scatter`, then projected to the target plane: `offset_cm = theta_rad * range_m * 100`. Same kick spreads more at longer range.

**Output:** ordered list of `Shot{ x_cm, y_cm, shot_index, time_s }` relative to the point of aim.

**Determinism:** seeded RNG (per-scenario seed) so side-by-side comparisons are reproducible.

### Guaranteed, tested behaviours

Tuning constants are dialed in during implementation, but these directional invariants are guaranteed and form the test suite:

- Slow cadence (`dt >> recovery`) -> negligible vertical walk; fast cadence -> measurable upward walk.
- Higher skill -> smaller group **and** smaller flinch bias **and** less walk.
- Right-handed flinch lands low-left; left-handed low-right.
- Longer range -> proportionally larger linear spread for the same angles.
- Later shots in a string kick slightly more than earlier shots (magazine depletion).
- Same seed + inputs -> identical impacts.

## Scoring (`scoring.py`)

One scorer per target type, using real target dimensions in cm:

- **Bullseye** — each shot scored by radial distance against ring radii -> ring value (10..1, X-ring center). Reports total score, X-count, group size (extreme spread, cm), mean point of impact (MPI), and vertical walk.
- **IPSC silhouette** — A/C/D zone hit -> points; reports total points, zone breakdown, and **hit factor** (points / string time).
- **Popper** — steel knock-down; a hit inside the popper outline neutralizes it. Reports hit/miss, **shots-to-neutralize**, and time-to-first-hit.

## Rendering (`targets.py`)

Authentic target faces rendered as SVG strings (no external libraries):

- **Bullseye** — paper-colored field, numbered concentric rings, black aiming bull, red shot markers (white-outlined, optionally numbered by shot order).
- **IPSC silhouette** — tan cardboard target with A/C/D zone outlines + markers.
- **Popper** — classic steel popper (round head, stem, base); a "NEUTRALIZED" stamp when knocked down.
- The run's stats (shooter, gun, ammo, range, cadence, score, hit factor, group size, MPI, vertical walk) appear in a **side panel beside the target face**, not overlaid, to keep the face authentic. The canvas is larger than the target so misses are still visible off the paper/steel.

## Output & integration (`practice.py`)

- Writes one SVG per scenario into an output directory.
- Generates a Markdown **gallery** that embeds/links the SVGs — mirroring how `EXAMPLE.md` documents the existing report.
- **Git handling:** commit a **curated example set** (a handful of SVGs + the gallery `.md`), consistent with the committed `EXAMPLE.md`. Bulk/extra generated output goes to a gitignored output directory.

## Testing

Per-module unit tests in `tests/` (the project uses `python3 -m unittest`):

- `simulation.py` — assert each guaranteed invariant above using deterministic seeds.
- `scoring.py` — known impact sets produce known scores / hit factors / knock-down outcomes.
- `targets.py` — rendered SVG contains expected structural elements (ring count, one marker per shot, neutralized stamp when applicable) and is well-formed.
- `practice.py` — smoke test that the curated set generates the expected files and gallery without error.

## Error handling

Follows the existing project convention: invalid configuration values raise `ValueError` with a clear message listing valid options (matching `recoil.py`'s validation style). Caliber/data mismatches in the main loop are surfaced as warnings to stderr, consistent with the existing report.
