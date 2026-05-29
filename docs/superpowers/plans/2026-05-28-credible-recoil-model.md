# Credible Recoil Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current energy-based throwoff model with a momentum-, leverage-, and recovery-based recoil model that stays simple enough for CDDA tuning.

**Architecture:** Keep `recoil.py` as the executable entry point, but split the math into pure helper functions inside that file so the prototype remains easy to run and easy to test. Add a small stdlib `unittest` test suite that locks in physical identities, support/stance behavior, and action-type sharpness without introducing new dependencies.

**Tech Stack:** Python 3 standard library (`json`, `math`, `re`, `sys`, `unittest`)

---

## File structure

- Modify: `recoil.py` — keep the script standalone, add pure helper functions for free recoil, mechanics defaults, disturbance, and recovery, then update report rendering to show the new outputs.
- Create: `tests/__init__.py` — make the `tests` package importable for `python3 -m unittest` commands.
- Create: `tests/test_recoil.py` — add regression tests for momentum identities, full-vs-empty magazine behavior, action sharpness, support effects, and recovery.
- Modify: `README.md` — document the new model split between free recoil physics and shooter disturbance.
- Modify: `EXAMPLE.md` — regenerate example output after the report format changes.

### Task 1: Creating the free-recoil helper layer

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_recoil.py`
- Modify: `recoil.py:17-56`

- [ ] **Step 1: Create the test package marker**

```python
# tests/__init__.py
```

- [ ] **Step 2: Write the failing tests for the new free-recoil helpers**

```python
import math
import unittest

import recoil


class TestFreeRecoil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()

    def test_free_recoil_uses_momentum_identity(self):
        gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        ammo = recoil.AMMO["9x19mm Parabellum"][0]
        result = recoil.calculate_free_recoil(gun, ammo, "full")
        system_mass = result["system_mass_kg"]
        expected_energy = result["ejecta_momentum"] ** 2 / (2 * system_mass)
        self.assertAlmostEqual(result["free_recoil_energy"], expected_energy, places=6)

    def test_loaded_magazine_reduces_free_recoil_energy(self):
        gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        ammo = recoil.AMMO["9x19mm Parabellum"][0]
        full_mag = recoil.calculate_free_recoil(gun, ammo, "full")
        empty_mag = recoil.calculate_free_recoil(gun, ammo, "empty")
        self.assertLess(full_mag["free_recoil_energy"], empty_mag["free_recoil_energy"])
