# Spec Delta

## Purpose

Ranks Poké Balls by catch chance for a wild Pokémon and a situation, on the server, so
the website and the app give the same odds from the same rules.

## ADDED Requirements

### Requirement: The backend ranks balls by catch chance
For a Pokémon and a situation, the backend SHALL return every ball with:
- its chance to catch per throw;
- the throws needed for a 90% chance;
- why it scores as it does;
- the formula terms: max and current HP, effective catch rate, HP factor, ball, status
  and low-level multipliers, the modified rate, shake and critical-capture chances.

The situation covers wild level, your level, HP %, status, turn, night or cave, on
water, caught before, love match, species caught and the Catching Charm. Balls SHALL
be ordered by chance, best first, ties keeping the ball table's order. The Master Ball
and any rate of 255 or more SHALL be a sure catch. No LLM is involved.

#### Scenario: Quick Ball on turn 1
- **WHEN** the client asks about a Pokémon with catch rate 45 at full HP on turn 1
- **THEN** the Quick Ball's multiplier is ×5 and it ranks above the Ultra Ball

#### Scenario: Status and HP
- **WHEN** the same Pokémon is asleep at 1% HP
- **THEN** every ball's chance is higher than at full HP with no status

#### Scenario: Unknown Pokémon or bad input
- **WHEN** the Pokémon doesn't exist, or a level or HP is out of range
- **THEN** the response is 404 or 422 respectively

### Requirement: Catch odds match the previous client formula
For the same Pokémon and situation, every ball's chance, throws and formula terms SHALL equal what the website's client-side formula produced, checked against golden cases recorded from it.

#### Scenario: Golden cases
- **WHEN** the backend computes the recorded cases
- **THEN** every value equals the recorded one

### Requirement: Clients show the backend's catch odds
The website and the app SHALL show the backend's ranking and terms and SHALL NOT compute catch chances themselves.

#### Scenario: Website tile
- **WHEN** the owner changes the wild level on the website's catch-rate tile
- **THEN** the tile shows the backend's updated ranking
