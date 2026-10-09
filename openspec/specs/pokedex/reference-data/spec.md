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

### Requirement: Evolution stages carry their display labels
Every evolution stage in a Pokémon detail response, for the species chain and each form's chain, SHALL include display labels computed by the backend. The labels are an ordered list of chips, each with a label and a tone (`solid` for the main mechanic, `soft` for qualifiers), plus a description that is present only when the chips alone don't explain the step. Each mechanic's exact number SHALL appear once, in the description, never doubled on a chip.

#### Scenario: Plain level-up
- **WHEN** a client requests Bulbasaur's detail
- **THEN** the Bulbasaur → Ivysaur stage shows one solid chip "Lv. 16" and no description

#### Scenario: Item evolution
- **WHEN** a client requests Eevee's detail
- **THEN** the Eevee → Vaporeon stage shows one solid chip "Water Stone" and no description

#### Scenario: Friendship with a time of day
- **WHEN** a client requests Eevee's detail
- **THEN** the Eevee → Espeon stage shows a solid "Friendship" chip, then a soft "Day" chip, and a description that names the happiness threshold once

#### Scenario: Trade
- **WHEN** a stage evolves by trading
- **THEN** it shows a solid "Trade" chip and a description that mentions the Linking Cord

#### Scenario: Works without an LLM key
- **WHEN** no LLM key is configured, or the provider is rate-limiting
- **THEN** the labels are returned unchanged; they never involve the LLM

### Requirement: Evolution labels match the previous website labels
For every evolution stage in the ingested data, the backend's labels SHALL equal what the website computed before this change: the same chips in the same order with the same tones, and the same description.

#### Scenario: Golden parity over all stages
- **WHEN** the test suite labels every recorded evolution stage
- **THEN** each result equals the recorded output of the previous website code for that stage

### Requirement: Clients show the backend's evolution labels
The website's evolution chain SHALL display the backend's labels and SHALL NOT derive its own from the raw stage fields.

#### Scenario: Evolution chain on the detail page
- **WHEN** the user opens Eevee's detail page
- **THEN** every branch shows the same chips and "?" descriptions as before this change
