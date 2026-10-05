# calc-coach/damage-maths Specification

## Purpose
Guarantees that the backend computes the damage calculator's numbers exactly as the calculator does, so the calc coach's answers, what-ifs and survival thresholds always agree with what the user sees.

## Requirements

### Requirement: Backend damage matches the calculator
For the same attacker, defender, move, level and field inputs, the backend damage maths SHALL produce the same single-hit result as the calculator in the browser: minimum and maximum damage as a percentage of the defender's maximum HP, hits to KO from the defender's current HP, type effectiveness, STAB, and the attack and defense stats used. The inputs include stats from base stats, IVs, EVs and nature; item and ability modifiers; weather, terrain, screens, critical hits, burn, doubles spread, Helping Hand and Friend Guard. A shared set of reference cases computed by the calculator's own code SHALL be checked against the backend on every test run.

#### Scenario: Reference cases
- **WHEN** the backend computes every reference case
- **THEN** each min %, max %, hits-to-KO, effectiveness and STAB equals the calculator's value, with percentages equal to within 0.01

#### Scenario: Immunity
- **WHEN** a Ground move targets a Flying-type defender
- **THEN** the result is 0% with effectiveness 0 and no KO

### Requirement: What-if changes
A damage calculation SHALL accept changes to either side's item, ability, nature, EVs or current HP and to the field, and SHALL report the result both with and without the changes.

#### Scenario: Item what-if
- **WHEN** the user asks how much Garchomp's Earthquake does to Salamence with Choice Band instead of its current item
- **THEN** the result shows the current range and the Choice Band range

### Requirement: Survival thresholds
Given a defender, an attacker and a move, the system SHALL find the smallest investment that lets the defender survive the hit at maximum damage from its current HP. Investment means HP and the relevant defense EVs (in steps of 4, within 252 each and 508 total with the defender's other EVs kept), then a beneficial nature if EVs alone aren't enough. When no legal spread survives, it SHALL say so and report the best spread's damage range, naming the other EVs it kept when they are what rules survival out. When the current set already survives, it SHALL say so and propose no change.

#### Scenario: Survivable
- **WHEN** a bulky defender can survive Close Combat with some HP and Defense investment
- **THEN** the result names the HP and Defense EVs (and nature, if needed) and the damage range at that spread

#### Scenario: Not survivable
- **WHEN** no legal spread survives the hit
- **THEN** the result says it can't be survived and shows the best spread's damage range

#### Scenario: Already survives
- **WHEN** the defender's current set already survives the hit
- **THEN** the result says so with the current damage range and offers nothing to apply
