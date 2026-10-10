# Spec Delta

## Purpose

The damage calculator's coach in the app: questions about the focused Pokémon,
answered by the server's calc coach, with cards that apply into the calculator only on
a click.

## ADDED Requirements

### Requirement: Coach for the focused Pokémon
The calculator SHALL offer a coach for the focused Pokémon:
- quick questions: "Best build", "Bulky set" and "Fast sweeper", or once a build is proposed the website's follow-ups;
- when the matchup allows, "Can <it> OHKO <its target>?" and "How much bulk does <it> need to survive <target>'s <move>?";
- a question box.

Each question SHALL send the calculator's state (level, mode, field, every filled active slot's set, move and aim, the focus, the turn's hits, and any proposal with its thread). The conversation SHALL show each answer (without [n] markers), the How line, and an error line on failure.

#### Scenario: Damage question without an LLM
- **WHEN** the owner asks "Can Garchomp OHKO Corviknight?"
- **THEN** the request carries both slots and the shown hits, and the answer and a damage card appear with 0 LLM calls

#### Scenario: Keyless build
- **WHEN** the server has no LLM key and the owner taps "Best build"
- **THEN** the answer says builds need a key and no build card appears

### Requirement: Cards apply into the calculator only on a click
A damage what-if and a survive result SHALL offer Apply when they carry changes. Applying SHALL set those fields (item, ability, nature, EVs, HP) on the named calculator slots and mark them Custom; Revert SHALL restore those slots exactly. A build proposal SHALL be shown against the current set, and applying SHALL set its ability, nature, item, EVs and a chosen move (the picked chip, else its first damaging move); Revert SHALL restore the set and move from before the first Apply. A card about a Pokémon the calculator no longer holds SHALL NOT apply. Nothing is saved anywhere else.

#### Scenario: Survive applied and reverted
- **WHEN** a survive card recommends an EV spread and the owner presses Apply EVs, then Revert
- **THEN** the defender's EVs become that spread, then exactly what they were

#### Scenario: Build applied and reverted
- **WHEN** the owner applies a proposed build for Garchomp, then presses Revert
- **THEN** Garchomp's set and move first match the build, then exactly the previous set and move

#### Scenario: Revised proposal
- **WHEN** a follow-up returns a different build after one was applied
- **THEN** the card shows the new build waiting for Apply, and the calculator keeps the applied set until then
