# Copilot instructions for `cdda-recoil-model`

This repository is primarily a research/proposal workspace for firearm simulation ideas in CDDA, with one executable Python proof of concept for recoil modeling. Treat `README.md` as project context and `recoil.py` plus the JSON data files as the working implementation surface.

## Commands

There are no dedicated build, test, or lint targets configured in this repository.

- Run the full prototype report:

  ```bash
  python3 recoil.py
  ```

- Run a single recoil calculation while iterating on formulas or data:

  ```bash
  python3 - <<'PY'
  import recoil
  recoil.load_data()
  gun = recoil.WEAPONS['9x19mm Parabellum'][0]
  ammo = recoil.AMMO['9x19mm Parabellum'][0]
  energy, nominal_v, actual_v = recoil.calculate_recoil(gun, ammo, 'full')
  print(f"{gun['name']} | {ammo['name']} | {energy:.2f} J | nominal {nominal_v} | actual {actual_v:.2f}")
  PY
  ```

## High-level architecture

- `README.md` describes the big picture: this repo collects notes about possible CDDA firearm simulation changes, with recoil being the only implemented prototype.
- `recoil.py` is a standalone script, not a package. It loads all runtime data from `ammo.json`, `guns.json`, and `shooters.json`, then renders a Markdown-style report to stdout for every weapon/ammo combination.
- The main computation flow is:
  1. `load_data()` populates global module state from the three JSON files.
  2. `calculate_recoil()` computes recoil energy and adjusted muzzle velocity for a gun/ammo/configuration combination.
  3. `show_recoil()` formats per-weapon output and calls `calculate_throwoff()` for each shooter profile.
  4. The `__main__` block generates a table of contents first, then the full report body.
- `EXAMPLE.md` is generated-style reference output; use it to understand expected formatting when changing report structure.

## Key conventions

- The JSON files are coupled by shared caliber keys. `guns.json` and `ammo.json` must stay aligned at the top level because `recoil.py` iterates weapons by caliber and expects matching ammo entries.
- `shooters.json` is keyed by display name and stores profile objects directly, while `ammo.json` and `guns.json` map caliber names to lists of records. Follow those shapes when adding data.
- Unit conventions matter and are mixed across source data: masses are stored in grams, shooter height is stored in millimeters, velocities are meters/second, and barrel lengths are inches. `recoil.py` performs selective conversions inline rather than normalizing all inputs up front.
- `recoil.py` relies on module-level globals (`AMMO`, `WEAPONS`, `SHOOTER`). If you import helper functions in an ad hoc script, call `load_data()` first.
- The output is intentionally report-oriented Markdown text, not structured JSON or a reusable API. When changing formatting, preserve the current heading/link style unless you also update the example output and any docs that describe it.
- Caliber mismatches are surfaced as warnings to stderr in the main loop rather than handled defensively throughout the script. If you change data loading or iteration, preserve that expectation.
