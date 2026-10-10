# pokedex/move-kinds Specification

## Purpose
Says, on the server, which moves are Z-Moves or Max Moves and which games they belong
to, so every client filters them the same way.

## Requirements

### Requirement: Moves carry their kind
Every move the move search returns SHALL carry a kind:
- `max` when its name starts with "Max " or "G-Max ";
- `z` when it has 1 PP and isn't Struggle, Sketch or Revival Blessing;
- otherwise `regular`.

#### Scenario: Kinds
- **WHEN** a client lists every move
- **THEN** Max Airstream is `max`, Breakneck Blitz is `z`, Sketch is `regular`, and Earthquake is `regular`

### Requirement: Moves nothing learns are placed in their games
The move games list SHALL include, besides the moves some Pokémon learns there, every Z-Move in Sun/Moon and Ultra Sun/Ultra Moon, and every Max Move in Sword/Shield.

#### Scenario: Sword/Shield
- **WHEN** a client reads the Sword/Shield entry
- **THEN** its moves include Max Airstream and no Z-Move
