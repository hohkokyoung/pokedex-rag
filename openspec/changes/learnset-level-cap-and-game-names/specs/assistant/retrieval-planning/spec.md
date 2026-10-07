# Spec Delta

## MODIFIED Requirements

### Requirement: Filters are explicit tool arguments
Filters a planner decides, such as types, damage class, legendary/mythical inclusion, generation, game (for Pokémon queries: present in that game's data), learn method (level-up, TM, tutor, egg), a level cap (learned by level-up at or below a level), and stat thresholds, SHALL be passed as tool arguments. Tools SHALL apply them as given rather than re-deriving them from the question text.

#### Scenario: Legendary exclusion on learners
- **WHEN** a plan has a learnset step for Earthquake with `legendary: false`
- **THEN** no legendary Pokémon appears among the returned learners, whatever the question's wording

#### Scenario: Game on a Pokémon query
- **WHEN** a plan ranks Pokémon by base stat total with `game: "Scarlet/Violet"`
- **THEN** only Pokémon in Scarlet / Violet's data are ranked, and the answer names the game

#### Scenario: Learn method on learners
- **WHEN** a plan has a learnset step for Earthquake restricted to Water types with `method: level-up`
- **THEN** only Water-types that learn Earthquake by level-up are counted and listed, and TM-only learners are not

## ADDED Requirements

### Requirement: Level caps on learnset questions
A question that limits how late a move is learned ("below lvl 30", "before level 30", "by level 30", "lv 30 or below") SHALL be planned as a learnset step with a level cap: "below/before/under N" caps at N − 1, and "by/until/up to N" or "N or below" caps at N. A cap SHALL restrict the lookup to level-up. Such a question SHALL NOT take the fast path.

#### Scenario: Below a level
- **WHEN** the keyword planner receives "does garchomp learn crunch below lvl 30"
- **THEN** the plan is one learnset step for Garchomp and Crunch with method level-up and a cap of 29, and it is not fast-pathed

#### Scenario: By a level
- **WHEN** the keyword planner receives "does Garchomp get Crunch by level 30"
- **THEN** the learnset step has a cap of 30

#### Scenario: Capped learners
- **WHEN** a plan asks who learns Crunch by level-up with a cap of 20
- **THEN** fewer Pokémon are counted than with no cap, and Garchomp is not among them

#### Scenario: Rate-limited planner keeps the cap
- **WHEN** the LLM planning call is rate-limited for "does garchomp learn crunch below lvl 30"
- **THEN** the keyword plan still carries the cap of 29, and the answer is the capped one

### Requirement: A capped "no" says when the move is learned
When a learn check with a level cap finds no qualifying level-up, the answer SHALL say the Pokémon doesn't learn the move by level-up by that level and, if it learns it later, how and when it does. It SHALL be written by code with a citation, with no answer LLM call.

#### Scenario: Garchomp and Crunch below Lv 30
- **WHEN** a learn check asks whether Garchomp learns Crunch by level-up with a cap of 29
- **THEN** the answer reads that Garchomp doesn't learn Crunch by level-up by Lv 29, and that it learns it on evolving (Lv 48), with a citation

#### Scenario: Within the cap
- **WHEN** the same check has a cap of 48
- **THEN** the answer is yes

### Requirement: Evolution moves name their evolution level
A move learned the moment a Pokémon evolves SHALL be described as learned on evolving, with the level it evolves at when that is a level, rather than as level-up with no level. Against a level cap it SHALL count at that evolution level, and SHALL NOT count when the evolution has no level (for example item or trade).

#### Scenario: Garchomp's Crunch in Scarlet / Violet
- **WHEN** a learn check asks whether Garchomp learns Crunch by level-up in Scarlet / Violet
- **THEN** the answer is yes, on evolving (Lv 48)

### Requirement: Game names mean the original unless a remake is asked for
A game named by a bare title SHALL resolve to the original game, not a remake whose title contains it ("Diamond" → Diamond / Pearl). "new …" or "… remake(s)" SHALL resolve to the remake ("new Diamond and Pearl" → Brilliant Diamond / Shining Pearl). Leading filler such as "old", "original" or "the" SHALL be ignored.

#### Scenario: Bare name from the LLM planner
- **WHEN** a learnset step has `game: "diamond"`
- **THEN** the lookup uses Diamond / Pearl, and the answer names Diamond / Pearl

#### Scenario: Old games
- **WHEN** the keyword planner receives "can garchomp learn crunch in old diamond and pearl game"
- **THEN** the step's game is Diamond / Pearl

#### Scenario: Remakes
- **WHEN** the keyword planner receives "can garchomp learn crunch below level 50 in new diamond and pearl game"
- **THEN** the step's game is Brilliant Diamond / Shining Pearl

#### Scenario: Remake titles still resolve directly
- **WHEN** a step names "brilliant diamond", "ultra sun" or "black 2"
- **THEN** it resolves to Brilliant Diamond / Shining Pearl, Ultra Sun / Ultra Moon or Black 2 / White 2

### Requirement: An unmatched game is stated, not dropped
When a question clearly names a game ("in the … game", "in the new …") and no game matches it, the keyword plan SHALL list it as a constraint it couldn't apply, so the answer opens with the not-applied note. Such a question SHALL NOT take the fast path. Everyday phrases ("in the sun") and games that do resolve SHALL NOT be flagged.

#### Scenario: Unknown game on the keyword path
- **WHEN** no LLM key is configured and the user asks "can garchomp learn crunch in the newest gizmo game"
- **THEN** the answer opens with a note that the game "newest gizmo game" couldn't be applied, followed by the learn check without a game

#### Scenario: Recognised game is not flagged
- **WHEN** the keyword planner receives "can garchomp learn crunch in new diamond and pearl game"
- **THEN** the plan lists no unapplied constraint
