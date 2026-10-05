# assistant/result-views Specification

## Purpose

Defines the streamed contract between the assistant and the UI: plan progress, which planner decided, typed result views tied to citations, and usage. It also defines how the Ask page and the home Ask tile present them.

## Requirements

### Requirement: Plan progress is streamed for every question
The Ask stream SHALL send a `plan` event before any step runs. The event lists each step (id, tool, one-line reason) and the `planner` that produced it (`llm` or `keyword`), and whether the plan came from cache. It SHALL send a `step` event whenever a step changes state (`running`, `done`, `empty`, `error`), carrying a one-line summary. A re-plan SHALL send another `plan` event containing only the added steps.

#### Scenario: Normal ordering
- **WHEN** a two-step plan runs to completion
- **THEN** the client receives `plan`, then `step` events for both steps ending in a terminal state, then `sources`, then answer `delta` events, then `done`

#### Scenario: Keyword-planned question
- **WHEN** a question is planned by the keyword planner
- **THEN** its `plan` event has `planner: "keyword"` and the same step and view events follow as for an LLM plan

#### Scenario: Error step
- **WHEN** a step fails
- **THEN** its `step` event has state `error` and a short human-readable summary, and the stream continues

### Requirement: The stream reports the planner, not a route
The Ask stream SHALL NOT send a `route` event. The `sources`, `delta` and `error` events SHALL keep their current shapes. The `done` event SHALL carry usage: the number of LLM calls and the tokens used.

#### Scenario: Done carries usage
- **WHEN** an answer finishes after a plan call and an answer call
- **THEN** the `done` event reports 2 LLM calls with input and output token counts

### Requirement: Results are streamed as typed views
A step whose result has a visual form SHALL send a `view` event. The event carries the step id, a view kind, structured data for that kind, and the step-local evidence indices its data came from. Supported kinds are `ranking`, `pokemon_list`, `type_chart`, `move_list`, `learnset`, `learners`, `learn_check`, and, for the team coach, `candidates`, `set_edit`, `member_added` and `duel`. View data SHALL come from the tool result, not from the LLM answer. Each entry in the `sources` event SHALL identify the step and step-local index it came from, so views can be linked to global source numbers.

#### Scenario: Ranking view
- **WHEN** a Pokémon query sorted by Speed returns 5 rows
- **THEN** a `ranking` view is sent with the stat axis (`speed`), the 5 rows (name, dex number, types, value) in order, the total match count, and their evidence indices

#### Scenario: Step without a visual
- **WHEN** a semantic search step returns description passages only
- **THEN** no `view` event is sent for it, and its passages appear only in sources

#### Scenario: Set-edit view
- **WHEN** a coach set-edit step proposes a new set for Garchomp
- **THEN** a `set_edit` view is sent with the team side, slot, the current set and the proposed set (moves, ability, nature, item, EVs) and the fields that change

### Requirement: Non-streaming Ask returns the plan and views
The non-streaming Ask response SHALL contain the answer, the `planner`, the executed steps with their final states, the views, the sources, and usage. It SHALL NOT contain a `route`.

#### Scenario: Non-streaming answer
- **WHEN** a client POSTs a question to the non-streaming Ask endpoint
- **THEN** the response contains the planner, the steps with terminal states, the views, the sources and usage, and no `route` field

### Requirement: Ask shows live plan steps
While a question runs, the Ask page SHALL show each step with its reason and current state, updating live. Keyword plans SHALL be labelled as a keyword match with no LLM. Once the answer finishes, the list SHALL collapse to a one-line summary (step count and time) that can be expanded again. Under reduced motion, state changes SHALL appear without animated transitions.

#### Scenario: Live progress
- **WHEN** a three-step plan is running and step 2 finishes first
- **THEN** step 2 shows as done with its summary while steps 1 and 3 still show as running

#### Scenario: Collapse after answer
- **WHEN** the answer stream ends
- **THEN** the step list collapses to a summary line, and expanding it shows every step with its final state

### Requirement: Ask renders evidence from views
The Ask evidence panel SHALL render each view in plan step order, using the visual for its kind. Hovering a view row or card SHALL highlight its citations in the answer, and hovering a citation SHALL highlight the matching row or card. Sources that no view covers SHALL appear as evidence cards. Rendering SHALL be the same for LLM and keyword plans.

#### Scenario: Two views in one answer
- **WHEN** an answer has a `ranking` view and a `type_chart` view
- **THEN** both render in step order, and hovering citation `[n]` that belongs to the ranking highlights its row

#### Scenario: Keyword-planned answer
- **WHEN** "What does Earthquake do?" is answered from a keyword plan
- **THEN** the evidence panel shows the move view for Earthquake, the same as for an LLM plan

### Requirement: Home Ask tile uses the plan contract
The home page Ask tile SHALL show the streamed answer and its evidence from the `plan`, `view` and `sources` events. It SHALL NOT depend on a route.

#### Scenario: Ranking on the home tile
- **WHEN** the user asks "Fastest Pokémon" on the home tile
- **THEN** the tile shows the answer and the ranking from the `ranking` view
