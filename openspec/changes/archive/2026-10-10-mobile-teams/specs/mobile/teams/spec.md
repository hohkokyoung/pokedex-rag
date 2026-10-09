# Spec Delta

## Purpose

Lets the owner build, grade and compare saved teams in the app, showing exactly the
grades, profile, strategy and matchup the backend computes for the website.

## ADDED Requirements

### Requirement: Teams tab and team list
The app SHALL have a bottom navigation bar with Pokédex and Teams. The Teams tab SHALL list every saved team. A non-empty team's card SHALL show its name, sprites, grade and score from the backend rating, play style, AI summary, weak to / resists / hits-hard facts, six letter grades and up to three fixes. An empty team SHALL show its name and an invitation to add Pokémon.

#### Scenario: Saved teams
- **WHEN** the user opens Teams
- **THEN** "Garchomp team" shows grade A and 88/100, matching the website

#### Scenario: Empty team
- **WHEN** a team has no members
- **THEN** its card says it's empty and opening it shows six empty slots

### Requirement: Create, rename and delete teams
The user SHALL be able to create a named team, rename a team, and delete a team after confirming. A deleted team SHALL disappear from the list.

#### Scenario: Create
- **WHEN** the user taps New team and enters "Rain"
- **THEN** a team named Rain is created on the server and its page opens

#### Scenario: Delete
- **WHEN** the user deletes a team and confirms
- **THEN** the server deletes it and it leaves the list; cancelling deletes nothing

### Requirement: Slots and the Pokémon picker
The team page SHALL show six slots, each filled slot with sprite, name, types, role and BST. Tapping an empty slot SHALL open a picker that searches Pokémon by name or dex number, forms included. Choosing one SHALL fill that slot on the server.

#### Scenario: Add to an empty slot
- **WHEN** the user taps an empty slot and picks Garchomp
- **THEN** the slot shows Garchomp and the rating updates

### Requirement: Set editor with legal choices only
Editing a filled slot SHALL offer only legal choices for that species or form:
- its abilities, with hidden marked;
- held items, searchable;
- natures, with their + and − stats;
- EVs, each 0–252 and at most 510 in total;
- IVs, each 0–31;
- up to four moves from its learnset.

Save SHALL write the slot. Remove SHALL clear it. A choice the server rejects SHALL be reported, not silently lost.

#### Scenario: Change Garchomp's set
- **WHEN** the user gives Garchomp Jolly, Choice Scarf, 252 Atk / 252 Spe, and Earthquake, Outrage, Stone Edge, Fire Fang, then saves
- **THEN** the server holds that set and the slot and report reflect it

#### Scenario: EV limits
- **WHEN** the user tries to raise EVs beyond 510 in total
- **THEN** the editor stops at 510

#### Scenario: Four moves at most
- **WHEN** four moves are chosen
- **THEN** no fifth can be added until one is removed

### Requirement: The report shows the backend's analysis
The team page SHALL show:
- the rating (grade, score, style, lean, biggest gap) and the AI summary, with ↻ Regenerate;
- the six grades with headline and fix;
- the strategy axes, now and with learnable moves;
- the type profile;
- the sets per member, with Use suggested;
- defence per attacking type.

Grades, profile and axes SHALL come from the backend, unchanged.

#### Scenario: Same numbers as the website
- **WHEN** the user opens Garchomp team
- **THEN** it shows 88/100 · A, Defence B (74), Sets C (61), and the website's fix lines

#### Scenario: Use suggested
- **WHEN** the user taps Use suggested on a member with empty parts
- **THEN** the engine's suggestion is applied to the empty parts only, via the server

#### Scenario: Without an LLM key
- **WHEN** the backend has no LLM key
- **THEN** the report shows the rules-written summary, and everything else is unaffected

### Requirement: Compare with another team
The team page SHALL let the user pick another saved team as the opponent. With an opponent, it SHALL show the matchup verdict, the scorecard (ours vs theirs per factor), their threats, our pressure and the engine's advice. The team's own grade SHALL stay as it is without an opponent.

#### Scenario: Garchomp team vs Rival
- **WHEN** the user compares Garchomp team with Rival (mockup)
- **THEN** it shows the verdict "Even", the one-on-ones 17–18, and Tyranitar among their threats, and Garchomp team's grade is still A (88)
