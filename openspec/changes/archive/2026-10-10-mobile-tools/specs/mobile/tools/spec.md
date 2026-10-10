# Spec Delta

## Purpose

Brings the website's reference tools to the app: type calculator, nature helper,
catch rate and the move / ability / item lookup, all reading server data.

## ADDED Requirements

### Requirement: Tools tab
The app SHALL have a Tools tab, after Ask, listing the type calculator, nature helper, catch rate and lookup. Each tool SHALL show the can't-reach state when the server can't be reached.

#### Scenario: Open a tool
- **WHEN** the owner taps Tools, then Catch rate
- **THEN** the catch-rate tool opens, and back returns to the list with the tab kept

### Requirement: Type calculator
The owner SHALL pick one or two types (a third pick replaces the older one). The calculator SHALL show what the typing takes ×4 and ×2, resists ×½ and ×¼, is immune to, and which types the picked types hit ×2, read from the served type chart.

#### Scenario: Dual typing
- **WHEN** the owner picks Fire and Flying
- **THEN** Rock shows under ×4 and Ground under immune

### Requirement: Nature helper
The helper SHALL show the 5×5 grid of natures from the server (+stat rows, −stat columns, neutral natures on the diagonal). Tapping one SHALL show its ±10% effect, or that it is neutral.

#### Scenario: Adamant
- **WHEN** the owner taps Adamant
- **THEN** it reads +Atk / −SpA (±10%)

### Requirement: Catch rate
The owner SHALL pick a Pokémon and set the situation (wild level, your level, HP %, status, turn, night or cave, on water, caught before, love match, species caught, Catching Charm). The tool SHALL list the server's ranked balls with each chance per throw, throws for 90% and why, and SHALL show the formula terms for the top ball. It SHALL NOT compute chances itself.

#### Scenario: Change the situation
- **WHEN** the owner sets the status to Sleep
- **THEN** the app requests the ranking with status sleep and shows the new order

### Requirement: Lookup
One search box SHALL find moves, abilities and items by name. A move SHALL open its details and who learns it per game; an ability SHALL show its effect and the Pokémon that have it (filterable by name), each opening its page; an item SHALL show its effect, category, cost and Fling power when it has one. A move nobody learns SHALL say why.

#### Scenario: Search
- **WHEN** the owner types "leftovers"
- **THEN** the Leftovers item is listed, and opening it shows its effect

#### Scenario: Ability holders
- **WHEN** the owner opens Intimidate and filters "gyara"
- **THEN** Gyarados is listed and opens its page