```

- [ ] **Step 3: Run the single test target to verify it fails**

Run: `python3 -m unittest tests.test_recoil.TestFreeRecoil.test_free_recoil_uses_momentum_identity -v`

Expected: FAIL with `AttributeError: module 'recoil' has no attribute 'calculate_free_recoil'`

- [ ] **Step 4: Write the minimal free-recoil implementation in `recoil.py`**

```python
ACTION_GAS_FACTORS = {
    "bolt": 1.50,
    "revolver": 1.55,
    "locked_breech": 1.50,
    "direct_blowback": 1.60,
    "roller_delayed": 1.55,
    "gas": 1.75,
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

    if configuration == "full":
        ammo_mass = gun_data["mag_mass"] + gun_data["capacity"] * used_ammo["cartridge_mass"]
    else:
        ammo_mass = gun_data["mag_mass"]

    system_mass_kg = (m_gun + ammo_mass) / 1000
    gas_factor = ACTION_GAS_FACTORS[gun_data["action_type"]]
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


def calculate_recoil(gun, used_ammo, configuration):
    result = calculate_free_recoil(gun, used_ammo, configuration)
    return (
        result["free_recoil_energy"],
        result["nominal_velocity"],
        result["actual_velocity"],
    )
```

- [ ] **Step 5: Run the focused test file to verify it passes**

Run: `python3 -m unittest tests.test_recoil.TestFreeRecoil -v`

Expected: PASS with `Ran 2 tests`

- [ ] **Step 6: Commit the free-recoil helper layer**

```bash
git add recoil.py tests/__init__.py tests/test_recoil.py
git commit -m "feat: add free recoil helper layer"
```

### Task 2: Replacing throwoff with angular disturbance and recovery

**Files:**
- Modify: `tests/test_recoil.py`
- Modify: `recoil.py:59-148`

- [ ] **Step 1: Write the failing tests for support, action sharpness, and recovery**

```python
class TestDisturbanceModel(unittest.TestCase):
    def setUp(self):
        self.recoil_data = {
            "ejecta_momentum": 6.0,
            "free_recoil_energy": 10.0,
            "system_mass_kg": 3.5,
        }
        self.shooter = {
            "height": 1800,
            "weight": 80000,
            "strength": 6,
            "skill": 6,
            "injured_hand": False,
        }

    def test_stocked_support_reduces_aim_kick(self):
        pistol = {"type": "pistol", "support_class": "two_hand", "bore_offset": 0.05, "action_type": "locked_breech"}
        stocked = {"type": "rifle", "support_class": "stocked", "bore_offset": 0.05, "action_type": "locked_breech"}
        pistol_result = recoil.calculate_disturbance(self.shooter, pistol, self.recoil_data, "standing")
        stocked_result = recoil.calculate_disturbance(self.shooter, stocked, self.recoil_data, "standing")
        self.assertLess(stocked_result["aim_kick_rad"], pistol_result["aim_kick_rad"])

    def test_blowback_is_sharper_than_gas_for_same_impulse(self):
        blowback = {"type": "submachinegun", "support_class": "stocked", "bore_offset": 0.04, "action_type": "direct_blowback"}
        gas = {"type": "rifle", "support_class": "stocked", "bore_offset": 0.04, "action_type": "gas"}
        blowback_result = recoil.calculate_disturbance(self.shooter, blowback, self.recoil_data, "standing")
        gas_result = recoil.calculate_disturbance(self.shooter, gas, self.recoil_data, "standing")
        self.assertGreater(blowback_result["aim_kick_rad"], gas_result["aim_kick_rad"])

    def test_skill_improves_recovery_without_changing_free_recoil(self):
        novice = dict(self.shooter, skill=1)
        expert = dict(self.shooter, skill=8)
        gun = {"type": "rifle", "support_class": "stocked", "bore_offset": 0.06, "action_type": "gas"}
        novice_result = recoil.calculate_disturbance(novice, gun, self.recoil_data, "standing")
        expert_result = recoil.calculate_disturbance(expert, gun, self.recoil_data, "standing")
        self.assertLess(expert_result["recovery_seconds"], novice_result["recovery_seconds"])
```

- [ ] **Step 2: Run a single disturbance test to verify it fails**

Run: `python3 -m unittest tests.test_recoil.TestDisturbanceModel.test_stocked_support_reduces_aim_kick -v`

Expected: FAIL with `AttributeError: module 'recoil' has no attribute 'calculate_disturbance'`

- [ ] **Step 3: Implement the disturbance and recovery helpers**

```python
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
```

- [ ] **Step 4: Replace the current `calculate_throwoff()` report body**

```python
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
```

- [ ] **Step 5: Update `show_recoil()` to pass full recoil dictionaries**

```python
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
```

- [ ] **Step 6: Run the full test file to verify it passes**

Run: `python3 -m unittest tests.test_recoil -v`

Expected: PASS with `Ran 5 tests`

- [ ] **Step 7: Commit the disturbance model**

```bash
git add recoil.py tests/test_recoil.py
git commit -m "feat: model angular recoil disturbance"
```

### Task 3: Documenting mechanics defaults and report output

**Files:**
- Modify: `README.md:11-124`
- Modify: `EXAMPLE.md`

- [ ] **Step 1: Write the failing documentation check by generating the new report**

Run: `python3 recoil.py > /tmp/recoil-new-example.md && diff -u EXAMPLE.md /tmp/recoil-new-example.md`

Expected: FAIL with a diff showing the new `Recoil Physics` and `Shooter Disturbance` sections not yet documented.

- [ ] **Step 2: Update the README recoil section**

```markdown
## Recoil

For recoil, there is a "proof-of-concept" Python script, with simplified
models of firearms, ammunition, and shooters.

The current prototype now separates:

* Free recoil physics from projectile and propellant momentum
* Weapon-mechanics shaping, such as action type and support class
* Shooter disturbance outputs, reported as aim kick and recovery time

See [recoil.py](recoil.py) for details and implementation comments.

There is an [example](EXAMPLE.md) output showing the generated report for the
experimental model.
```

- [ ] **Step 3: Regenerate `EXAMPLE.md` from the updated script**

Run: `python3 recoil.py > EXAMPLE.md`

Expected: `EXAMPLE.md` now contains `### Recoil Physics` and `### Shooter Disturbance` sections.

- [ ] **Step 4: Re-run the documentation diff to verify it is clean**

Run: `python3 recoil.py > /tmp/recoil-new-example.md && diff -u EXAMPLE.md /tmp/recoil-new-example.md`

Expected: PASS with no output

- [ ] **Step 5: Commit the documentation refresh**

```bash
git add README.md EXAMPLE.md
git commit -m "docs: document the credible recoil model"
```

### Task 4: Verifying end-to-end script behavior

**Files:**
- Modify: `tests/test_recoil.py`
- Modify: `recoil.py`

- [ ] **Step 1: Add an end-to-end report sanity test**

```python
from io import StringIO
from contextlib import redirect_stdout


class TestReportOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        recoil.load_data()

    def test_show_recoil_prints_new_sections(self):
        gun = recoil.WEAPONS["9x19mm Parabellum"][0]
        ammo = recoil.AMMO["9x19mm Parabellum"][0]
        buffer = StringIO()
        with redirect_stdout(buffer):
            recoil.show_recoil(gun, ammo)
        output = buffer.getvalue()
        self.assertIn("### Recoil Physics", output)
        self.assertIn("### Shooter Disturbance", output)
        self.assertIn("Recovery (s)", output)
```

- [ ] **Step 2: Run the single report-output test to verify it fails if the section labels differ**

Run: `python3 -m unittest tests.test_recoil.TestReportOutput.test_show_recoil_prints_new_sections -v`

Expected: PASS if Task 2 is complete; if it fails, the failure should point to mismatched section labels or missing output text.

- [ ] **Step 3: Run the full verification commands**

Run: `python3 -m unittest tests.test_recoil -v`

Expected: PASS with all tests green

Run: `python3 recoil.py > /tmp/recoil-report.md && head -n 40 /tmp/recoil-report.md`

Expected: PASS with a report that includes a table of contents followed by the new recoil physics and shooter disturbance sections.

- [ ] **Step 4: Commit the end-to-end verification coverage**

```bash
git add recoil.py tests/test_recoil.py README.md EXAMPLE.md
git commit -m "test: lock in recoil report outputs"
```
