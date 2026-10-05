# team-coach/coach-actions Specification

## Purpose

Defines what the team coach may change on the user's teams and how. Changes happen only on an explicit command or a click, every proposed set is legal, and every change can be undone.

## Requirements

### Requirement: Explicit add commands add immediately with Undo
When the user gives an imperative add command naming a Pokémon (for example "add Garchomp"), the coach SHALL put that Pokémon in the team's next empty slot and report it. The reply SHALL offer Undo, which clears that slot again. If the team is full or already has that Pokémon, the coach SHALL say so and change nothing.

#### Scenario: Add to a team with space
- **WHEN** the team has 3 members and the user says "add Garchomp"
- **THEN** Garchomp is saved in slot 4, the page's team refreshes, and the reply shows an Undo action

#### Scenario: Undo
- **WHEN** the user presses Undo on that reply
- **THEN** slot 4 is cleared and the team shows its 3 original members

#### Scenario: Team full
- **WHEN** the team has 6 members and the user says "add Garchomp"
- **THEN** nothing is saved and the reply says the team is full

### Requirement: Deliberation never changes the team
A question about whether or which Pokémon to add (for example "should I add Garchomp?" or "who should I add?") SHALL NOT change the team. The coach MAY show candidate cards, and each card SHALL add (or, when the team is full, replace a chosen member) only when its button is clicked. A card-made change SHALL offer Revert.

#### Scenario: Should I add
- **WHEN** the user asks "Should I add Garchomp?"
- **THEN** the team is unchanged after the reply

#### Scenario: Candidate card
- **WHEN** a recommendation reply shows candidate cards and the user clicks Add on one
- **THEN** that Pokémon is added to the next empty slot and the card shows Revert

### Requirement: Set changes are validated proposals
A request to change a team member's set SHALL produce a proposal for that member (on the user's team or the selected opponent), built only from that Pokémon's legal moves, abilities, natures and held items. Any invented option SHALL be dropped. The proposal SHALL show the current set against the proposed one and SHALL NOT be saved until the user applies it. An applied proposal SHALL offer Revert to the exact previous set.

#### Scenario: Faster set
- **WHEN** the user asks "Give Garchomp a faster set"
- **THEN** a proposal for Garchomp shows was → now for moves, ability, nature, item and EVs, and the stored team is unchanged

#### Scenario: Apply and Revert
- **WHEN** the user applies the proposal and then presses Revert
- **THEN** Garchomp first holds the proposed set, then exactly its previous set

#### Scenario: Opponent member
- **WHEN** an opponent is selected and the user asks "Give their Salamence a bulkier set"
- **THEN** the proposal targets the opponent team's Salamence

#### Scenario: Unknown member
- **WHEN** the user asks to change the set of a Pokémon that is on neither team
- **THEN** no proposal is made and the reply says that Pokémon isn't on the team

### Requirement: Nothing else changes stored data
Apart from explicit adds and the user's own clicks (Add, Replace, Apply, Undo, Revert), coach questions SHALL NOT change any team, and other tools SHALL remain read-only. Question history logging stays as today.

#### Scenario: Recommendation
- **WHEN** the coach answers a draft question
- **THEN** no team is changed until the user clicks a candidate's button
