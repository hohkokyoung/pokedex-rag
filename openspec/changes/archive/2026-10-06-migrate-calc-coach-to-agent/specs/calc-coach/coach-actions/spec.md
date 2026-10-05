# Spec Delta

## Purpose

Defines what the calc coach may change: only the calculator in the browser, only when the user clicks, and always reversibly. Saved teams are never touched.

## ADDED Requirements

### Requirement: Build proposals apply to the calculator only on a click
A build proposal SHALL be built only from the Pokémon's legal moves, abilities, natures and held items, with any invented option dropped. It SHALL be shown against the calculator's current set and change nothing until the user applies it. Applying SHALL change only that calculator slot. Revert SHALL restore the calculator set and chosen move from before the first Apply.

#### Scenario: Apply and Revert
- **WHEN** the user applies a proposed build for Garchomp and then presses Revert
- **THEN** the calculator slot first holds the proposed build, then exactly its previous set and move

#### Scenario: Follow-up revises the proposal
- **WHEN** a proposal exists and the user asks "make it faster"
- **THEN** a revised proposal replaces it in the card, and an already-applied set stays until the user applies again

### Requirement: What-if and threshold results can be applied
A damage what-if or a survival threshold result SHALL offer to apply its changes (the item, nature or EVs it used) to the matching calculator slot, on a click, with Revert. Nothing SHALL be applied without the click.

#### Scenario: Threshold applied
- **WHEN** a survival result recommends 252 HP / 124 Def and the user clicks Apply
- **THEN** the defender's calculator EVs become that spread, and Revert restores the previous EVs

### Requirement: The calc coach never changes stored data
Calc coach questions SHALL NOT create, change or delete any saved team or other stored data, apart from logging the question to history as other assistant surfaces do.

#### Scenario: Any calc question
- **WHEN** any calc coach question completes
- **THEN** no saved team has changed
