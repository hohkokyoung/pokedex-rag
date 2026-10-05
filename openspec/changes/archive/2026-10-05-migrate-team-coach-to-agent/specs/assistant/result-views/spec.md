# Spec Delta

## MODIFIED Requirements

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
