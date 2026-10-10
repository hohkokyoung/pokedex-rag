# mobile/finder Specification

## Purpose
The website's advanced search in the app: every move, ability and item, with filters
and sorting, opening the same details as the lookup.

## Requirements

### Requirement: Advanced search
The lookup SHALL offer Advanced search: tabs for Moves, Abilities and Items with their counts, one search box shared across tabs, "N of M" shown, and Clear to reset search and filters. Picking a row SHALL open the same move, ability or item details as the lookup. The catalogs SHALL load once per launch, and a failed load SHALL offer retry or the can't-reach state.

#### Scenario: Switch tabs
- **WHEN** the owner types "rain" on Moves and switches to Abilities
- **THEN** the search stays "rain" and abilities whose effect mentions rain (Swift Swim, Drizzle) are listed, but not "terrain" matches

### Requirement: Move filters and sort
Moves SHALL filter by types (any of the picked), category (any picked; a folded Z-Move matches either of its categories), kind (regular, Z-Move, Max Move, from the server) and game (the server's list), and sort by power, PP, accuracy or name; moves without the sorted value sink to the end, ties by name. Same-named moves SHALL show as one row.

#### Scenario: Fire special by power
- **WHEN** the owner picks Fire, Special, and sorts by power
- **THEN** the first row is the strongest special Fire move, and status moves aren't listed

#### Scenario: Max Moves in Sword/Shield
- **WHEN** the owner picks kind Max Move and game Sword/Shield
- **THEN** Max Moves are listed

### Requirement: Item filters and sort
Items SHALL filter by category (most-populated first) and sort by name, cost or Fling power.

#### Scenario: Fling
- **WHEN** the owner sorts items by Fling power
- **THEN** the first row has the highest Fling power and items without one come last
