# A Proposal for a Refined Firearm Simulation Model for CDDA

This is meant to be notes around ideas of physics based alternative models
for recoil, noise, damage, automatic fire handling, and
even handloading for Cataclysm: Dark Days Ahead.

These are my personal notes, and nothing here is set in stone.

Suggestions, criticism, and expert advice is welcome.

## Recoil

For recoil, there is a "proof-of-concept" Python script, with simplified
models of firearms, ammunition, and shooters.

See [recoil.py](recoil.py) for details, and implmentation comments.

There is an [example](EXAMPLE.md) output, showing the output from the
very experimental model.

The physical concept of recoil is based on the idea of conservation
of momentum. https://en.wikipedia.org/wiki/Momentum

In the context of firearms it means that for the energy contained
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
is more difficult to calculate reliably, but which can be estimated:

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

There is an empirical model for adjusting muzzle velocity depending on barrel length and
cartridge power, which I've abstracted into a function with corresponding graph here:
https://docs.google.com/spreadsheets/d/10TeuTTjwusbWB9SaH-nq03bMWDyILylU9Btvtu3uTDM/edit#gid=1882141270

For gun mods:

* Its effect on the mass of the firearm
* Its effect on the recoil reduction of the firearm (in Joules)

## External Ballistics

Simulating the effects of drag, ballistic coefficients, bullet shapes, etc., may be
overkill (pun intended) for CDDA, but some effects might contribute both to realism
and fun (of both kinds) in the game.

### Environmental Effects on Bullet Trajectory

* Wind
* Humidity
* Ricochets
* Fragmentation

### "Barrier Blind" ammunition

Certain types of ammunition (like the M855A1 Enhanced Performance Round) are designed to
be able to penetrate intermediate barriers like car doors, windows, planks, even steel
plates, without severely compromising lethality in a soft target.

### Tracers

Tracers could be fun, and could potentially set fire to things, and be used for attracting
the attention of NPCs from a distance.

### Sabots

Long range sniping is not yet a thing, but for certain calibres (say .50 BMG) sabot rounds
could be used to penetrate even armored vehicles and APCs.

## Terminal Ballistics

A model for taking into account penetration, energy dumped into the target, expansion,
fragmentation, etc. could be made. There's a lot of ballistic data to be found online.

If and when a more detailed model for injuries and damage becomes a thing in CDDA,
terminal ballistics could take into account the effect of hitting bone, major blood vessels,
nerves, and muscles.

Also, terminal ballistics calculation would allow for overpenetration calculations. Certain
rounds could pass through a number of zombies more or less unhindered. And, you could fire
through cars, walls, and even trees in some circumstances.

### Bullet types

These are already modeled by damage modifiers in the current game, but could be expanded upon.

* JHP
* FMJ
* Open Tip
* Solid
* Spitzer

### Frangible ammunition

These types of rounds disintegrate almost completely when they hit something, often leaving
a visible mark. When hitting a body, they could have devastating superficial wounds,
causing severe shock and pain, but could potentially be stopped completely by light
body armor (even a leather coat).

### Armor Piercing

These are already modelled, but could also play into the putative "terminal ballistics"
model above.

### Explosive Rounds

These could also have devastating effects on tissue and/or walls, locks, doors, etc.
A good terminal ballistics model could take into account the damage dumped by the round
itself when penetrating, and the effect of the explosion after penetration.

## Other Effects

### Noise

The amount of energy transformed into noise is proportional to the escaped gases of the
firearm. The more energy in the ejected gases, the larger the report.

This effect is modeled by "gun loudness", but could be calculated as an effect of the
energy released at discharge.

Also, at longer distances, it's still possible to hear the crack of the shockwave of the
bullet passing by, before you hear the sound of the firearm discharge. (Unless of course,
the round is subsonic before it misses you. If it hits you, you probably have more pressing
concerns than thinking about the noise.)

### Ammunition Weight

A fully loaded firearm weighs more than an empty firearm. For some firearms, this effect can be
considerable. The recoil from a fully loaded Glock 19M is markedly less (at least theoretically),
than firing the last round from the same firearm, due to the mass of the firearm including
the cartridges still in the magazine.

### Heat

Firearms heat up when fired, some more than others. The energy imparted onto the receiver from
the gases released may sometimes have a considerable effect on the rate of fire, the wear of
the parts, on accuracy, and on the shooter itself, which may get burned on certain parts (say,
the barrel of a FN MAG after firing 150 rounds into a gaggle of Kevlar Hulks).

Some firearms may become so hot they cook-off a cartridge in the breech without the shooter
pulling the trigger. Certain machine guns may continue to fire this way until they run out
of ammo (or misfire).

This could be simulated by estimating a heatup from a portion of the released energy of the
ammo, and the heat capacity of the barrel/mechanism.

Oh, and a hot barrel would glow bright in infrared, which may attract certain types of
monsters (or repel others?).

### Fouling

There is already a model for fouling in the game.

### Wear & Tear

Some parts of a firearm can only withstand a certain number of shots. Recoil springs, lugs,
firing pins, breech blocks, etc. may be worn out after 10000 to 50000 rounds fired.

Similar to vehicles, a system for breaking down a specific part of a weapon, and to fix it,
might be interesting, and also play into the various ways a firearm may malfunction.

### Environmental Effects

Cold weather conditions may cause firearms to lock up, as can humidity, dirt and debris,
and, one can assume, general filth.

### Interchangeable Parts and Firearm Disassembly

Most firearms can be disassembled into smaller parts. You can fit a H&K G3 fully inside a
messenger bag if you take it apart.

It would be interesting to have to ability to take firearms apart and replace broken
parts in one from another. This would be a system similar to vehicle engines.
