# Spec Delta

## Purpose

Plays out one calculator turn (move order, targeting, HP carried over, Focus Sash, KO
calls) the same way on the website and the server, so every client shows the same
battle log.

## ADDED Requirements

### Requirement: The backend plays out a calculator turn
Given the calculator state, the backend SHALL return the turn:
- **Order:** slots with a Pokémon move by move priority, then Speed.
- **Targeting:** in doubles, single-target moves hit the aimed foe (or its partner if
  the aim has fainted); spread moves hit both foes (and the partner for "everyone
  else"); an ally move boosts the partner's damage; singles is always one target.
- **HP:** HP carries over as a worst/best range from each slot's current HP; Focus
  Sash saves its holder once from full HP.
- **Outcome:** each hit is called a KO, a possible KO, or neither; a Pokémon KO'd even
  on low rolls doesn't move.

Types, stats and move data SHALL come from the database. No LLM is involved.

#### Scenario: Faster Pokémon first
- **WHEN** Garchomp (Speed 102 base, 252 EVs) and a slower foe both attack with priority-0 moves
- **THEN** Garchomp's step comes first

#### Scenario: Spread move in doubles
- **WHEN** a doubles attacker uses Earthquake
- **THEN** it hits both foes and its partner, each marked friendly-fire or not

#### Scenario: Focus Sash
- **WHEN** a full-HP Focus Sash holder takes a hit that would KO
- **THEN** the hit is marked as saved by the sash and the holder is left at 1 HP or more

#### Scenario: Unknown move or Pokémon
- **WHEN** a slot names a move or Pokémon not in the data
- **THEN** the response is 422 and names the slot

### Requirement: The turn matches the website
For the same state, the backend's turn SHALL equal the website's: the same order, steps, hits, ranges, KO calls and final HP ranges, checked against reference cases generated from the website's code.

#### Scenario: Reference cases
- **WHEN** the backend plays the generated reference cases
- **THEN** every value equals the website's
