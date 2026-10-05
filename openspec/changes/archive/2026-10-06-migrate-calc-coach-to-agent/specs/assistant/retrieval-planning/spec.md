# Spec Delta

## MODIFIED Requirements

### Requirement: Filters are explicit tool arguments
Filters a planner decides, such as types, damage class, legendary/mythical inclusion, generation, game, learn method (level-up, TM, tutor, egg), and stat thresholds, SHALL be passed as tool arguments. Tools SHALL apply them as given rather than re-deriving them from the question text.

#### Scenario: Legendary exclusion on learners
- **WHEN** a plan has a learnset step for Earthquake with `legendary: false`
- **THEN** no legendary Pokémon appears among the returned learners, whatever the question's wording

#### Scenario: Learn method on learners
- **WHEN** a plan has a learnset step for Earthquake restricted to Water types with `method: level-up`
- **THEN** only Water-types that learn Earthquake by level-up are counted and listed, and TM-only learners are not

## ADDED Requirements

### Requirement: Constraints the tools can't express are stated
The LLM planner SHALL list, with every plan, the constraints the question states that no tool argument can express (empty when there are none). When the list is not empty, the answer SHALL open with a note naming them and saying the results answer a broader question. When no step at all can be planned for such a question, the answer SHALL say what can't be applied instead of falling back to a broader keyword plan, without an answer LLM call.

#### Scenario: Partly expressible
- **WHEN** the planner ranks Pokémon by Attack and reports "trade evolution" as unhandled
- **THEN** the answer opens with a note that the trade-evolution constraint couldn't be applied, followed by the ranking

#### Scenario: Nothing expressible
- **WHEN** the planner returns no steps and reports an unhandled constraint
- **THEN** the answer says it can't answer from the Pokédex data and names the constraint, and no keyword-plan fallback runs

### Requirement: Level-up levels name their games
When no game is asked for and a Pokémon learns a move by level-up at different levels across games, the answer SHALL give the newest game's level with those games named, and the other games' level range, rather than a single level.

#### Scenario: Swampert and Earthquake
- **WHEN** the user asks which Water-types learn Earthquake
- **THEN** Swampert's entry reads by level-up at Lv 1 in SwSh/BDSP and Lv 51–52 in other games
