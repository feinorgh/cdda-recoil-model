# Per-Example 5-Shot Stance-Comparison SVGs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add to every weapon/ammo example in `EXAMPLE.md` one illustrative SVG showing a 5-shot series for Commando Cassie, overlaying all three stances (standing/crouching/prone) color-coded on a bullseye, with the shooting distance noted.

**Architecture:** A new `render_overlay_svg` in `targets.py` draws a bullseye face once and overlays several color-coded shot series plus a legend. A new `examples.py` module runs the recoil simulation for the three stances (Commando Cassie, 5 shots, 25 m, 5 s), scores each, and renders/writes the SVG, returning a repo-root-relative link. `recoil.py`'s report code (`show_recoil`) calls `examples` via a lazy import and prints a `### 5-Shot Stance Comparison` heading + image link. The recoil physics functions stay unchanged.

**Tech Stack:** Python 3 standard library only; `unittest` run as `python3 -m unittest` from the repo root.

---

### Task 1: Overlay rendering in `targets.py`

**Files:**
- Modify: `targets.py` (add `_bullseye_face`, color param on `_shot_markers`, `_overlay_panel`, `render_overlay_svg`; refactor `_render_bullseye` to reuse `_bullseye_face`)
- Test: `tests/test_targets.py` (add `TestOverlaySvg`)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_targets.py`:

```python
class TestOverlaySvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["bullseye"]

        def mk(total):
            return {
                "target": "bullseye", "total_score": total, "x_count": 0,
                "group_size_cm": 3.0, "mpi_x_cm": 0.0, "mpi_y_cm": 0.0,
                "per_shot": [], "vertical_walk_cm": 1.0,
            }

        self.series = [
            {"label": "standing", "color": "#c0392b",
             "shots": [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}],
             "score": mk(10)},
            {"label": "crouching", "color": "#2471a3",
             "shots": [
                 {"x_cm": 1.0, "y_cm": 1.0, "shot_index": 0, "time_s": 0.0},
                 {"x_cm": 2.0, "y_cm": -1.0, "shot_index": 1, "time_s": 1.0},
             ],
             "score": mk(18)},
            {"label": "prone", "color": "#1e8449",
             "shots": [{"x_cm": 0.0, "y_cm": 0.5, "shot_index": 0, "time_s": 0.0}],
             "score": mk(20)},
        ]
        self.run_meta = {
            "gun": "Glock 17", "ammo": "FMJ", "shooter": "Commando Cassie",
            "range_m": 25, "shot_count": 5, "time_limit_s": 5.0,
        }

    def test_well_formed_svg(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertIn("</svg>", svg)

    def test_three_stance_colors_present(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        for color in ("#c0392b", "#2471a3", "#1e8449"):
            self.assertIn(color, svg)

    def test_all_shot_markers_drawn(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        total = sum(len(s["shots"]) for s in self.series)
        self.assertEqual(svg.count('class="shot"'), total)

    def test_legend_has_labels_and_range(self):
        svg = targets.render_overlay_svg(self.target_def, self.series, self.run_meta)
        for label in ("standing", "crouching", "prone"):
            self.assertIn(label, svg)
        self.assertIn("25 m", svg)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_targets.TestOverlaySvg -v`
Expected: FAIL with `AttributeError: module 'targets' has no attribute 'render_overlay_svg'`

- [ ] **Step 3: Add a color parameter to `_shot_markers`**

In `targets.py`, change the signature and the `fill` of `_shot_markers` so single-color callers are unaffected:

```python
def _shot_markers(shots, target_def, color="#c0392b"):
    parts = []
    for shot in shots:
        px, py = _to_px(shot["x_cm"], shot["y_cm"], target_def)
        parts.append(
            f'<circle class="shot" cx="{px:.1f}" cy="{py:.1f}" r="4" '
            f'fill="{color}" stroke="#ffffff" stroke-width="0.8"/>'
        )
    return "\n".join(parts)
```

- [ ] **Step 4: Extract `_bullseye_face` and reuse it in `_render_bullseye`**

In `targets.py`, add this helper (place it just above `_render_bullseye`):

```python
def _bullseye_face(target_def):
    """SVG parts for the bullseye background and rings (no shots/panel)."""
    cx = _MARGIN_PX + _FACE_PX / 2.0
    cy = _MARGIN_PX + _FACE_PX / 2.0
    scale = _scale(target_def)
    parts = [
        f'<rect x="{_MARGIN_PX}" y="{_MARGIN_PX}" width="{_FACE_PX}" '
        f'height="{_FACE_PX}" fill="#f4f1e8" stroke="#999999"/>'
    ]
    # Rings outer-first so inner rings draw on top.
    for ring_score, radius in reversed(target_def["rings"]):
        r = radius * scale
        black = radius <= target_def["black_radius_cm"]
        fill = "#111111" if black else "none"
        stroke = "#ffffff" if black else "#222222"
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>'
        )
    return parts
```

Then replace the body of `_render_bullseye` (the background-rect + ring loop) so it reuses the helper. The new `_render_bullseye` reads:

```python
def _render_bullseye(target_def, shots, score, run_meta):
    parts = [_svg_open()]
    parts.extend(_bullseye_face(target_def))
    parts.append(_shot_markers(shots, target_def))
    parts.append(_stats_panel([
        ("Scenario", run_meta["scenario"]),
        ("Gun", run_meta["gun"]),
        ("Ammo", run_meta["ammo"]),
        ("Shooter", run_meta["shooter"]),
        ("Range", f'{run_meta["range_m"]} m'),
        ("String", f'{run_meta["shot_count"]} rds / {run_meta["time_limit_s"]} s'),
        ("Score", f'{score["total_score"]} ({score["x_count"]}X)'),
        ("Group", f'{score["group_size_cm"]:.1f} cm'),
        ("MPI", f'{score["mpi_x_cm"]:.1f}, {score["mpi_y_cm"]:.1f} cm'),
    ]))
    parts.append("</svg>")
    return "\n".join(parts)
```

- [ ] **Step 5: Add `_overlay_panel` and `render_overlay_svg`**

In `targets.py`, add after `_render_ipsc` (and before `render_svg`):

```python
def _overlay_panel(series, run_meta):
    x = _MARGIN_PX * 2 + _FACE_PX
    parts = [f'<line x1="{x - 8}" y1="{_MARGIN_PX}" x2="{x - 8}" '
             f'y2="{_MARGIN_PX + _FACE_PX}" stroke="#dddddd"/>']
    y = _MARGIN_PX + 18
    for label, value in [
        ("Gun", run_meta["gun"]),
        ("Ammo", run_meta["ammo"]),
        ("Shooter", run_meta["shooter"]),
        ("Range", f'{run_meta["range_m"]} m'),
        ("String", f'{run_meta["shot_count"]} rds / {run_meta["time_limit_s"]} s'),
    ]:
        parts.append(
            f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="12" '
            f'fill="#333333">{html.escape(str(label))}: '
            f'<tspan font-weight="bold">{html.escape(str(value))}</tspan></text>'
        )
        y += 20
    y += 10
    parts.append(
        f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="12" '
        f'font-weight="bold" fill="#333333">Stance comparison</text>'
    )
    y += 22
    for s in series:
        score = s["score"]
        parts.append(
            f'<rect x="{x}" y="{y - 10}" width="11" height="11" '
            f'fill="{s["color"]}" stroke="#ffffff" stroke-width="0.5"/>'
        )
        summary = (
            f'{s["label"]}: {score["group_size_cm"]:.1f} cm, '
            f'{score["total_score"]} ({score["x_count"]}X)'
        )
        parts.append(
            f'<text x="{x + 18}" y="{y}" font-family="sans-serif" '
            f'font-size="12" fill="#333333">{html.escape(summary)}</text>'
        )
        y += 18
        walk = score.get("vertical_walk_cm")
        if walk is not None:
            parts.append(
                f'<text x="{x + 18}" y="{y}" font-family="sans-serif" '
                f'font-size="10" fill="#777777">walk {walk:.1f} cm</text>'
            )
            y += 18
    return "\n".join(parts)


def render_overlay_svg(target_def, series, run_meta):
    """Render a bullseye with several color-coded shot series overlaid.

    `series` is an ordered list of dicts with keys ``label``, ``color``,
    ``shots`` (a list of shot dicts) and ``score`` (a bullseye score dict that
    may include ``vertical_walk_cm``).
    """
    parts = [_svg_open()]
    parts.extend(_bullseye_face(target_def))
    for s in series:
        parts.append(_shot_markers(s["shots"], target_def, color=s["color"]))
    parts.append(_overlay_panel(series, run_meta))
    parts.append("</svg>")
    return "\n".join(parts)
```

- [ ] **Step 6: Run the new tests and the full target suite**

Run: `python3 -m unittest tests.test_targets -v`
Expected: PASS (existing `TestBullseyeSvg`/`TestPopperSvg`/`TestIpscSvg` still pass — the refactor is output-identical — plus 4 new `TestOverlaySvg` tests).

- [ ] **Step 7: Verify the `_bullseye_face` refactor did not change committed output**

Regenerate the curated gallery and confirm no byte churn in the committed SVGs:

Run:
```bash
python3 practice.py
git diff --exit-code -- targets/*.svg targets/TARGETS.md && echo "NO CHURN"
```
Expected: `NO CHURN` (the bullseye refactor is byte-identical, so the curated
gallery files are unchanged). If there is a diff, the refactor altered output —
fix `_bullseye_face` to match the original ordering/formatting exactly.

- [ ] **Step 8: Commit**

```bash
git add targets.py tests/test_targets.py
git commit -m "feat: add color-coded multi-series bullseye overlay renderer

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: `examples.py` overlay generator

**Files:**
- Create: `examples.py`
- Test: `tests/test_examples.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_examples.py`:

```python
import os
import tempfile
import unittest

import recoil
import examples


class TestExampleOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()
        cls.gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        cls.ammo = recoil.AMMO["9x19mm Parabellum"][0]
        cls.shooter = recoil.SHOOTER["Commando Cassie"]

    def test_writes_file_and_returns_link(self):
        with tempfile.TemporaryDirectory() as d:
            link = examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            self.assertTrue(link.endswith(".svg"))
            self.assertTrue(os.path.exists(os.path.join(d, os.path.basename(link))))

    def test_three_stance_colors_in_output(self):
        with tempfile.TemporaryDirectory() as d:
            link = examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            with open(os.path.join(d, os.path.basename(link))) as fp:
                svg = fp.read()
            for color in ("#c0392b", "#2471a3", "#1e8449"):
                self.assertIn(color, svg)

    def test_deterministic_output(self):
        with tempfile.TemporaryDirectory() as d:
            link = examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            path = os.path.join(d, os.path.basename(link))
            with open(path) as fp:
                first = fp.read()
            examples.render_example_overlay(
                self.gun, self.ammo, self.shooter, "Commando Cassie", out_dir=d
            )
            with open(path) as fp:
                second = fp.read()
            self.assertEqual(first, second)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_examples -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'examples'`

- [ ] **Step 3: Create `examples.py`**

```python
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
    writes one color-coded overlay SVG. Returns the path (relative to `out_dir`)
    of the written file, suitable as a Markdown image link from the repo root.
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
```

> **Determinism note:** the per-example seed (`zlib.crc32`) and `%.1f` SVG
> coordinate formatting are stable across runs, and the file is written with an
> explicit UTF-8 / `\n` newline. Random scatter uses `random.gauss`, which is
> deterministic for a fixed seed on a given CPython version; byte-for-byte
> stability is therefore guaranteed run-to-run on the same interpreter (which is
> what the committed SVGs and the Task 4 diff check rely on).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_examples -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add examples.py tests/test_examples.py
git commit -m "feat: add examples module rendering per-example stance overlays

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: Report hook in `recoil.py`

**Files:**
- Modify: `recoil.py` (inside `show_recoil`, after the Shooter Disturbance loop)
- Test: `tests/test_examples.py` (add `TestReportHook`)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_examples.py`:

```python
import contextlib
import io


class TestReportHook(unittest.TestCase):
    def setUp(self):
        recoil.load_data()
        self.gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        self.ammo = recoil.AMMO["9x19mm Parabellum"][0]

    def test_show_recoil_emits_stance_comparison_link(self):
        original = examples.render_example_overlay
        examples.render_example_overlay = (
            lambda *a, **k: "targets/example/stub.svg"
        )
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                recoil.show_recoil(self.gun, self.ammo)
            out = buf.getvalue()
        finally:
            examples.render_example_overlay = original
        self.assertIn("5-Shot Stance Comparison", out)
        self.assertIn("![", out)
        self.assertIn("targets/example/stub.svg", out)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_examples.TestReportHook -v`
Expected: FAIL — `show_recoil` output does not yet contain `5-Shot Stance Comparison`.

- [ ] **Step 3: Add the report hook**

In `recoil.py`, in `show_recoil`, locate the end of the function:

```python
    print("\n### Shooter Disturbance")
    for shooter in SHOOTER:
        calculate_throwoff(shooter, gun, recoil_full, recoil_empty)
    print("\n")
```

Replace the final `print("\n")` with:

```python
    # 5-shot stance comparison illustration (rendered by examples.py).
    import examples
    cassie = SHOOTER.get(examples.EXAMPLE_SHOOTER)
    if cassie is None:
        print(
            f"WARNING: shooter '{examples.EXAMPLE_SHOOTER}' not found; "
            f"skipping stance comparison for {gun['name']}",
            file=sys.stderr,
        )
    else:
        link = examples.render_example_overlay(
            gun, used_ammo, cassie, examples.EXAMPLE_SHOOTER
        )
        print(
            f"\n### 5-Shot Stance Comparison "
            f"({examples.EXAMPLE_SHOOTER}, {examples.EXAMPLE_RANGE_M} m)\n"
        )
        print(
            f"![5-shot stance comparison for {gun['name']} with "
            f"{used_ammo['name']} at {examples.EXAMPLE_RANGE_M} m]({link})\n"
        )
    print("\n")
```

(The lazy `import examples` inside the function avoids an **import-time** cycle:
`examples` imports `simulation`, which imports `recoil`. Note that under
`python3 recoil.py` the active generator module is `__main__`, so this lazy
import causes a second `recoil` module object to be created with `AMMO`/
`WEAPONS`/`SHOOTER` still `None`; that is harmless because `examples`/
`simulation` only call `calculate_free_recoil`, `get_gun_defaults`, and
`calculate_disturbance`, which read their passed-in records and module constants,
never those globals.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_examples -v`
Expected: PASS (4 tests total in the file).

- [ ] **Step 5: Commit**

```bash
git add recoil.py tests/test_examples.py
git commit -m "feat: embed stance-comparison SVG link in recoil report output

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: Regenerate EXAMPLE.md, commit SVGs, update README

**Files:**
- Regenerate: `EXAMPLE.md`
- Create: `targets/example/*.svg` (27 files)
- Modify: `README.md`

- [ ] **Step 1: Regenerate the report and SVGs**

Run: `python3 recoil.py > EXAMPLE.md`
Expected: exits 0; `EXAMPLE.md` updated; `targets/example/` now contains one
`.svg` per weapon/ammo combination (26 with the current data).

- [ ] **Step 2: Verify the artifacts**

Run:
```bash
EXPECTED=$(python3 -c "import recoil; recoil.load_data(); print(sum(len(recoil.WEAPONS[g])*len(recoil.AMMO[g]) for g in recoil.WEAPONS if g in recoil.AMMO))")
echo "expected combos: $EXPECTED"
ls targets/example/*.svg | wc -l
grep -c "5-Shot Stance Comparison" EXAMPLE.md
grep -c "](targets/example/" EXAMPLE.md
```
Expected: all three counts equal `$EXPECTED` (currently `26`).

- [ ] **Step 3: Verify determinism (re-run produces no diff)**

Run:
```bash
python3 recoil.py > /tmp/EXAMPLE_rerun.md
diff EXAMPLE.md /tmp/EXAMPLE_rerun.md && echo "STABLE"
git status --porcelain targets/example/
```
Expected: `STABLE`; re-running does not change committed SVG bytes (no unexpected churn after the first generation).

- [ ] **Step 4: Update README**

In `README.md`, in the "Target Practice Renderer" subsection, add a sentence:

```markdown
`EXAMPLE.md` additionally embeds, per weapon/ammo example, a 5-shot
stance-comparison target: Commando Cassie firing five rounds at 25 m in the
standing, crouching, and prone stances, color-coded on one bullseye. These
SVGs are generated into `targets/example/` by `python3 recoil.py`.
```

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m unittest discover -s tests`
Expected: OK (all prior tests plus the new overlay/examples/report-hook tests).

- [ ] **Step 6: Commit**

```bash
git add EXAMPLE.md README.md targets/example
git commit -m "docs: regenerate EXAMPLE.md with per-example stance-comparison SVGs

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Notes for the implementer

- Run all tests from the repo root so `recoil.load_data()` finds `ammo.json`,
  `guns.json`, `shooters.json` in the working directory.
- Do not modify the recoil physics functions (`calculate_free_recoil`,
  `calculate_disturbance`, `get_gun_defaults`, `calculate_recoil`). Only the
  report output (`show_recoil`) changes in `recoil.py`.
- Keep pure standard library; follow the repo convention of returning dicts and
  raising `ValueError` with a clear message for invalid inputs (delegated here
  to the existing `simulate_string`/`score_string`/`TARGET_DEFS` lookups).
