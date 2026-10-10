## Purpose
How the catalog (`GET /api/pokemon`) combines several requested types, the same for every client.

## ADDED Requirements

### Requirement: Any requested type matches
The catalog's type filter SHALL list a Pokémon that has any of the requested types, each Pokémon once.

#### Scenario: Three types
- **WHEN** a client asks for Fire, Water and Grass
- **THEN** the result holds every Pokémon with one of them, more than any one type alone and no more than their sum
