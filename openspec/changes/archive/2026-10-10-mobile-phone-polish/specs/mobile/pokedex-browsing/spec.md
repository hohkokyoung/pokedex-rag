## MODIFIED Requirements

### Requirement: Dex entries and where to find
The detail page SHALL show dex entries one generation at a time, picked from a segmented control that starts on the newest; each entry SHALL list the games that share it. It SHALL show where to find the Pokémon per game: location, area, method, level range, rate and conditions. When the Pokémon has no encounter data, it SHALL say so.

#### Scenario: Garchomp's encounters
- **WHEN** the user opens Garchomp's Where to find
- **THEN** it lists The Crown Tundra's Max Raid dens with levels 45–60

#### Scenario: Dex entries
- **WHEN** the user opens Garchomp's dex entries and picks IV
- **THEN** the Generation IV entries show, each with the games that share it
