# Spec Delta

## MODIFIED Requirements

### Requirement: Results are streamed as typed views
A step whose result has a visual form SHALL send a `view` event. The event carries the step id, a view kind, structured data for that kind, and the step-local evidence indices its data came from. Supported kinds are `ranking`, `pokemon_list`, `type_chart`, `move_list`, `learnset`, `learners`, `learn_check`; for the team coach, `candidates`, `set_edit`, `member_added` and `duel`; and for the calc coach, `damage`, `survive` and `build_proposal`. View data SHALL come from the tool result, not from the LLM answer. Each entry in the `sources` event SHALL identify the step and step-local index it came from, so views can be linked to global source numbers.

#### Scenario: Ranking view
- **WHEN** a Pokémon query sorted by Speed returns 5 rows
- **THEN** a `ranking` view is sent with the stat axis (`speed`), the 5 rows (name, dex number, types, value) in order, the total match count, and their evidence indices

#### Scenario: Step without a visual
- **WHEN** a semantic search step returns description passages only
- **THEN** no `view` event is sent for it, and its passages appear only in sources

#### Scenario: Set-edit view
- **WHEN** a coach set-edit step proposes a new set for Garchomp
- **THEN** a `set_edit` view is sent with the team side, slot, the current set and the proposed set (moves, ability, nature, item, EVs) and the fields that change

#### Scenario: Damage view
- **WHEN** a calc damage step computes Garchomp's Earthquake against Salamence with a Choice Band what-if
- **THEN** a `damage` view is sent with the attacker and defender slots, the move, the current min–max % and KO call, and the what-if's min–max % and KO call

### Requirement: Ask shows live plan steps
While a question runs, the Ask page SHALL show each step with its reason and current state, updating live. Keyword plans SHALL be labelled as planned by keywords, with the question's LLM call count shown alongside (a keyword plan can still spend a call on a build or an answer). Once the answer finishes, the list SHALL collapse to a one-line summary (step count and time) that can be expanded again. Under reduced motion, state changes SHALL appear without animated transitions. When the plan reports constraints it couldn't apply, the answer's opening note SHALL be shown as a notice before the verdict, never as the verdict.

#### Scenario: Live progress
- **WHEN** a three-step plan is running and step 2 finishes first
- **THEN** step 2 shows as done with its summary while steps 1 and 3 still show as running

#### Scenario: Collapse after answer
- **WHEN** the answer stream ends
- **THEN** the step list collapses to a summary line, and expanding it shows every step with its final state

#### Scenario: Unapplied constraint notice
- **WHEN** the answer opens with a note that a constraint couldn't be applied
- **THEN** the note is shown as a notice and the next paragraph is shown as the verdict

