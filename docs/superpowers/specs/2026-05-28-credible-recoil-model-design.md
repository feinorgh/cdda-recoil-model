# Credible Recoil Model Design

**Goal:** Improve the current recoil prototype so it stays playable for CDDA while becoming more physically grounded and more faithful to real weapon mechanics.

## Summary

The current prototype already points in the right direction by basing recoil generation on conservation of momentum and by considering gun mass, ammo mass, barrel length, and shooter properties. The biggest weakness is that the shooter disturbance model is not dimensionally correct: it uses recoil energy as if it were velocity or momentum. A credible next version should separate recoil generation, weapon-mechanics shaping, and shooter-facing aim disturbance into distinct layers.

## Current model limitations

1. `calculate_throwoff()` uses recoil energy in a way that does not correspond to velocity, momentum, or angular impulse.
2. The model does not include bore-axis leverage, so muzzle rise lacks a mechanical cause.
3. Action type is only approximated through a simple gas factor, so blowback, delayed, gas-operated, and manually operated firearms are not meaningfully separated.
4. Non-rifles collapse into a crude one-handed stance model, which does not represent two-handed pistols, stocked pistols, SMGs, or braced weapons well.
5. The model mixes objective recoil generation with subjective controllability too early, which makes tuning harder.

## Recommended approach

Use a three-layer recoil model.

### Layer 1: Free recoil physics

Compute the physical recoil baseline from conservation of momentum.

For one shot:

- `p_bullet = m_bullet * v_bullet`
- `p_gas = m_gas * v_gas`
- `p_total = p_bullet + p_gas`

Then:

- `M_system = gun_mass + loaded_ammo_mass + attached_mod_mass`
- `v_recoil = p_total / M_system`
- `E_free = p_total^2 / (2 * M_system)`

This layer should remain mostly objective and explainable.

### Layer 2: Weapon-mechanics shaping

Keep the total recoil baseline, but change how the impulse is delivered.

This layer should model:

- action type
- muzzle devices
- stock or brace support
- bore offset
- impulse sharpness or spread

The goal is not to delete momentum arbitrarily. Instead, it is to represent why two weapons with similar free recoil can still feel different in sharpness, rise, and controllability.

### Layer 3: Shooter disturbance and recovery

Translate recoil into gameplay consequences.

This layer should produce at least:

1. rearward kick
2. muzzle rise or angular disturbance
3. recovery time or recovery rate

Aim disturbance should be based on angular leverage and impulse rather than on recoil energy divided by shooter mass.

## Proposed formulas and abstractions

### Baseline recoil

- Bullet momentum: `p_bullet = m_bullet * v_bullet`
- Gas momentum: `p_gas = m_gas * v_gas`
- Total ejecta momentum: `p_total = p_bullet + p_gas`
- Recoiling system mass: `M_system = gun_mass + ammo_mass + mod_mass`
- Rearward gun velocity: `v_recoil = p_total / M_system`
- Free recoil energy: `E_free = p_total^2 / (2 * M_system)`

### Gas and barrel treatment

The current reference-barrel velocity model is acceptable as a starting point, but the next version should:

- retain a reference barrel length per ammunition type
- retain empirical barrel-length velocity adjustment
- make gas velocity an explicit approximation instead of a fixed rifle versus non-rifle switch
- optionally vary barrel sensitivity by cartridge class

A balanced model can still use:

- `v_gas = gas_velocity_factor * v_bullet`

but the factor should depend on cartridge or action family, not only on whether the gun is a rifle.

### Angular disturbance

The shooter-facing effect should be modeled as a simplified rotational problem:

- angular disturbance proportional to `p_total * bore_offset`
- moderated by stance, shouldering, support, strength, skill, and weapon mass

A credible gameplay approximation is:

- `aim_kick ~ (p_total * bore_offset * action_sharpness) / control_factor`

Where `control_factor` can combine:

- stance
- stock or brace support
- one-handed versus two-handed handling
- shooter strength
- weapon skill
- encumbrance or injuries
- weapon mass

### Recovery

Recovery should be separate from initial kick.

This lets the game model differences such as:

- sharp kick but slow recovery
- smooth push with low disturbance
- moderate first-shot kick but poor burst controllability

## Practical data additions

### Ammunition

- bullet mass
- muzzle velocity at reference barrel
- propellant mass or cartridge-class proxy
- reference barrel length

### Firearms

- unloaded mass
- barrel length
- magazine mass and capacity
- action type
- stock or support class
- bore offset class
- optional muzzle-device class

### Mods

- mass delta
- gas redirection or brake effect
- support effect
- recovery effect

### Shooter state

- strength
- weapon skill
- stance
- support state
- encumbrance
- hand or arm injuries

## What should stay heuristic

These factors are worth modeling with categories and tuned coefficients instead of trying to simulate them exactly:

- gas exit velocity
- exact reciprocating mass behavior
- exact impulse time curve
- detailed human biomechanics

This keeps the model grounded without making content authoring too expensive.

## What should be deferred

These are real effects, but they are lower priority for CDDA:

- detailed lock-time behavior
- precise slide or bolt timing per platform
- shoulder pocket compliance
- very fine grip asymmetry differences
- sight-height or optic-mass micro-effects
- heating or fouling as recoil modifiers

## Recommended staged implementation

### Stage 1: Physics cleanup

1. Keep conservation-of-momentum recoil generation.
2. Replace the throwoff model with a momentum- and leverage-based disturbance model.
3. Improve stance and support handling.

### Stage 2: Weapon-mechanics pass

1. Add action categories.
2. Add muzzle-device effects.
3. Add recovery behavior as a separate output.
4. Improve automatic-fire and burst controllability from impulse sharpness and recovery rather than a single recoil scalar.

## Recommendation

For CDDA, the best target is a balanced model:

- physics-based recoil generation
- discrete but meaningful action and support categories
- separate outputs for kick, rise, and recovery
- heuristic tuning only where exact simulation would be too data-heavy

The single highest-value correction is to replace the current energy-based throwoff calculation with an impulse- and leverage-based model.
