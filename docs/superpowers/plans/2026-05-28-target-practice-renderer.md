# Target Practice Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simulate strings of shots driven by the existing recoil model and render authentic SVG bullseye, IPSC silhouette, and popper targets that visibly demonstrate how recoil, shooter skill, weapon, ammunition, and firing cadence affect shot placement.

**Architecture:** Small single-responsibility modules around the unchanged `recoil.py` physics engine: `simulation.py` (recoil + behaviour → shot coordinates), `scoring.py` (impacts → score), `targets.py` (target geometry + SVG), and `practice.py` (orchestration + Markdown gallery). New data lives in `scenarios.json`; `shooters.json` gains a `handedness` field. All functions are pure over plain dicts/lists, matching the repo's existing dict-returning style.

**Tech Stack:** Python 3 standard library only (no external dependencies). Tests use `unittest` run via `python3 -m unittest`.

---

## Reference: existing `recoil.py` contract (do NOT modify this file)

- `recoil.load_data()` — populates module globals `AMMO`, `WEAPONS`, `SHOOTER` from `ammo.json`, `guns.json`, `shooters.json` (read relative to the current working directory).
- `recoil.get_gun_defaults(gun)` — returns the gun dict merged over type defaults (`action_type`, `support_class`, `bore_offset`).
- `recoil.calculate_free_recoil(gun, ammo, configuration)` — `configuration` is `"full"` or `"empty"`. Returns a dict containing `system_mass_kg`, `ejecta_momentum`, `free_recoil_energy`, `nominal_velocity`, `actual_velocity`.
- `recoil.calculate_disturbance(shooterdata, gun, recoil_data, stance)` — `recoil_data` must contain `system_mass_kg` and `ejecta_momentum`. `stance` is `"standing"`/`"crouching"`/`"prone"`. Returns a dict containing `aim_kick_rad`, `recovery_seconds`, `support_class`, `control_factor`, `action_sharpness`.

