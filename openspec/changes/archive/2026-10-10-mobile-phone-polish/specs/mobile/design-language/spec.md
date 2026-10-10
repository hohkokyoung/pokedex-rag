## MODIFIED Requirements

### Requirement: The website's language on every screen
Every screen SHALL use:
- the website's tinted gradient ground and white panels with 1px hairlines (no shadows, no panels nested in panels);
- 10px corners on controls and 14px on panels;
- type chips with 6px corners that always show the type name, spaced from neighbouring text;
- Chakra Petch only for page titles and Pokémon names, and JetBrains Mono for numbers;
- a phone type scale one step smaller than the website's (body 14), with text fields on the same scale.

Red SHALL mark only actions and the current selection.

#### Scenario: Narrow phone
- **WHEN** any screen is shown at 375pt wide
- **THEN** nothing clips or scrolls sideways

## ADDED Requirements

### Requirement: Filters on a phone
Filters SHALL be a row of pills, each opening a sheet for that one filter; a pill SHALL turn ink and name its choice when set. Types SHALL be picked as solid type chips in a three-column grid: picked ones carry a check, and while any is picked the others fade. No filter row SHALL run off the screen.

#### Scenario: Pick a type
- **WHEN** the owner opens Type on the Pokédex and picks Fire
- **THEN** Fire shows a check, the other types fade, the pill reads "Fire", and the list reloads with Fire-types
