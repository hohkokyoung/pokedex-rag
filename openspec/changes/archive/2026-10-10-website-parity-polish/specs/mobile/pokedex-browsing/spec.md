## MODIFIED Requirements

### Requirement: Search, filter and sort
The app SHALL let the user search by name or dex number, filter by any number of types (a Pokémon with any of them is listed) and by generation, and sort by any sort the backend supports (dex number, name, total and each base stat) in either order. Every change SHALL reload the list from the first page.

#### Scenario: Search by name
- **WHEN** the user types "garch"
- **THEN** the list shows Garchomp

#### Scenario: Search by number
- **WHEN** the user types "445"
- **THEN** the list shows Garchomp

#### Scenario: Type and generation filter
- **WHEN** the user filters by Dragon and Generation 4
- **THEN** every listed Pokémon is a Dragon type from Generation 4, and Garchomp is among them

#### Scenario: Several types
- **WHEN** the user picks Fire, Water and Grass
- **THEN** the app asks for all three and the Type pill reads "3 types"

#### Scenario: Sort by Speed, descending
- **WHEN** the user sorts by Speed, highest first
- **THEN** the first row is the fastest Pokémon in the backend's data

#### Scenario: No matches
- **WHEN** a search and filters match nothing
- **THEN** the list says no Pokémon match and offers to clear the filters

### Requirement: Pokémon detail
Opening a Pokémon SHALL show its artwork, name, dex number, genus, types, base stats with the total, abilities (hidden marked), type matchups and evolution chain, all from the backend's detail response. Alternate forms SHALL be switchable from one pill naming the form shown, which opens a sheet of the forms; switching updates the types, stats, abilities, matchups and artwork shown.

#### Scenario: Garchomp
- **WHEN** the user opens Garchomp
- **THEN** it shows Dragon/Ground, base stat total 600, Rough Skin as hidden, and Ice under ×4 in matchups

#### Scenario: Form switch
- **WHEN** the user opens Garchomp's forms and selects Mega Garchomp
- **THEN** the stats, abilities and artwork change to Mega Garchomp's
