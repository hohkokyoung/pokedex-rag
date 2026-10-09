# pokedex/reference-data Specification

## Purpose

Serves the static game-reference data that clients display (the type-effectiveness
chart and the Alcremie spin rules) from the backend, so no client hard-codes its own
copy and every client agrees with the ingested data the assistant answers from.

## Requirements


### Requirement: The backend serves the type-effectiveness chart
The backend SHALL provide a read-only endpoint returning the 18 battle types in display order (normal, fire, water, electric, grass, ice, fighting, poison, ground, flying, psychic, bug, rock, ghost, dragon, dark, steel, fairy). For every attacking type it SHALL give the damage multiplier against each defending type, taken from the ingested effectiveness data. Non-battle types SHALL be excluded.

#### Scenario: Chart contents
- **WHEN** a client requests the type chart
- **THEN** the response lists the 18 types in display order and, for every attacking/defending pair, a multiplier of 0, 0.5, 1 or 2 matching the ingested data

#### Scenario: Known matchups
- **WHEN** a client requests the type chart
- **THEN** ground→flying is 0, water→fire is 2, fire→water is 0.5 and normal→normal is 1

#### Scenario: No non-battle types
- **WHEN** the ingested data contains a type outside the 18 battle types
- **THEN** that type appears in neither the order nor the chart

#### Scenario: Works without an LLM key
- **WHEN** no LLM key is configured, or the provider is rate-limiting
- **THEN** the type chart is returned unchanged; it never involves the LLM

### Requirement: The served chart matches the previous client chart
The served chart SHALL equal the chart the website hard-coded before this change for all 324 attacking/defending pairs. Any difference SHALL fail the test suite, not silently change the website's matchups.

#### Scenario: Parity with the previous chart
- **WHEN** the test suite compares the served chart with the recorded previous client chart
- **THEN** all 324 multipliers are equal

### Requirement: Clients read type matchups from the served chart
The home Type Calculator and the Pokémon detail page's "hits super-effectively" list SHALL compute from the served chart. The website SHALL fetch the chart at most once per page load. While the chart is loading, these views SHALL show a loading state rather than wrong multipliers.

#### Scenario: Type Calculator
- **WHEN** the user picks Dragon/Flying in the home Type Calculator
- **THEN** it shows Ice as a 4× weakness and Ground as an immunity, from the served chart

#### Scenario: Fetched once
- **WHEN** the user moves between the home page and several detail pages in one session
- **THEN** the type chart is requested from the backend at most once

### Requirement: Spin evolutions come with their spin guide
When a Pokémon's evolution data includes a stage triggered by spinning, the detail response SHALL include a spin guide. The guide holds the ordered spin steps, the topping each Sweet gives, and for each cream its spin direction, spin duration and time of day, in a fixed cream order. Evolution data without a spin stage SHALL have no spin guide.

#### Scenario: Milcery's detail page
- **WHEN** a client requests Milcery's (or Alcremie's) detail
- **THEN** the response contains a spin guide with 3 steps, 7 Sweet→topping entries and 9 cream rules, Vanilla Cream first and Rainbow Swirl last

#### Scenario: Other evolutions
- **WHEN** a client requests the detail of a Pokémon whose evolutions don't involve spinning, such as Bulbasaur
- **THEN** the response has no spin guide

#### Scenario: Evolution chain shows the guide
- **WHEN** the user opens Alcremie's detail page and expands its variants
- **THEN** the "How it works" steps, the topping per Sweet and the spin rule per cream show the same text as before this change
