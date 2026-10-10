# mobile/design-language Specification

## Purpose

The app's shared look and screen structure: the website's light Instrument language,
cleaner, on every screen.

## Requirements

### Requirement: The website's language on every screen
Every screen SHALL use:
- the website's tinted gradient ground and white panels with 1px hairlines (no shadows, no panels nested in panels);
- 10px corners on controls and 14px on panels;
- type chips with 6px corners that always show the type name, spaced from neighbouring text;
- Chakra Petch only for page titles and Pokémon names, and JetBrains Mono for numbers.

Red SHALL mark only actions and the current selection.

#### Scenario: Narrow phone
- **WHEN** any screen is shown at 375pt wide
- **THEN** nothing clips or scrolls sideways

### Requirement: Tray navigation with a separate Ask
The bottom bar SHALL be a tray holding Pokédex, Teams and Tools, with the current one raised, plus a separate red Ask button. Each tab SHALL keep its place when switching.

#### Scenario: Switch tabs
- **WHEN** the owner taps Teams, then Pokédex
- **THEN** Teams shows raised while open, and the Pokédex is where they left it

### Requirement: Pokédex cards
The Pokédex SHALL show two columns of cards with the dex number, the sorted number (labelled), artwork, name, genus and type chips. Tapping a card SHALL open its detail, with the artwork carried over.

#### Scenario: Sorted by Speed
- **WHEN** the list is sorted by Speed
- **THEN** each card's corner number is its Speed, labelled Speed

### Requirement: Detail and team in segments
A Pokémon's page SHALL open on a hero (artwork on its type glow, the ghosted dex number, name, genus, types, favourite), then segments: Overview (stats, abilities, matchups, facts), Moves, Evolution (the chain and the spin guide), and Where (dex entries and encounters). A team's page SHALL open on its grade, name, score and six slots, then segments: Report, Coach and Compare. Segments SHALL switch without leaving the page.

#### Scenario: Garchomp's moves
- **WHEN** the owner opens Garchomp and taps Moves
- **THEN** the moveset shows under the same hero, and Overview is one tap away

#### Scenario: Team coach
- **WHEN** the owner opens a team and taps Coach
- **THEN** the coach shows under the same slots