Key data shapes (from the repo's JSON):
- `guns.json`: `{ "<caliber>": [ {"name","type","barrel_length","mass","mag_mass","capacity"}, ... ] }`
- `ammo.json`: `{ "<caliber>": [ {"name","type","bullet_mass","propellant_mass","ref_barrel","v_muzzle","cartridge_mass"}, ... ] }`
- `shooters.json`: `{ "<display name>": {"weight","height","strength","skill","injured_hand"} }`

**Coordinate convention used throughout simulation & scoring:** origin = point of aim, `x` positive = right, `y` positive = up, units = **centimetres on the target plane**. (SVG rendering flips `y` because SVG's axis points down.)

**Test command convention:** run from the repo root, e.g. `python3 -m unittest tests.test_simulation -v`. The full suite is `python3 -m unittest`.

---

## Task 1: Data files — shooter handedness and scenarios

**Files:**
- Modify: `shooters.json`
- Create: `scenarios.json`
- Test: `tests/test_data.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_data.py`:

```python
import json
import unittest


class TestDataFiles(unittest.TestCase):
    def test_every_shooter_has_handedness(self):
        with open("shooters.json", "r") as fp:
            shooters = json.load(fp)
        self.assertTrue(shooters, "shooters.json must not be empty")
        for name, data in shooters.items():
            self.assertIn("handedness", data, f"{name} missing handedness")
            self.assertIn(data["handedness"], ("right", "left"))

    def test_scenarios_have_required_fields(self):
        with open("scenarios.json", "r") as fp:
            scenarios = json.load(fp)
        self.assertTrue(scenarios, "scenarios.json must not be empty")
        required = {
            "name", "target", "range_m", "caliber",
            "gun", "ammo", "shooter", "shot_count", "time_limit_s",
            "stance", "seed",
        }
        for scenario in scenarios:
            missing = required - set(scenario.keys())
            self.assertFalse(missing, f"{scenario.get('name')} missing {missing}")
            self.assertIn(scenario["target"], ("bullseye", "ipsc_silhouette", "popper"))
            self.assertIn(scenario["stance"], ("standing", "crouching", "prone"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_data -v`
Expected: FAIL — `shooters.json` entries lack `handedness`, and `scenarios.json` does not exist (`FileNotFoundError`).

- [ ] **Step 3: Add `handedness` to every shooter in `shooters.json`**

Add `"handedness": "right"` to each shooter object, and make one shooter left-handed for demonstration. The file becomes:

```json
{
  "Alice Smallframe": {
    "weight": 45000,
    "height": 1570,
    "strength": 5,
    "skill": 1,
    "injured_hand": false,
    "handedness": "right"
  },
  "Burly Bob": {
    "weight": 82000,
    "height": 1950,
    "strength": 8,
    "skill": 5,
    "injured_hand": false,
    "handedness": "left"
  },
  "Commando Cassie": {
    "weight": 58000,
    "height": 1640,
    "strength": 6,
    "skill": 8,
    "injured_hand": false,
    "handedness": "right"
  },
  "Damaged Dan": {
    "weight": 75000,
    "height": 1780,
    "strength": 3,
    "skill": 5,
    "injured_hand": true,
    "handedness": "right"
  }
}
```

- [ ] **Step 4: Create `scenarios.json` with the curated comparison set**

Create `scenarios.json`. These scenarios reference existing gun/ammo/shooter records and tell three comparison stories (skill, cadence, weapon):

```json
[
  {
    "name": "Skill comparison - Alice (novice) rapid fire",
    "target": "bullseye",
    "range_m": 25,
    "caliber": "9x19mm Parabellum",
    "gun": "Glock 17",
    "ammo": "9x19mm 115 gr Federal FMJ",
    "shooter": "Alice Smallframe",
    "shot_count": 5,
    "time_limit_s": 10,
    "stance": "standing",
    "seed": 1
  },
  {
    "name": "Skill comparison - Commando Cassie (expert) rapid fire",
    "target": "bullseye",
    "range_m": 25,
    "caliber": "9x19mm Parabellum",
    "gun": "Glock 17",
    "ammo": "9x19mm 115 gr Federal FMJ",
    "shooter": "Commando Cassie",
    "shot_count": 5,
    "time_limit_s": 10,
    "stance": "standing",
    "seed": 1
  },
  {
    "name": "Cadence comparison - Cassie slow fire",
    "target": "bullseye",
    "range_m": 25,
    "caliber": "9x19mm Parabellum",
    "gun": "Glock 17",
    "ammo": "9x19mm 115 gr Federal FMJ",
    "shooter": "Commando Cassie",
    "shot_count": 5,
    "time_limit_s": 50,
    "stance": "standing",
    "seed": 2
  },
  {
    "name": "Cadence comparison - Cassie rapid fire",
    "target": "bullseye",
    "range_m": 25,
    "caliber": "9x19mm Parabellum",
    "gun": "Glock 17",
    "ammo": "9x19mm 115 gr Federal FMJ",
    "shooter": "Commando Cassie",
    "shot_count": 5,
    "time_limit_s": 5,
    "stance": "standing",
    "seed": 2
  },
  {
    "name": "Weapon comparison - Glock 17 popper speed string",
    "target": "popper",
    "range_m": 10,
    "caliber": "9x19mm Parabellum",
    "gun": "Glock 17",
    "ammo": "9x19mm 115 gr Federal FMJ",
    "shooter": "Commando Cassie",
    "shot_count": 3,
    "time_limit_s": 1.5,
    "stance": "standing",
    "seed": 3
  },
  {
    "name": "Weapon comparison - MP5-N popper speed string",
    "target": "popper",
    "range_m": 10,
    "caliber": "9x19mm Parabellum",
    "gun": "MP5-N",
    "ammo": "9x19mm 115 gr Federal FMJ",
    "shooter": "Commando Cassie",
    "shot_count": 3,
    "time_limit_s": 1.5,
    "stance": "standing",
    "seed": 3
  },
  {
    "name": "Practical scoring - Cassie IPSC silhouette",
    "target": "ipsc_silhouette",
    "range_m": 10,
    "caliber": "9x19mm Parabellum",
    "gun": "Glock 17",
    "ammo": "9x19mm 115 gr Federal FMJ",
    "shooter": "Commando Cassie",
    "shot_count": 6,
    "time_limit_s": 4,
    "stance": "standing",
    "seed": 4
  }
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m unittest tests.test_data -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add shooters.json scenarios.json tests/test_data.py
git commit -m "feat: add shooter handedness and scenario definitions

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 2: `simulation.py` — per-shot recoil with magazine depletion

**Files:**
- Create: `simulation.py`
- Test: `tests/test_simulation.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_simulation.py`:

```python
import unittest

import recoil
import simulation


class TestRoundRecoil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()
        cls.gun = recoil.WEAPONS["9x19mm Parabellum"][2]  # Glock 17, capacity 17
        cls.ammo = recoil.AMMO["9x19mm Parabellum"][0]

    def test_fewer_rounds_means_more_free_recoil_energy(self):
        full = simulation.round_recoil_data(self.gun, self.ammo, 17)
        nearly_empty = simulation.round_recoil_data(self.gun, self.ammo, 1)
        self.assertLess(full["system_mass_kg"], nearly_empty["system_mass_kg"] + 1)
        self.assertGreater(
            nearly_empty["free_recoil_energy"], full["free_recoil_energy"]
        )

    def test_ejecta_momentum_is_independent_of_round_count(self):
        full = simulation.round_recoil_data(self.gun, self.ammo, 17)
        nearly_empty = simulation.round_recoil_data(self.gun, self.ammo, 1)
        self.assertAlmostEqual(
            full["ejecta_momentum"], nearly_empty["ejecta_momentum"], places=9
        )

    def test_full_magazine_matches_recoil_full_configuration(self):
        ref = recoil.calculate_free_recoil(self.gun, self.ammo, "full")
        got = simulation.round_recoil_data(self.gun, self.ammo, self.gun["capacity"])
        self.assertAlmostEqual(got["system_mass_kg"], ref["system_mass_kg"], places=9)
        self.assertAlmostEqual(
            got["free_recoil_energy"], ref["free_recoil_energy"], places=9
        )

    def test_empty_magazine_matches_recoil_empty_configuration(self):
        ref = recoil.calculate_free_recoil(self.gun, self.ammo, "empty")
        got = simulation.round_recoil_data(self.gun, self.ammo, 0)
        self.assertAlmostEqual(got["system_mass_kg"], ref["system_mass_kg"], places=9)
        self.assertAlmostEqual(
            got["free_recoil_energy"], ref["free_recoil_energy"], places=9
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_simulation -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'simulation'`.

- [ ] **Step 3: Create `simulation.py` with the round-recoil helper**

```python
"""Simulates strings of shots using the recoil model and shooter behaviour."""

import random

import recoil


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
        "free_recoil_energy": ejecta_momentum ** 2 / (2 * system_mass_kg),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_simulation -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add simulation.py tests/test_simulation.py
git commit -m "feat: add per-shot recoil with magazine depletion

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 3: `simulation.py` — `simulate_string` core (muzzle climb, recovery, projection, determinism)

**Files:**
- Modify: `simulation.py`
- Test: `tests/test_simulation.py`

This task adds the shot loop with muzzle climb and active compensation, but **without** flinch or scatter yet (those come in Task 4), so the climb behaviour can be tested in isolation. With scatter disabled, shot 0 lands exactly at the point of aim.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_simulation.py`:

```python
class TestSimulateStringClimb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()
        cls.gun = recoil.WEAPONS["9x19mm Parabellum"][2]  # Glock 17
        cls.ammo = recoil.AMMO["9x19mm Parabellum"][0]
        cls.shooter = dict(recoil.SHOOTER["Commando Cassie"])

    def _scenario(self, time_limit_s, range_m=25, shot_count=5):
        return {
            "range_m": range_m,
            "shot_count": shot_count,
            "time_limit_s": time_limit_s,
            "stance": "standing",
            "seed": 1,
        }

    def test_returns_one_shot_per_round(self):
        shots = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(10),
            flinch=False, scatter=False,
        )
        self.assertEqual(len(shots), 5)
        self.assertEqual([s["shot_index"] for s in shots], [0, 1, 2, 3, 4])

    def test_first_shot_is_on_point_of_aim_without_flinch_or_scatter(self):
        shots = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(10),
            flinch=False, scatter=False,
        )
        self.assertAlmostEqual(shots[0]["x_cm"], 0.0, places=6)
        self.assertAlmostEqual(shots[0]["y_cm"], 0.0, places=6)

    def test_rapid_fire_walks_up_more_than_slow_fire(self):
        slow = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(50),
            flinch=False, scatter=False,
        )
        rapid = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(2),
            flinch=False, scatter=False,
        )
        slow_walk = slow[-1]["y_cm"] - slow[0]["y_cm"]
        rapid_walk = rapid[-1]["y_cm"] - rapid[0]["y_cm"]
        self.assertGreater(rapid_walk, slow_walk)
        self.assertGreater(rapid_walk, 0.0)

    def test_longer_range_scales_offsets_linearly(self):
        near = simulation.simulate_string(
            self.gun, self.ammo, self.shooter,
            self._scenario(2, range_m=10), flinch=False, scatter=False,
        )
        far = simulation.simulate_string(
            self.gun, self.ammo, self.shooter,
            self._scenario(2, range_m=20), flinch=False, scatter=False,
        )
        # Same angles, double the range -> double the linear offset.
        self.assertAlmostEqual(far[-1]["y_cm"], near[-1]["y_cm"] * 2, places=4)

    def test_deterministic_with_seed(self):
        a = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(2)
        )
        b = simulation.simulate_string(
            self.gun, self.ammo, self.shooter, self._scenario(2)
        )
        self.assertEqual(a, b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_simulation.TestSimulateStringClimb -v`
Expected: FAIL — `AttributeError: module 'simulation' has no attribute 'simulate_string'`.

- [ ] **Step 3: Add tunable constants and `simulate_string` to `simulation.py`**

Add the constants block below the imports, and append the function. (Flinch/scatter constants are included now so Task 4 only adds code that uses them.)

```python
# --- Behaviour tuning constants -------------------------------------------
# These are initial values. They are tuned during implementation so that a
# relaxed expert groups inside the bullseye 10-ring and shot zero sits on the
# point of aim. The TEST SUITE asserts only DIRECTIONAL/RELATIVE behaviour, so
# it remains valid as these constants are adjusted.

# Active compensation between shots: effectiveness in [0, 1] of cancelling the
# accumulated muzzle climb before the next shot.
COMP_BASE = 0.55       # baseline fraction of climb a shooter cancels
COMP_SKILL = 0.06      # additional effectiveness per skill point

# Anticipation / flinch: a systematic pre-shot push, down and toward the
# trigger hand. Scales with recoil energy and time pressure; reduced by skill
# and strength.
FLINCH_BASE = 0.0009          # rad per joule of free-recoil energy
FLINCH_LATERAL_FRAC = 0.5     # lateral push as a fraction of the downward push
SKILL_FLINCH = 0.10           # skill reduction per point
STR_FLINCH = 0.04             # strength reduction per point
PRESSURE_FLINCH = 0.5         # extra flinch per unit of time pressure

# Random scatter (inherent wobble), expressed as an angular sigma in radians.
SCATTER_BASE = 0.0006         # baseline sigma
SKILL_SCATTER = 0.18          # skill reduction per point
PRESSURE_SCATTER = 0.5        # extra sigma per unit of time pressure
RECOIL_SCATTER = 0.03         # extra sigma per joule of free-recoil energy


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

        if flinch:
            flinch_mag = (
                FLINCH_BASE * energy
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
```

Note: flinch and scatter are gated independently so tests can isolate the
deterministic muzzle-climb trace (`flinch=False, scatter=False`), the
systematic flinch bias (`flinch=True, scatter=False`), or the full model.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_simulation -v`
Expected: PASS (all `TestRoundRecoil` and `TestSimulateStringClimb` tests).

- [ ] **Step 5: Commit**

```bash
git add simulation.py tests/test_simulation.py
git commit -m "feat: add shot-string simulation with muzzle climb and recovery

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 4: `simulation.py` — flinch bias and scatter behaviour tests

**Files:**
- Test: `tests/test_simulation.py`

The implementation already exists (added in Task 3). This task adds the tests that lock in the flinch-direction and skill-related behaviour. If any test fails, adjust the relevant constant in `simulation.py` (e.g. increase `FLINCH_BASE` so the bias dominates scatter) until the directional behaviour holds — do not weaken the assertions.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_simulation.py`:

```python
def _group_size_cm(shots):
    biggest = 0.0
    for i in range(len(shots)):
        for j in range(i + 1, len(shots)):
            dx = shots[i]["x_cm"] - shots[j]["x_cm"]
            dy = shots[i]["y_cm"] - shots[j]["y_cm"]
            biggest = max(biggest, (dx * dx + dy * dy) ** 0.5)
    return biggest


class TestFlinchAndScatter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()
        cls.gun = recoil.WEAPONS["9x19mm Parabellum"][2]  # Glock 17
        cls.ammo = recoil.AMMO["9x19mm Parabellum"][0]

    def _scenario(self):
        return {
            "range_m": 25,
            "shot_count": 8,
            "time_limit_s": 4,
            "stance": "standing",
            "seed": 7,
        }

    def test_right_handed_flinch_pushes_low_left(self):
        shooter = dict(recoil.SHOOTER["Alice Smallframe"], handedness="right")
        # Shot 0 has zero accumulated climb, so its offset is pure flinch bias.
        shots = simulation.simulate_string(
            self.gun, self.ammo, shooter, self._scenario(),
            flinch=True, scatter=False,
        )
        self.assertLess(shots[0]["x_cm"], 0.0)  # left
        self.assertLess(shots[0]["y_cm"], 0.0)  # low

    def test_left_handed_flinch_mirrors_to_low_right(self):
        right = dict(recoil.SHOOTER["Alice Smallframe"], handedness="right")
        left = dict(recoil.SHOOTER["Alice Smallframe"], handedness="left")
        right_shots = simulation.simulate_string(
            self.gun, self.ammo, right, self._scenario(),
            flinch=True, scatter=False,
        )
        left_shots = simulation.simulate_string(
            self.gun, self.ammo, left, self._scenario(),
            flinch=True, scatter=False,
        )
        # The lateral flinch flips sign for a left-handed shooter (shot 0).
        self.assertGreater(left_shots[0]["x_cm"], right_shots[0]["x_cm"])
        self.assertGreater(left_shots[0]["x_cm"], 0.0)

    def test_higher_skill_shrinks_the_group(self):
        novice = dict(recoil.SHOOTER["Alice Smallframe"], skill=1, handedness="right")
        expert = dict(recoil.SHOOTER["Alice Smallframe"], skill=8, handedness="right")
        novice_group = _group_size_cm(
            simulation.simulate_string(self.gun, self.ammo, novice, self._scenario())
        )
        expert_group = _group_size_cm(
            simulation.simulate_string(self.gun, self.ammo, expert, self._scenario())
        )
        self.assertLess(expert_group, novice_group)

    def test_higher_skill_reduces_flinch_bias(self):
        novice = dict(recoil.SHOOTER["Alice Smallframe"], skill=1, handedness="right")
        expert = dict(recoil.SHOOTER["Alice Smallframe"], skill=8, handedness="right")
        # Compare the pure flinch bias on shot 0 (zero climb, no scatter).
        novice_low = -simulation.simulate_string(
            self.gun, self.ammo, novice, self._scenario(),
            flinch=True, scatter=False,
        )[0]["y_cm"]
        expert_low = -simulation.simulate_string(
            self.gun, self.ammo, expert, self._scenario(),
            flinch=True, scatter=False,
        )[0]["y_cm"]
        self.assertLess(expert_low, novice_low)

    def test_higher_skill_reduces_vertical_walk(self):
        novice = dict(recoil.SHOOTER["Alice Smallframe"], skill=1, handedness="right")
        expert = dict(recoil.SHOOTER["Alice Smallframe"], skill=8, handedness="right")
        novice_shots = simulation.simulate_string(
            self.gun, self.ammo, novice, self._scenario(),
            flinch=False, scatter=False,
        )
        expert_shots = simulation.simulate_string(
            self.gun, self.ammo, expert, self._scenario(),
            flinch=False, scatter=False,
        )
        novice_walk = novice_shots[-1]["y_cm"] - novice_shots[0]["y_cm"]
        expert_walk = expert_shots[-1]["y_cm"] - expert_shots[0]["y_cm"]
        self.assertLess(expert_walk, novice_walk)
```

- [ ] **Step 2: Run test to verify it (passes or guides tuning)**

Run: `python3 -m unittest tests.test_simulation.TestFlinchAndScatter -v`
Expected: PASS (5 tests). If a directional assertion fails, increase the dominant constant (`FLINCH_BASE` for bias-direction tests, `SKILL_SCATTER`/`SKILL_FLINCH` for skill tests) in `simulation.py` and re-run until all pass.

- [ ] **Step 3: Run the whole simulation suite**

Run: `python3 -m unittest tests.test_simulation -v`
Expected: PASS (all classes).

- [ ] **Step 4: Commit**

```bash
git add simulation.py tests/test_simulation.py
git commit -m "test: lock in flinch direction and skill behaviour

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 5: `scoring.py` — bullseye scorer

**Files:**
- Create: `scoring.py`
- Test: `tests/test_scoring.py`

`score_string(shots, target_def)` dispatches on `target_def["type"]`. Target-def dict shapes are documented in Task 8 (where the canonical definitions live); the scorer only consumes plain dicts, so tests build their own inline.

- [ ] **Step 1: Write the failing test**

Create `tests/test_scoring.py`:

```python
import unittest

import scoring


BULLSEYE = {
    "type": "bullseye",
    "name": "Test Bull",
    # (score, outer_radius_cm), inner ring first
    "rings": [
        (10, 2.5), (9, 5.0), (8, 7.5), (7, 10.0),
        (6, 12.5), (5, 15.0), (4, 17.5), (3, 20.0),
        (2, 22.5), (1, 25.0),
    ],
    "x_ring_radius_cm": 1.25,
    "black_radius_cm": 10.0,
    "size_cm": 55.0,
}


class TestBullseyeScoring(unittest.TestCase):
    def test_center_hit_scores_ten_and_x(self):
        shots = [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertEqual(result["total_score"], 10)
        self.assertEqual(result["x_count"], 1)

    def test_ring_boundaries_score_correctly(self):
        shots = [
            {"x_cm": 0.0, "y_cm": 4.0, "shot_index": 0, "time_s": 0.0},   # 9 ring
            {"x_cm": 0.0, "y_cm": 9.0, "shot_index": 1, "time_s": 0.0},   # 7 ring
            {"x_cm": 0.0, "y_cm": 24.0, "shot_index": 2, "time_s": 0.0},  # 1 ring
        ]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertEqual(result["total_score"], 9 + 7 + 1)

    def test_miss_outside_outer_ring_scores_zero(self):
        shots = [{"x_cm": 30.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertEqual(result["total_score"], 0)

    def test_reports_group_size_and_mpi(self):
        shots = [
            {"x_cm": 1.0, "y_cm": 1.0, "shot_index": 0, "time_s": 0.0},
            {"x_cm": -1.0, "y_cm": -1.0, "shot_index": 1, "time_s": 0.0},
        ]
        result = scoring.score_string(shots, BULLSEYE)
        self.assertAlmostEqual(result["group_size_cm"], (8.0) ** 0.5, places=6)
        self.assertAlmostEqual(result["mpi_x_cm"], 0.0, places=6)
        self.assertAlmostEqual(result["mpi_y_cm"], 0.0, places=6)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_scoring -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scoring'`.

- [ ] **Step 3: Create `scoring.py` with shared helpers and the bullseye scorer**

```python
"""Scores a simulated shot string against a target definition."""

import math


def _distance(shot):
    return math.hypot(shot["x_cm"], shot["y_cm"])


def _group_size_cm(shots):
    biggest = 0.0
    for i in range(len(shots)):
        for j in range(i + 1, len(shots)):
            dx = shots[i]["x_cm"] - shots[j]["x_cm"]
            dy = shots[i]["y_cm"] - shots[j]["y_cm"]
            biggest = max(biggest, math.hypot(dx, dy))
    return biggest


def _mpi(shots):
    n = len(shots)
    if n == 0:
        return 0.0, 0.0
    return (
        sum(s["x_cm"] for s in shots) / n,
        sum(s["y_cm"] for s in shots) / n,
    )


def _score_bullseye(shots, target_def):
    rings = target_def["rings"]  # inner-first list of (score, outer_radius_cm)
    x_radius = target_def["x_ring_radius_cm"]
    total = 0
    x_count = 0
    per_shot = []
    for shot in shots:
        d = _distance(shot)
        score = 0
        for ring_score, radius in rings:
            if d <= radius:
                score = ring_score
                break
        total += score
        is_x = d <= x_radius
        if is_x:
            x_count += 1
        per_shot.append({"shot_index": shot["shot_index"], "score": score, "x": is_x})
    mpi_x, mpi_y = _mpi(shots)
    return {
        "target": "bullseye",
        "total_score": total,
        "x_count": x_count,
        "group_size_cm": _group_size_cm(shots),
        "mpi_x_cm": mpi_x,
        "mpi_y_cm": mpi_y,
        "per_shot": per_shot,
    }


def score_string(shots, target_def):
    """Score `shots` against `target_def`, dispatching on its ``type``."""
    target_type = target_def["type"]
    if target_type == "bullseye":
        return _score_bullseye(shots, target_def)
    raise ValueError(
        f"Invalid target type '{target_type}'. "
        f"Valid types are: bullseye, ipsc_silhouette, popper"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_scoring -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scoring.py tests/test_scoring.py
git commit -m "feat: add bullseye scoring

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 6: `scoring.py` — popper scorer

**Files:**
- Modify: `scoring.py`
- Test: `tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_scoring.py`:

```python
POPPER = {
    "type": "popper",
    "name": "Test Popper",
    "head_radius_cm": 15.0,    # round head centred on the point of aim
    "body_top_y_cm": -8.0,     # top edge of the body, below the aim point
    "body_width_cm": 20.0,
    "body_height_cm": 60.0,
    "size_cm": 80.0,
}


class TestPopperScoring(unittest.TestCase):
    def test_first_hit_neutralizes_and_records_shot_and_time(self):
        shots = [
            {"x_cm": 30.0, "y_cm": 30.0, "shot_index": 0, "time_s": 0.0},   # miss
            {"x_cm": 2.0, "y_cm": 1.0, "shot_index": 1, "time_s": 0.4},     # head hit
            {"x_cm": 0.0, "y_cm": 0.0, "shot_index": 2, "time_s": 0.8},
        ]
        result = scoring.score_string(shots, POPPER)
        self.assertTrue(result["neutralized"])
        self.assertEqual(result["shots_to_neutralize"], 2)
        self.assertAlmostEqual(result["time_to_hit_s"], 0.4, places=6)

    def test_body_hit_counts(self):
        shots = [{"x_cm": 0.0, "y_cm": -40.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, POPPER)
        self.assertTrue(result["neutralized"])

    def test_all_misses_not_neutralized(self):
        shots = [{"x_cm": 100.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, POPPER)
        self.assertFalse(result["neutralized"])
        self.assertIsNone(result["shots_to_neutralize"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_scoring.TestPopperScoring -v`
Expected: FAIL — `ValueError: Invalid target type 'popper'`.

- [ ] **Step 3: Add the popper scorer and register it**

Add this function to `scoring.py`:

```python
def _hits_popper(shot, target_def):
    x, y = shot["x_cm"], shot["y_cm"]
    head_r = target_def["head_radius_cm"]
    if math.hypot(x, y) <= head_r:
        return True
    half_w = target_def["body_width_cm"] / 2.0
    top = target_def["body_top_y_cm"]
    bottom = top - target_def["body_height_cm"]
    return (-half_w <= x <= half_w) and (bottom <= y <= top)


def _score_popper(shots, target_def):
    neutralized = False
    shots_to_neutralize = None
    time_to_hit = None
    for shot in shots:
        if _hits_popper(shot, target_def):
            neutralized = True
            shots_to_neutralize = shot["shot_index"] + 1
            time_to_hit = shot["time_s"]
            break
    return {
        "target": "popper",
        "neutralized": neutralized,
        "shots_to_neutralize": shots_to_neutralize,
        "time_to_hit_s": time_to_hit,
        "group_size_cm": _group_size_cm(shots),
    }
```

Then add a branch in `score_string` before the `raise`:

```python
    if target_type == "popper":
        return _score_popper(shots, target_def)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_scoring -v`
Expected: PASS (all bullseye + popper tests).

- [ ] **Step 5: Commit**

```bash
git add scoring.py tests/test_scoring.py
git commit -m "feat: add popper knock-down scoring

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 7: `scoring.py` — IPSC silhouette scorer

**Files:**
- Modify: `scoring.py`
- Test: `tests/test_scoring.py`

The silhouette uses simplified concentric elliptical zones (A/C/D) centred on the point of aim. Minor power-factor scoring: A=5, C=3, D=1. Hit factor = total points / string time.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_scoring.py`:

```python
IPSC = {
    "type": "ipsc_silhouette",
    "name": "Test IPSC",
    # (label, points, half_width_cm, half_height_cm), inner zone first
    "zones": [
        ("A", 5, 7.5, 15.0),
        ("C", 3, 15.0, 23.0),
        ("D", 1, 22.5, 30.0),
    ],
    "size_cm": 70.0,
}


class TestIpscScoring(unittest.TestCase):
    def test_center_is_alpha(self):
        shots = [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, IPSC, string_time_s=2.0)
        self.assertEqual(result["total_points"], 5)
        self.assertEqual(result["zone_counts"]["A"], 1)

    def test_zone_breakdown_and_miss(self):
        shots = [
            {"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0},    # A
            {"x_cm": 12.0, "y_cm": 0.0, "shot_index": 1, "time_s": 0.0},   # C
            {"x_cm": 0.0, "y_cm": 28.0, "shot_index": 2, "time_s": 0.0},   # D
            {"x_cm": 50.0, "y_cm": 0.0, "shot_index": 3, "time_s": 0.0},   # miss
        ]
        result = scoring.score_string(shots, IPSC, string_time_s=2.0)
        self.assertEqual(result["total_points"], 5 + 3 + 1)
        self.assertEqual(result["zone_counts"]["A"], 1)
        self.assertEqual(result["zone_counts"]["C"], 1)
        self.assertEqual(result["zone_counts"]["D"], 1)
        self.assertEqual(result["misses"], 1)

    def test_hit_factor_is_points_over_time(self):
        shots = [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0}]
        result = scoring.score_string(shots, IPSC, string_time_s=2.5)
        self.assertAlmostEqual(result["hit_factor"], 5 / 2.5, places=6)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_scoring.TestIpscScoring -v`
Expected: FAIL — `score_string()` got an unexpected keyword argument `string_time_s` (and missing `ipsc_silhouette` branch).

- [ ] **Step 3: Add the IPSC scorer, the `string_time_s` parameter, and register it**

Add this function to `scoring.py`:

```python
def _score_ipsc(shots, target_def, string_time_s):
    zones = target_def["zones"]  # inner-first list of (label, points, hw, hh)
    total = 0
    misses = 0
    zone_counts = {label: 0 for label, _pts, _hw, _hh in zones}
    for shot in shots:
        x, y = shot["x_cm"], shot["y_cm"]
        matched = None
        for label, points, hw, hh in zones:
            if (x / hw) ** 2 + (y / hh) ** 2 <= 1.0:
                matched = (label, points)
                break
        if matched is None:
            misses += 1
        else:
            label, points = matched
            zone_counts[label] += 1
            total += points
    hit_factor = total / string_time_s if string_time_s and string_time_s > 0 else 0.0
    return {
        "target": "ipsc_silhouette",
        "total_points": total,
        "zone_counts": zone_counts,
        "misses": misses,
        "hit_factor": hit_factor,
        "group_size_cm": _group_size_cm(shots),
    }
```

Change the `score_string` signature and add the branch:

```python
def score_string(shots, target_def, string_time_s=None):
    """Score `shots` against `target_def`, dispatching on its ``type``.

    `string_time_s` is the total string time used for IPSC hit-factor scoring;
    it is ignored by other target types.
    """
    target_type = target_def["type"]
    if target_type == "bullseye":
        return _score_bullseye(shots, target_def)
    if target_type == "popper":
        return _score_popper(shots, target_def)
    if target_type == "ipsc_silhouette":
        return _score_ipsc(shots, target_def, string_time_s)
    raise ValueError(
        f"Invalid target type '{target_type}'. "
        f"Valid types are: bullseye, ipsc_silhouette, popper"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_scoring -v`
Expected: PASS (all bullseye + popper + IPSC tests).

- [ ] **Step 5: Commit**

```bash
git add scoring.py tests/test_scoring.py
git commit -m "feat: add IPSC silhouette scoring with hit factor

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 8: `targets.py` — target definitions and bullseye SVG

**Files:**
- Create: `targets.py`
- Test: `tests/test_targets.py`

`targets.py` owns the canonical target definitions (`TARGET_DEFS`, keyed by the `target` string used in scenarios) and the SVG renderer. The renderer maps target-plane cm → SVG pixels, flipping `y` (SVG y points down). The run's stats render in a side panel beside the target face.

- [ ] **Step 1: Write the failing test**

Create `tests/test_targets.py`:

```python
import unittest

import targets


class TestTargetDefs(unittest.TestCase):
    def test_all_three_targets_defined(self):
        self.assertIn("bullseye", targets.TARGET_DEFS)
        self.assertIn("popper", targets.TARGET_DEFS)
        self.assertIn("ipsc_silhouette", targets.TARGET_DEFS)
        for key, td in targets.TARGET_DEFS.items():
            self.assertEqual(td["type"], key)


class TestBullseyeSvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["bullseye"]
        self.shots = [
            {"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0},
            {"x_cm": 2.0, "y_cm": -3.0, "shot_index": 1, "time_s": 0.5},
        ]
        self.score = {
            "target": "bullseye", "total_score": 19, "x_count": 1,
            "group_size_cm": 3.6, "mpi_x_cm": 1.0, "mpi_y_cm": -1.5,
            "per_shot": [], "vertical_walk_cm": -3.0,
        }
        self.run_meta = {
            "scenario": "Test", "gun": "Glock 17", "ammo": "FMJ",
            "shooter": "Cassie", "range_m": 25, "shot_count": 2,
            "time_limit_s": 5,
        }

    def test_returns_well_formed_svg_string(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertIn("</svg>", svg)

    def test_draws_one_marker_per_shot(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertEqual(svg.count('class="shot"'), len(self.shots))

    def test_includes_stats_panel_text(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertIn("Glock 17", svg)
        self.assertIn("Cassie", svg)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_targets -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'targets'`.

- [ ] **Step 3: Create `targets.py` with defs and bullseye renderer**

```python
"""Target geometry definitions and authentic SVG target rendering."""

import html

TARGET_DEFS = {
    "bullseye": {
        "type": "bullseye",
        "name": "ISSF 25 m Precision",
        "rings": [
            (10, 2.5), (9, 5.0), (8, 7.5), (7, 10.0),
            (6, 12.5), (5, 15.0), (4, 17.5), (3, 20.0),
            (2, 22.5), (1, 25.0),
        ],
        "x_ring_radius_cm": 1.25,
        "black_radius_cm": 10.0,
        "size_cm": 55.0,
    },
    "ipsc_silhouette": {
        "type": "ipsc_silhouette",
        "name": "IPSC Metric (simplified)",
        "zones": [
            ("A", 5, 7.5, 15.0),
            ("C", 3, 15.0, 23.0),
            ("D", 1, 22.5, 30.0),
        ],
        "size_cm": 70.0,
    },
    "popper": {
        "type": "popper",
        "name": "IPSC Popper",
        "head_radius_cm": 15.0,
        "body_top_y_cm": -8.0,
        "body_width_cm": 20.0,
        "body_height_cm": 60.0,
        "size_cm": 80.0,
    },
}

# Layout constants (SVG pixels).
_FACE_PX = 360       # the target face occupies a square of this size
_PANEL_PX = 220      # width of the side stats panel
_MARGIN_PX = 20


def _scale(target_def):
    """Pixels per centimetre so the target's `size_cm` fills the face square."""
    return _FACE_PX / target_def["size_cm"]


def _to_px(x_cm, y_cm, target_def):
    """Target-plane cm (y up) -> SVG pixels (y down), centred in the face."""
    scale = _scale(target_def)
    cx = _MARGIN_PX + _FACE_PX / 2.0
    cy = _MARGIN_PX + _FACE_PX / 2.0
    return cx + x_cm * scale, cy - y_cm * scale


def _shot_markers(shots, target_def):
    parts = []
    for shot in shots:
        px, py = _to_px(shot["x_cm"], shot["y_cm"], target_def)
        parts.append(
            f'<circle class="shot" cx="{px:.1f}" cy="{py:.1f}" r="4" '
            f'fill="#c0392b" stroke="#ffffff" stroke-width="0.8"/>'
        )
    return "\n".join(parts)


def _stats_panel(lines):
    x = _MARGIN_PX * 2 + _FACE_PX
    parts = [f'<line x1="{x - 8}" y1="{_MARGIN_PX}" x2="{x - 8}" '
             f'y2="{_MARGIN_PX + _FACE_PX}" stroke="#dddddd"/>']
    y = _MARGIN_PX + 18
    for label, value in lines:
        parts.append(
            f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="12" '
            f'fill="#333333">{html.escape(str(label))}: '
            f'<tspan font-weight="bold">{html.escape(str(value))}</tspan></text>'
        )
        y += 20
    return "\n".join(parts)


def _svg_open():
    width = _MARGIN_PX * 3 + _FACE_PX + _PANEL_PX
    height = _MARGIN_PX * 2 + _FACE_PX
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">'
    )


def _render_bullseye(target_def, shots, score, run_meta):
    cx = _MARGIN_PX + _FACE_PX / 2.0
    cy = _MARGIN_PX + _FACE_PX / 2.0
    scale = _scale(target_def)
    parts = [_svg_open()]
    parts.append(
        f'<rect x="{_MARGIN_PX}" y="{_MARGIN_PX}" width="{_FACE_PX}" '
        f'height="{_FACE_PX}" fill="#f4f1e8" stroke="#999999"/>'
    )
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


def render_svg(target_def, shots, score, run_meta):
    """Render an authentic SVG target with shot markers and a stats panel."""
    target_type = target_def["type"]
    if target_type == "bullseye":
        return _render_bullseye(target_def, shots, score, run_meta)
    raise ValueError(
        f"Invalid target type '{target_type}'. "
        f"Valid types are: bullseye, ipsc_silhouette, popper"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_targets -v`
Expected: PASS (`TestTargetDefs` + `TestBullseyeSvg`).

- [ ] **Step 5: Commit**

```bash
git add targets.py tests/test_targets.py
git commit -m "feat: add target definitions and bullseye SVG rendering

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 9: `targets.py` — popper SVG

**Files:**
- Modify: `targets.py`
- Test: `tests/test_targets.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_targets.py`:

```python
class TestPopperSvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["popper"]
        self.shots = [{"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.3}]
        self.run_meta = {
            "scenario": "Speed", "gun": "MP5-N", "ammo": "FMJ",
            "shooter": "Cassie", "range_m": 10, "shot_count": 1, "time_limit_s": 1.5,
        }

    def test_neutralized_popper_shows_stamp(self):
        score = {
            "target": "popper", "neutralized": True,
            "shots_to_neutralize": 1, "time_to_hit_s": 0.3, "group_size_cm": 0.0,
        }
        svg = targets.render_svg(self.target_def, self.shots, score, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertIn("NEUTRALIZED", svg)
        self.assertEqual(svg.count('class="shot"'), 1)

    def test_standing_popper_has_no_stamp(self):
        score = {
            "target": "popper", "neutralized": False,
            "shots_to_neutralize": None, "time_to_hit_s": None, "group_size_cm": 0.0,
        }
        svg = targets.render_svg(self.target_def, self.shots, score, self.run_meta)
        self.assertNotIn("NEUTRALIZED", svg)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_targets.TestPopperSvg -v`
Expected: FAIL — `ValueError: Invalid target type 'popper'`.

- [ ] **Step 3: Add the popper renderer and register it**

Add to `targets.py`:

```python
def _render_popper(target_def, shots, score, run_meta):
    scale = _scale(target_def)
    head_cx, head_cy = _to_px(0.0, 0.0, target_def)
    head_r = target_def["head_radius_cm"] * scale
    half_w = target_def["body_width_cm"] / 2.0
    body_left_px, body_top_px = _to_px(-half_w, target_def["body_top_y_cm"], target_def)
    body_w_px = target_def["body_width_cm"] * scale
    body_h_px = target_def["body_height_cm"] * scale

    parts = [_svg_open()]
    parts.append(
        f'<rect x="{_MARGIN_PX}" y="{_MARGIN_PX}" width="{_FACE_PX}" '
        f'height="{_FACE_PX}" fill="#fbfbfb" stroke="#cccccc"/>'
    )
    parts.append(
        f'<rect x="{body_left_px:.1f}" y="{body_top_px:.1f}" '
        f'width="{body_w_px:.1f}" height="{body_h_px:.1f}" '
        f'fill="#8a847a" stroke="#333333"/>'
    )
    parts.append(
        f'<circle cx="{head_cx:.1f}" cy="{head_cy:.1f}" r="{head_r:.1f}" '
        f'fill="#b8b3a8" stroke="#333333" stroke-width="1.5"/>'
    )
    parts.append(_shot_markers(shots, target_def))
    if score.get("neutralized"):
        parts.append(
            f'<text x="{head_cx:.1f}" y="{head_cy:.1f}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="22" font-weight="bold" '
            f'fill="#1e8449" transform="rotate(-12 {head_cx:.1f} {head_cy:.1f})">'
            f'NEUTRALIZED</text>'
        )
    stn = score.get("shots_to_neutralize")
    tth = score.get("time_to_hit_s")
    parts.append(_stats_panel([
        ("Scenario", run_meta["scenario"]),
        ("Gun", run_meta["gun"]),
        ("Ammo", run_meta["ammo"]),
        ("Shooter", run_meta["shooter"]),
        ("Range", f'{run_meta["range_m"]} m'),
        ("Result", "Neutralized" if score.get("neutralized") else "Standing"),
        ("Shots to hit", stn if stn is not None else "-"),
        ("Time to hit", f'{tth:.2f} s' if tth is not None else "-"),
    ]))
    parts.append("</svg>")
    return "\n".join(parts)
```

Add a branch in `render_svg` before the `raise`:

```python
    if target_type == "popper":
        return _render_popper(target_def, shots, score, run_meta)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_targets -v`
Expected: PASS (target defs + bullseye + popper).

- [ ] **Step 5: Commit**

```bash
git add targets.py tests/test_targets.py
git commit -m "feat: add popper SVG rendering

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 10: `targets.py` — IPSC silhouette SVG

**Files:**
- Modify: `targets.py`
- Test: `tests/test_targets.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_targets.py`:

```python
class TestIpscSvg(unittest.TestCase):
    def setUp(self):
        self.target_def = targets.TARGET_DEFS["ipsc_silhouette"]
        self.shots = [
            {"x_cm": 0.0, "y_cm": 0.0, "shot_index": 0, "time_s": 0.0},
            {"x_cm": 5.0, "y_cm": -5.0, "shot_index": 1, "time_s": 0.3},
        ]
        self.score = {
            "target": "ipsc_silhouette", "total_points": 10,
            "zone_counts": {"A": 2, "C": 0, "D": 0}, "misses": 0,
            "hit_factor": 5.0, "group_size_cm": 7.1,
        }
        self.run_meta = {
            "scenario": "IPSC", "gun": "Glock 17", "ammo": "FMJ",
            "shooter": "Cassie", "range_m": 10, "shot_count": 2, "time_limit_s": 2,
        }

    def test_renders_zones_and_hit_factor(self):
        svg = targets.render_svg(self.target_def, self.shots, self.score, self.run_meta)
        self.assertTrue(svg.lstrip().startswith("<svg"))
        self.assertEqual(svg.count('class="zone"'), len(self.target_def["zones"]))
        self.assertEqual(svg.count('class="shot"'), len(self.shots))
        self.assertIn("5.00", svg)  # hit factor formatted
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_targets.TestIpscSvg -v`
Expected: FAIL — `ValueError: Invalid target type 'ipsc_silhouette'`.

- [ ] **Step 3: Add the IPSC renderer and register it**

Add to `targets.py`:

```python
def _render_ipsc(target_def, shots, score, run_meta):
    scale = _scale(target_def)
    cx = _MARGIN_PX + _FACE_PX / 2.0
    cy = _MARGIN_PX + _FACE_PX / 2.0
    parts = [_svg_open()]
    parts.append(
        f'<rect x="{_MARGIN_PX}" y="{_MARGIN_PX}" width="{_FACE_PX}" '
        f'height="{_FACE_PX}" fill="#d9c7a8" stroke="#7a6a4a"/>'
    )
    # Zones outer-first so inner zones draw on top.
    for label, _points, hw, hh in reversed(target_def["zones"]):
        parts.append(
            f'<ellipse class="zone" cx="{cx:.1f}" cy="{cy:.1f}" '
            f'rx="{hw * scale:.1f}" ry="{hh * scale:.1f}" '
            f'fill="none" stroke="#5a4a2a" stroke-dasharray="4 3"/>'
        )
    parts.append(_shot_markers(shots, target_def))
    zc = score["zone_counts"]
    parts.append(_stats_panel([
        ("Scenario", run_meta["scenario"]),
        ("Gun", run_meta["gun"]),
        ("Ammo", run_meta["ammo"]),
        ("Shooter", run_meta["shooter"]),
        ("Range", f'{run_meta["range_m"]} m'),
        ("Points", score["total_points"]),
        ("Zones", f'A{zc.get("A", 0)} C{zc.get("C", 0)} D{zc.get("D", 0)}'),
        ("Misses", score["misses"]),
        ("Hit factor", f'{score["hit_factor"]:.2f}'),
    ]))
    parts.append("</svg>")
    return "\n".join(parts)
```

Add a branch in `render_svg` before the `raise`:

```python
    if target_type == "ipsc_silhouette":
        return _render_ipsc(target_def, shots, score, run_meta)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_targets -v`
Expected: PASS (all target renderers).

- [ ] **Step 5: Commit**

```bash
git add targets.py tests/test_targets.py
git commit -m "feat: add IPSC silhouette SVG rendering

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 11: `practice.py` — orchestration, gallery, and curated example output

**Files:**
- Create: `practice.py`
- Modify: `.gitignore`
- Test: `tests/test_practice.py`

`practice.py` ties everything together: load data, resolve each scenario's gun/ammo/shooter, simulate, compute `vertical_walk_cm`, score, render, and write SVG files plus a `TARGETS.md` gallery. Caliber/data mismatches are warned to stderr (matching the existing report's convention) and skipped.

- [ ] **Step 1: Write the failing test**

Create `tests/test_practice.py`:

```python
import os
import tempfile
import unittest

import practice


class TestPractice(unittest.TestCase):
    def test_resolve_records_finds_gun_ammo_shooter(self):
        practice.load_all()
        scenario = {
            "caliber": "9x19mm Parabellum",
            "gun": "Glock 17",
            "ammo": "9x19mm 115 gr Federal FMJ",
            "shooter": "Commando Cassie",
        }
        gun, ammo, shooter = practice.resolve_records(scenario)
        self.assertEqual(gun["name"], "Glock 17")
        self.assertEqual(ammo["name"], "9x19mm 115 gr Federal FMJ")
        self.assertEqual(shooter["strength"], 6)

    def test_resolve_records_raises_on_unknown_gun(self):
        practice.load_all()
        scenario = {
            "caliber": "9x19mm Parabellum",
            "gun": "No Such Gun",
            "ammo": "9x19mm 115 gr Federal FMJ",
            "shooter": "Commando Cassie",
        }
        with self.assertRaises(ValueError) as ctx:
            practice.resolve_records(scenario)
        self.assertIn("No Such Gun", str(ctx.exception))

    def test_run_scenarios_writes_svgs_and_gallery(self):
        practice.load_all()
        with tempfile.TemporaryDirectory() as out_dir:
            count = practice.run_scenarios(practice.SCENARIOS, out_dir)
            self.assertEqual(count, len(practice.SCENARIOS))
            svgs = [f for f in os.listdir(out_dir) if f.endswith(".svg")]
            self.assertEqual(len(svgs), len(practice.SCENARIOS))
            gallery = os.path.join(out_dir, "TARGETS.md")
            self.assertTrue(os.path.exists(gallery))
            with open(gallery, "r") as fp:
                text = fp.read()
            self.assertIn("# Target Practice Gallery", text)
            for svg in svgs:
                self.assertIn(svg, text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_practice -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'practice'`.

- [ ] **Step 3: Create `practice.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_practice -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Generate the committed curated example set**

Run: `python3 practice.py targets`
Expected: prints `Rendered 7 scenario(s) to targets/`, creating `targets/*.svg` and `targets/TARGETS.md`.

- [ ] **Step 6: Add a gitignored scratch directory for ad-hoc runs**

Append to `.gitignore`:

```
# Ad-hoc target render output (the curated set under targets/ is committed)
targets/scratch/
```

- [ ] **Step 7: Run the full test suite**

Run: `python3 -m unittest`
Expected: PASS (all tests across `test_data`, `test_simulation`, `test_scoring`, `test_targets`, `test_practice`, and the pre-existing `test_recoil`).

- [ ] **Step 8: Commit**

```bash
git add practice.py tests/test_practice.py .gitignore targets/
git commit -m "feat: add practice runner with curated target gallery

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Task 12: Documentation — README pointer to the new feature

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a short subsection under the Recoil section of `README.md`**

Insert after the paragraph that references `EXAMPLE.md` (the existing recoil prototype description):

```markdown
### Target Practice Renderer

A companion prototype simulates strings of shots using the recoil model and
renders authentic SVG targets (paper bullseye, IPSC silhouette, and IPSC
popper), so the effects of recoil, shooter skill, weapon, ammunition, and
firing cadence can be compared against real shooting formats (slow, timed, and
rapid fire; popper speed strings).

Run it with:

```bash
python3 practice.py
```

This reads `scenarios.json`, writes one SVG per scenario into `targets/`, and
generates `targets/TARGETS.md` — a gallery of the rendered targets.
```

- [ ] **Step 2: Verify the README renders (visual check) and commit**

```bash
git add README.md
git commit -m "docs: document the target practice renderer

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Notes for the implementer

- **Tuning vs. tests:** the behavioural constants in `simulation.py` are starting values. The tests assert *relative/directional* behaviour (group A < group B, walk increases with cadence, flinch direction), which stays valid as you tune. When you generate the curated set (Task 11, Step 5), eyeball the SVGs: shot zero should sit near the point of aim, a relaxed expert should group tightly, and a rushed novice should show a low, walking, spread group. Adjust constants if the visuals are unrealistic; the relative tests will still hold.
- **`recoil.py` is frozen:** do not modify it. All per-shot recoil variation is obtained via `simulation.round_recoil_data`, which recomputes system mass directly and reuses the (mass-independent) ejecta momentum.
- **Coordinate convention:** simulation and scoring use cm with y-up; only `targets.py` flips y for SVG. Keep that boundary clean.
- **Style:** functions return plain dicts and raise `ValueError` with a list of valid options on bad input, matching `recoil.py`.
```
