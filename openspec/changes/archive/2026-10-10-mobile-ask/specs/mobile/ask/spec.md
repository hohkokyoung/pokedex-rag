# Spec Delta

## Purpose

Lets the owner ask pokérag questions in the app and get the same grounded answers as
the website: streamed, cited, with the plan visible and code-written result cards.

## ADDED Requirements

### Requirement: Ask tab with starters and status
The app SHALL have an Ask tab with a question box and the website's starter questions, labelled by what they exercise. It SHALL show whether the server answers with an LLM or keyless. Keyless SHALL be stated, not hidden.

#### Scenario: Starters
- **WHEN** the user opens Ask before asking anything
- **THEN** it shows the five starters (Rank, Lore, Multi, Matchup, For you), and tapping one asks it

#### Scenario: Keyless server
- **WHEN** the server has no LLM key
- **THEN** Ask says answers are planned by keywords and quote the records, and questions still work

### Requirement: Streamed, cited answer
Asking SHALL stream the server's run. The plan's steps SHALL appear with their state as they run. The answer text SHALL appear as it arrives. A "How it was answered" line SHALL show the planner (keyword, LLM or cached), the elapsed time and the LLM calls. Each [n] in the answer SHALL open that source's record, with a link to its Pokémon when it has one.

#### Scenario: Ranking question
- **WHEN** the user asks "Which Pokémon has the highest Attack?"
- **THEN** the steps show the ranking lookup, the answer names the top Pokémon with a citation, and a ranking card lists them with their Attack

#### Scenario: Citation
- **WHEN** the user taps [1] in an answer
- **THEN** a sheet shows source 1's snippet and, if it is about a Pokémon, a link to that Pokémon's page

#### Scenario: Couldn't apply
- **WHEN** the plan reports part of the question it couldn't apply
- **THEN** the answer says so up front

#### Scenario: Server unreachable or failing
- **WHEN** the server can't be reached, or the stream reports an error
- **THEN** Ask shows the can't-reach state or the error message, never a blank answer

#### Scenario: Rate-limited or keyless LLM
- **WHEN** the LLM is rate-limited (429) or there is no key
- **THEN** the answer still arrives through the server's fallback (keyword plan, code-written or extractive answer), and the line shows no LLM calls beyond those made

### Requirement: Result cards for every Ask view
The app SHALL render each Ask view the server sends as a card: ranking, pokemon_list, type_chart, move_list, learnset, learners and learn_check. Each card SHALL list its source numbers. A Pokémon in a card SHALL open its page. A view kind the app doesn't know SHALL be skipped, not crash the answer.

#### Scenario: Learn check
- **WHEN** the user asks "Can Pikachu learn Surf?"
- **THEN** a learn-check card says yes or no with how (from the view), and the answer cites it

#### Scenario: Type chart
- **WHEN** the user asks "What is Fire weak to?"
- **THEN** a type-chart card shows Fire's weaknesses, resistances and immunities as type chips

#### Scenario: Unknown view
- **WHEN** the stream includes a view kind the app doesn't render
- **THEN** that view is skipped and the rest of the answer shows

### Requirement: Ask next and profile
After an answer, the app SHALL offer follow-up questions built from the cited Pokémon, as on the website. The user SHALL be able to edit preferred types and see favourites, the inputs to "for you" questions, on the shared server profile.

#### Scenario: Follow-ups
- **WHEN** an answer cites Garchomp
- **THEN** "Tell me about Garchomp" and "What is similar to Garchomp?" are offered, and tapping one asks it

#### Scenario: Preferred types
- **WHEN** the user picks Dragon as a preferred type
- **THEN** the server profile's preferred types include dragon
