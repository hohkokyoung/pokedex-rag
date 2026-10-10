## MODIFIED Requirements

### Requirement: Lookup
Lookup SHALL open on every move, ability and item, with the finder's tabs, filters and sorting, and one search box that finds by name (abilities and items by effect too). With a search, each tab SHALL show its number of matches. A move SHALL open its details and who learns it per game; an ability SHALL show its effect and the Pokémon that have it (filterable by name), each opening its page; an item SHALL show its effect, category, cost and Fling power when it has one. A move nobody learns SHALL say why.

#### Scenario: Search
- **WHEN** the owner types "leftovers"
- **THEN** the Items tab counts 1, and opening Leftovers shows its effect

#### Scenario: Ability holders
- **WHEN** the owner opens Intimidate and filters "gyara"
- **THEN** Gyarados is listed and opens its page
