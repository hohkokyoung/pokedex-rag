# mobile/pokedex-browsing Specification

## Purpose

Lets the owner browse the Pokédex in a native app on iOS and Android, from the same
ingested data and backend-computed labels the website uses, so both clients always
agree.

## Requirements


### Requirement: Paged Pokédex list
The app SHALL list Pokémon from the backend's list endpoint in pages, loading the next page as the user nears the end. Each row SHALL show the dex number, name, type chips with type names, and an artwork thumbnail from the backend's sprites.

#### Scenario: First page
- **WHEN** the user opens the app with the server reachable
- **THEN** the list shows Bulbasaur (#001) first, with its Grass and Poison chips and artwork

#### Scenario: Infinite scroll
- **WHEN** the user scrolls near the end of the loaded rows
- **THEN** the next page is requested and appended, and no Pokémon appears twice

#### Scenario: End of results
- **WHEN** every result has been loaded
- **THEN** no further page is requested

### Requirement: Search, filter and sort
The app SHALL let the user search by name or dex number, filter by one or two types and by generation, and sort by any sort the backend supports (dex number, name, total and each base stat) in either order. Every change SHALL reload the list from the first page.

#### Scenario: Search by name
- **WHEN** the user types "garch"
- **THEN** the list shows Garchomp

#### Scenario: Search by number
- **WHEN** the user types "445"
- **THEN** the list shows Garchomp

#### Scenario: Type and generation filter
- **WHEN** the user filters by Dragon and Generation 4
- **THEN** every listed Pokémon is a Dragon type from Generation 4, and Garchomp is among them

#### Scenario: Sort by Speed, descending
- **WHEN** the user sorts by Speed, highest first
- **THEN** the first row is the fastest Pokémon in the backend's data

#### Scenario: No matches
- **WHEN** a search and filters match nothing
- **THEN** the list says no Pokémon match and offers to clear the filters

### Requirement: Pokémon detail
Opening a Pokémon SHALL show its artwork, name, dex number, genus, types, base stats with the total, abilities (hidden marked), type matchups and evolution chain, all from the backend's detail response. Alternate forms SHALL be switchable, and switching updates the types, stats, abilities, matchups and artwork shown.

#### Scenario: Garchomp
- **WHEN** the user opens Garchomp
- **THEN** it shows Dragon/Ground, base stat total 600, Rough Skin as hidden, and Ice under ×4 in matchups

#### Scenario: Form switch
- **WHEN** the user opens Garchomp and selects Mega Garchomp
- **THEN** the stats, abilities and artwork change to Mega Garchomp's

### Requirement: Matchups come from the served type chart
The detail's defensive matchup rows SHALL come from the detail response. The "Hits ×2" row SHALL be computed from the backend's type chart, which the app fetches at most once per launch. Until the chart arrives, the row SHALL show a loading placeholder, never guessed values.

#### Scenario: Hits row
- **WHEN** the user opens Garchomp
- **THEN** "Hits ×2" lists Fire, Electric, Poison, Rock, Dragon and Steel

#### Scenario: Chart fetched once
- **WHEN** the user opens several Pokémon in one session
- **THEN** the type chart is requested from the backend once

### Requirement: The evolution chain shows backend labels
The evolution chain SHALL show each stage's chips and description exactly as the backend returns them, with no label derived in the app. For chains that evolve by spinning, it SHALL show the backend's spin guide.

#### Scenario: Eevee
- **WHEN** the user opens Eevee
- **THEN** each branch shows the backend's chips, e.g. "Water Stone" for Vaporeon and "Friendship" + "Day" for Espeon, with the description available on tap

#### Scenario: Alcremie
- **WHEN** the user opens Alcremie
- **THEN** the spin guide shows its 3 steps, the 7 Sweet toppings and the 9 cream rules from the backend

### Requirement: Works without an LLM
Browsing SHALL make no LLM calls. The app SHALL behave identically with no LLM key configured on the backend, and while the LLM provider is rate-limiting.

#### Scenario: Backend without an LLM key
- **WHEN** the backend has no LLM key and the user browses list and detail
- **THEN** everything renders; nothing in phase 1 depends on the LLM

### Requirement: Design follows the product's tokens and motion rules
The app SHALL use the colour, type, radius and spacing tokens generated from DESIGN.md, and the bundled Chakra Petch, Space Grotesk and JetBrains Mono fonts. Type chips SHALL always show the type name. Layouts SHALL hold at 375pt width. When the device asks for reduced motion, the app SHALL replace its animations with instant changes.

#### Scenario: Reduced motion
- **WHEN** the device has reduced motion enabled and the user opens a detail page
- **THEN** stat bars and artwork appear without animation

#### Scenario: Narrow phone
- **WHEN** the app runs on a 375pt-wide screen
- **THEN** list rows and the detail page fit without horizontal scrolling or clipped text

### Requirement: Facts and training & breeding
The detail page SHALL show height, weight, habitat, capture rate, base experience and colour. It SHALL also show the gender ratio (or Genderless), egg groups, egg cycles with the approximate steps ((cycles + 1) × 255), growth rate, EV yield and base friendship, all from the detail response.

#### Scenario: Garchomp
- **WHEN** the user opens Garchomp
- **THEN** it shows 1.9 m, 95.0 kg, capture rate 45, ♂ 50% · ♀ 50%, egg groups Monster and Dragon, 40 cycles (~10,455 steps), Slow growth and 3 Attack EV yield

#### Scenario: Genderless
- **WHEN** the user opens a genderless Pokémon (gender rate −1)
- **THEN** the gender ratio reads Genderless

### Requirement: Moveset per game
The detail page SHALL list the moves the Pokémon learns in one game, newest game by default, with a picker for the games it appears in. Moves SHALL be grouped as Level-up (level number, or "Evo" for a move learned on evolving), Egg, TM / HM (with the machine label), Tutor and Other. The list SHALL be filterable by damage category and by type.

#### Scenario: Garchomp in Scarlet / Violet
- **WHEN** the user opens Garchomp's moveset
- **THEN** the game is Scarlet / Violet, Crunch is listed under Level-up as "Evo", and the TM group shows machine labels

#### Scenario: Another game
- **WHEN** the user picks Sword / Shield
- **THEN** the moveset reloads for that game

#### Scenario: Filter
- **WHEN** the user filters by Physical and Dragon
- **THEN** only physical Dragon-type moves are listed

### Requirement: Who else learns a move
Tapping a move SHALL show its type, category, power, accuracy, PP and effect. It SHALL also show the Pokémon that learn it in the selected game, each opening its own detail page.

#### Scenario: Earthquake learners
- **WHEN** the user taps Earthquake in Garchomp's Scarlet / Violet moveset
- **THEN** a sheet shows Earthquake's details and its Scarlet / Violet learners, Torterra among them

### Requirement: Dex entries and where to find
The detail page SHALL show dex entries grouped by generation. It SHALL show where to find the Pokémon per game: location, area, method, level range, rate and conditions. When the Pokémon has no encounter data, it SHALL say so.

#### Scenario: Garchomp's encounters
- **WHEN** the user opens Garchomp's Where to find
- **THEN** it lists The Crown Tundra's Max Raid dens with levels 45–60

#### Scenario: Dex entries
- **WHEN** the user opens Garchomp's dex entries
- **THEN** entries are grouped under their generations, with the games that share each entry

### Requirement: Favourites
The detail page SHALL let the user add or remove the Pokémon from favourites on the server profile, the one the website and Ask use. A Favourites screen SHALL list them, each opening its detail page.

#### Scenario: Add a favourite
- **WHEN** the user taps the heart on Garchomp
- **THEN** Garchomp is added to the server profile's favourites and appears on the Favourites screen

#### Scenario: Remove a favourite
- **WHEN** the user taps the filled heart again
- **THEN** Garchomp is removed from the profile

### Requirement: Previous and next
The detail page SHALL offer previous and next buttons that move by dex number, absent at the ends of the dex.

#### Scenario: Next
- **WHEN** the user taps Next on Garchomp (#445)
- **THEN** Munchlax (#446) opens

#### Scenario: Ends of the dex
- **WHEN** the user opens Bulbasaur (#001)
- **THEN** there is no Previous button
