# Spec Delta

## ADDED Requirements

### Requirement: Facts and training & breeding
The detail page SHALL show height, weight, habitat, capture rate, base experience and colour. It SHALL also show the gender ratio (or Genderless), egg groups, egg cycles with the approximate steps ((cycles + 1) × 255), growth rate, EV yield and base friendship, all from the detail response.

#### Scenario: Garchomp
- **WHEN** the user opens Garchomp
- **THEN** it shows 1.9 m, 95.0 kg, capture rate 45, ♂ 50% · ♀ 50%, egg groups Monster and Dragon, 40 cycles (~10,455 steps), Slow growth and 3 Attack EV yield

#### Scenario: Genderless
- **WHEN** the user opens a genderless Pokémon (gender rate −1)
- **THEN** the gender ratio reads Genderless

### Requirement: Moveset per game
The detail page SHALL list the moves the Pokémon learns in one game, newest game by default, with a picker for the games it appears in. Moves SHALL be grouped as Level-up (level number, or "Evo" for a move learned on evolving), Egg, TM / HM (with the machine label), Tutor and Other. The list SHALL be filterable by damage category and by type.

#### Scenario: Garchomp in Scarlet / Violet
- **WHEN** the user opens Garchomp's moveset
- **THEN** the game is Scarlet / Violet, Crunch is listed under Level-up as "Evo", and the TM group shows machine labels

#### Scenario: Another game
- **WHEN** the user picks Sword / Shield
- **THEN** the moveset reloads for that game

#### Scenario: Filter
- **WHEN** the user filters by Physical and Dragon
- **THEN** only physical Dragon-type moves are listed

### Requirement: Who else learns a move
Tapping a move SHALL show its type, category, power, accuracy, PP and effect. It SHALL also show the Pokémon that learn it in the selected game, each opening its own detail page.

#### Scenario: Earthquake learners
- **WHEN** the user taps Earthquake in Garchomp's Scarlet / Violet moveset
- **THEN** a sheet shows Earthquake's details and its Scarlet / Violet learners, Torterra among them

### Requirement: Dex entries and where to find
The detail page SHALL show dex entries grouped by generation. It SHALL show where to find the Pokémon per game: location, area, method, level range, rate and conditions. When the Pokémon has no encounter data, it SHALL say so.

#### Scenario: Garchomp's encounters
- **WHEN** the user opens Garchomp's Where to find
- **THEN** it lists The Crown Tundra's Max Raid dens with levels 45–60

#### Scenario: Dex entries
- **WHEN** the user opens Garchomp's dex entries
- **THEN** entries are grouped under their generations, with the games that share each entry

### Requirement: Favourites
The detail page SHALL let the user add or remove the Pokémon from favourites on the server profile, the one the website and Ask use. A Favourites screen SHALL list them, each opening its detail page.

#### Scenario: Add a favourite
- **WHEN** the user taps the heart on Garchomp
- **THEN** Garchomp is added to the server profile's favourites and appears on the Favourites screen

#### Scenario: Remove a favourite
- **WHEN** the user taps the filled heart again
- **THEN** Garchomp is removed from the profile

### Requirement: Previous and next
The detail page SHALL offer previous and next buttons that move by dex number, absent at the ends of the dex.

#### Scenario: Next
- **WHEN** the user taps Next on Garchomp (#445)
- **THEN** Munchlax (#446) opens

#### Scenario: Ends of the dex
- **WHEN** the user opens Bulbasaur (#001)
- **THEN** there is no Previous button
