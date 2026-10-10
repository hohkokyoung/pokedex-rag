# Spec Delta

## Purpose

The website's damage calculator in the app, showing the server's turn.

## ADDED Requirements

### Requirement: Calculator setup
The calculator SHALL offer singles or doubles and level 50 or 100. It SHALL have your side and the opponent's (one slot each in singles, two in doubles). Each slot SHALL have:
- a Pokémon (forms included);
- a preset (Offensive picks the spread matching the Pokémon's category; Bulky; Custom when edited);
- nature, EVs (≤ 252 each, ≤ 510 total), IVs, item, ability and current HP;
- a damaging move from its learnset, and in doubles the foe a single-target move aims at.

The field SHALL offer weather, terrain, Reflect, Light Screen, a critical hit, burn and Friend Guard. It SHALL open with Garchomp against Corviknight, as on the website.

#### Scenario: Offensive preset
- **WHEN** the owner picks a special attacker on the Offensive preset
- **THEN** its spread becomes Modest with 252 SpA / 252 Spe / 4 HP

#### Scenario: EV limits
- **WHEN** the owner sets EVs past 510 in total
- **THEN** the last change is capped so the total is 510

### Requirement: This turn
After any change, the app SHALL ask the server for the turn and show the battle log in move order:
- your Pokémon by name, the opponent's as "the opposing …";
- super-effective / not very effective / doesn't affect;
- each hit's range as % of HP, with an HP bar (worst roll solid, best roll faded);
- "It could faint", "fainted!", the Focus Sash save, and a step skipped because its Pokémon fainted.

The app SHALL keep the last turn on screen while the next loads, and SHALL NOT compute damage itself.

#### Scenario: Garchomp vs Corviknight
- **WHEN** the calculator opens with its defaults
- **THEN** the log shows Garchomp's move against the opposing Corviknight with the server's range

#### Scenario: Server unreachable
- **WHEN** the server can't be reached
- **THEN** the calculator shows the can't-reach state with Retry

### Requirement: The formula
The owner SHALL be able to show the formula for the focused Pokémon's hit (attack and defence stats, base damage, modifiers, type effectiveness and STAB) as the server computed it.

#### Scenario: Math
- **WHEN** the owner opens Math
- **THEN** the terms of the focused hit are shown
