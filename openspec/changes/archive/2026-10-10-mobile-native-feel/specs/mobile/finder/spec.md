## MODIFIED Requirements

### Requirement: Advanced search
The finder SHALL be the Lookup page itself: tabs for Moves, Abilities and Items with their counts (matches when searching), one search box shared across tabs, "N of M" shown, and Clear to reset search and filters. Picking a row SHALL open the move, ability or item details. The catalogs SHALL load once per launch, and a failed load SHALL offer retry or the can't-reach state.

#### Scenario: Switch tabs
- **WHEN** the owner types "rain" on Moves and switches to Abilities
- **THEN** the search stays "rain" and abilities whose effect mentions rain (Swift Swim, Drizzle) are listed, but not "terrain" matches
