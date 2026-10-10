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
- Chakra Petch only for page titles and Pokémon names, and JetBrains Mono for numbers;
- a phone type scale one step smaller than the website's (body 14), with text fields on the same scale.

Red SHALL mark only actions and the current selection.

#### Scenario: Narrow phone
- **WHEN** any screen is shown at 375pt wide
- **THEN** nothing clips or scrolls sideways

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

### Requirement: Tab bar
The bottom bar SHALL be one white capsule with four equal tabs: Pokédex, Teams, Tools and Ask. The current tab SHALL sit on a soft capsule that slides between tabs, and Ask SHALL be the red tab. A whole tab cell SHALL be its tap target, a pressed tab SHALL dim, and switching SHALL give a selection haptic. Each tab SHALL keep its place when switching.

#### Scenario: Switch tabs
- **WHEN** the owner taps near the edge of Teams, then Tools, Ask and Pokédex
- **THEN** each opens, and the Pokédex is where they left it

### Requirement: iOS behaviour
Pages SHALL slide in the iOS way and can be swiped back, each on its own background, so the page underneath never shows through. Taps SHALL NOT draw ink ripples. Choices SHALL open a sheet of rows with a red check rather than a dropdown menu or checkboxes. Loading SHALL use the iOS activity indicator, and confirmations SHALL use iOS alerts.

#### Scenario: Open a tool
- **WHEN** the owner opens a tool from the Tools tab
- **THEN** it slides in over an opaque background instead of cutting in

### Requirement: Filters on a phone
Filters SHALL be a row of pills, each opening a sheet for that one filter; a pill SHALL turn ink and name its choice when set. Types SHALL be picked as on the website: type names in grey that wrap across the width, a picked type filled with its colour and a soft glow of it. No filter row SHALL run off the screen.

#### Scenario: Pick a type
- **WHEN** the owner opens Type on the Pokédex and picks Fire
- **THEN** Fire fills orange, the pill reads "Fire", and the list reloads with Fire-types
