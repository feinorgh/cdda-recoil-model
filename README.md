# A Proposal for an Alternative Firearm Model for CDDA

This is meant to be an idea of physics based alternative model
for recoil, noise, damage, automatic fire handling, and
even handloading for Cataclysm: Dark Days Ahead.

## Recoil

The physical concept of recoil is based on the idea of conservation
of momentum. https://en.wikipedia.org/wiki/Momentum

In the concept of a firearm it means that for the energy contained
in the projectile fired, there is an equal but opposite force imparted
on the firearm, and, in turn, the shooter.

The recoil from a firearm is affected by many factors, but what's
referred to as "free recoil" can be calculated from a few known facts:

* The mass of the projectile fired
* The velocity of the projectile
* The mass of the ejected propellant gases
* The velocity of the gases when exiting the barrel
* The mass of the firearm

There's also a set of factors which may affect _felt_ recoil, which
is more difficult to calculae reliably, but which can be estimated:

* Muzzle brake effect
* Method of operation (action) of the firearm (blowback, various gas operations)
* Type of system for storing and releasing recoil energy (spring, hydraulic)
* Cyclic rate of the weapon (over what time does the recoil force act)
* Padding and grips
* Clothing of the shooter

And, finally, how the shooter _manages_ the recoil from the weapon can be
affected by:

* Body mass and strength
* Skill and experience
* Shooting stance (standing, sitting, prone)
* Anchoring. A rifle has three points of balance, a handgun has one. Certain
  firearms have two (grip and handle, no buttstock). A bipod gives an extra
  anchoring point.
* Physiological and mental state of the shooter (tired, dazed, drugs effects, pain, etc.)
* Reaction time of the nervous system (around 0.15 s for tactile response, around 0.25 s
  for vision)
* The environment (cold fingers, icy equipment, humidity)

These effects can be considered to impart a _push_ on the shooter, which can translate to
an angular momentum around the center of mass of the shooter.

### Simulating Recoil in *Cataclysm: Dark Days Ahead*

The data for firearms in the game currently contain _some_ of the necessary variables to
be able to calculate free recoil of a discharged weapon:

* The mass of the firearm
* The damage factor of the ammunition fired (roughly square root of the energy of the projectile)
* Gun modification effects (such as muzzle breaks, recoil dampeners, grips)
* The stance of the shooter/player (running/walking/crouching)

However, a lot of these values may be arbitrary. Some firearms affect the damage of the ammunition
they fire, presumably because of a shorter barrel? Some firearms have higher dispersion
than others, but this may also seem a bit arbitrary. The main downside to this is that
every weapon has its unique set of data, which has to be maintained in the JSON files.

The current recoil model in the game imparts a penalty on the aim of the shooter, in
quarter degrees (if I have understood it correctly).

A more _algorithmic_ approach to imparting this aim penalty within the same numeric domain
(mostly) could be done with a more physically realistic model, outlined in the
Python script in this directory.

This is a rough model still, but may have some advantages:

* The JSON data could lose the arbitrary values for damage reduction and dispersion penalties
* The free recoil could be calculated consistently through a few known and verifiable
  variables
* The algorithm itself could be tweaked and refined successively where more detail (if desirable)
  is required.

The downside is that a number of variables have to be put into the JSON files for guns & ammo (and,
presumably, the gunmods too).

For ammunition:

* Bullet mass
* Cartridge mass
* Propellant mass
* Reference muzzle velocity in a specific barrel length

These can all be looked up online for various types of ammunition. The propellant masses can be
generalized, as detailed information is not always available, but in general, for various
calibers, there's a "typical" load (which could also tie into the handloading mechanism of
the game).

For firearms:

* Barrel length (to automatically calculate velocity gain/loss in relation to reference muzzle
  velocity from the ammunition)
* Magazine mass (this, to a large extent is already present in the JSON data)
* Type of mechanism (see https://en.wikipedia.org/wiki/Action_(firearms))

For gun mods:

* Its effect on the mass of the firearm
* Its effect on the recoil reduction of the firearm (in Joules)
