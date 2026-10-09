# Spec Delta

## ADDED Requirements

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
