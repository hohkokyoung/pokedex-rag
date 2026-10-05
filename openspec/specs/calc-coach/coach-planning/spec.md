# calc-coach/coach-planning Specification

## Purpose
Answers questions asked in the damage calculator's coach by planning tool calls on the same agent as Ask and the team coach. The calculator's current state is always in context, and damage, threshold and build questions cost as few LLM calls as possible.

## Requirements

### Requirement: Calc questions are answered from a calc-scoped plan
Every calc coach question SHALL be answered by running a plan whose steps are tools available in the calc scope: damage calculation, survival thresholds, build proposals, and the Ask dex tools for learnsets, moves, type charts, coverage and rankings. The plan SHALL come from the LLM planner or the keyword planner, not from fixed intent checks.

#### Scenario: Damage question
- **WHEN** the calculator has Garchomp against Salamence and the user asks "Can Garchomp OHKO Salamence?"
- **THEN** the plan contains a damage step for Garchomp's chosen move against Salamence

#### Scenario: Dex question from the calculator
- **WHEN** the user asks the calc coach "Who learns Earthquake?"
- **THEN** the plan contains a learnset step for Earthquake, as on Ask

### Requirement: Calculator state is always attached
Every calc coach question SHALL include the calculator's current state as citable evidence without it being planned. That state covers each filled slot (side, Pokémon, nature, EVs, IVs, item, ability, current HP and chosen move), the level, singles or doubles, the field toggles, the hits the calculator currently shows, and any current build proposal. This evidence SHALL come first in the sources.

#### Scenario: Plain question about the matchup
- **WHEN** the user asks "Who wins this?"
- **THEN** the answer cites the calculator-state evidence for both sides' hits, and no extra lookup is needed

### Requirement: Simple calc questions skip the LLM planner
When the keyword planner reads a calc question as a single damage, threshold or build request about slots it can identify, it SHALL use its plan without calling the LLM planner. Recognised phrasings include "can X OHKO/2HKO Y", "how much does X do to Y", "how much Def/SpD/HP to survive Y's Z", "best build", and "make it …" follow-ups. Questions with several parts or ambiguous names SHALL go to the LLM planner.

#### Scenario: OHKO question
- **WHEN** an LLM key is configured and the user asks "Can Garchomp OHKO Salamence?"
- **THEN** no LLM call is made, and the answer is rendered from the damage result

#### Scenario: Build follow-up
- **WHEN** a build proposal exists and the user asks "Make it bulkier"
- **THEN** the plan revises that proposal without a planning call, using one build-coach call

### Requirement: Calc coach fallback without an LLM
When no LLM key is configured, or the planning call fails or is rate-limited, the calc coach SHALL use the keyword planner's plan. Damage and threshold answers SHALL still be produced from data. A build request SHALL say that it needs an LLM key.

#### Scenario: No key, damage
- **WHEN** no LLM key is configured and the user asks "Can Garchomp OHKO Salamence?"
- **THEN** the coach answers with the damage range and KO call

#### Scenario: No key, build
- **WHEN** no LLM key is configured and the user asks "Best build"
- **THEN** the coach replies that build suggestions need an LLM key, and no proposal is shown

### Requirement: Calc coach LLM usage is bounded and reported
A calc coach question SHALL use at most one planning call, one build-coach call and one answer call. When every non-context step is a damage, threshold or build result, the answer SHALL be rendered from those results with no further answer call. Each answer SHALL report its LLM calls and token usage.

#### Scenario: Build alone
- **WHEN** an LLM key is configured and the user asks "Best build"
- **THEN** the question reports 1 LLM call

### Requirement: Calc coach shows its plan
The calc coach box SHALL show each reply's plan steps live, folded to a one-line summary once the reply is complete. Under reduced motion, state changes SHALL appear without animated transitions.

#### Scenario: Damage reply
- **WHEN** a damage question runs
- **THEN** the reply shows its steps with their states, then folds to a summary line
