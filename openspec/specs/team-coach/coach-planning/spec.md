# team-coach/coach-planning Specification

## Purpose

Answers questions about the user's team — and the opponent they're comparing it with — by planning lookups and actions as tool calls on the same agent as Ask, with the team always in context and as few LLM calls as possible.

## Requirements

### Requirement: Coach questions are answered from a team-scoped plan
Every team coach question SHALL be answered by running a plan whose steps are tools available in the team scope. The team scope SHALL include the Ask dex tools for rankings, learnsets, moves, abilities, items, type charts and coverage, plus the team tools (recommendations, set-edit proposals, adds, duels). Lore search, look-alikes, profile picks and encounter locations stay Ask-only. The plan SHALL come from the LLM planner or the keyword planner, not from fixed intent checks.

#### Scenario: Dex question asked on the team page
- **WHEN** the user asks the coach "Can Garchomp learn Swords Dance?"
- **THEN** the plan contains a learnset check for Garchomp and Swords Dance, as it would on Ask

#### Scenario: Mixed question
- **WHEN** an LLM key is configured and the user asks "Draft two fast non-legendary attackers and give Garchomp a faster set"
- **THEN** the plan contains a recommendation step (sweeper role, non-legendary) and a set-edit step for Garchomp

### Requirement: Team context is always attached
Every coach question SHALL include team-context evidence without it being planned. The context covers the team report, each member's set, the deterministic team analysis and the per-slot suggestions. When an opponent is selected it also covers the opponent's members and the matchup. The team report SHALL be built by the server from the backend's ratings and matchup: both teams' overall grade with every area's verdict and fix, and with an opponent the matchup verdict and tally, their top threats with your best answer to each, the best lead, and the members that win no pairing. Clients SHALL NOT send report text. This evidence SHALL be citable like any other source and SHALL come first in the sources.

#### Scenario: Plain team question
- **WHEN** the user asks "What's my team's biggest weakness?"
- **THEN** the answer cites the team analysis, and no extra lookup is required to answer

#### Scenario: Opponent selected
- **WHEN** an opponent team is selected and the user asks "How do I beat them?"
- **THEN** the evidence includes the opponent's members and the matchup (verdict, best answers, threats)

#### Scenario: Same report for every client
- **WHEN** the website and the app ask the same question about the same teams
- **THEN** the team report in the evidence is identical, and it matches the text the website used to build for the same teams (except an empty opponent, below)

#### Scenario: Empty opponent
- **WHEN** the selected opponent has no members
- **THEN** the report has the team's rating and no opponent or matchup lines

### Requirement: Plain team questions skip the LLM planner
When the keyword planner finds no names, actions or lookups beyond the team context in a coach question, the team context alone SHALL answer it, without calling the LLM planner.

#### Scenario: Weakness question
- **WHEN** an LLM key is configured and the user asks "What's my team's biggest weakness?"
- **THEN** no planning call is made and the answer uses one LLM call

#### Scenario: Question with a lookup
- **WHEN** the user asks "Which Water types beat my team?"
- **THEN** the question is not treated as plain, and the LLM planner (or the keyword planner without a key) plans the extra lookup

### Requirement: Drafting preferences are tool arguments
Recommending additions SHALL be a tool whose arguments (role, legendary and mythical inclusion, wanted types) are set by the planner. The tool SHALL rank real Pokémon with the existing deterministic recommender, excluding current members and, unless asked, legendaries. No separate LLM call SHALL be made only to extract drafting preferences.

#### Scenario: Draft with sentiment
- **WHEN** an LLM key is configured and the user asks "Draft the rest of my team, fuck legendaries, I like sweepers"
- **THEN** the recommendation step has role sweeper and excludes legendaries and mythicals, and the question uses at most one planning call and one answer call

#### Scenario: Draft without a key
- **WHEN** no LLM key is configured and the user asks "Draft the rest of my team — sweepers, non-legendary"
- **THEN** the keyword planner plans the recommendation step with role sweeper and legendaries excluded, and the answer lists the candidates from data

### Requirement: Coach fallback without an LLM
When no LLM key is configured, or the planning call fails or is rate-limited, the coach SHALL use the keyword planner's team-scope plan. When the answer needs an LLM that isn't available, the coach SHALL answer from data: the page report when one is sent, else a brief from the team analysis, plus any tool results. A set-change request SHALL say that it needs an LLM key.

#### Scenario: No key, plain question
- **WHEN** no LLM key is configured and the page sent its report
- **THEN** the coach's answer is the report's content, and no error is shown

#### Scenario: No key, set change
- **WHEN** no LLM key is configured and the user asks "Give Garchomp a faster set"
- **THEN** the coach replies that set suggestions need an LLM key, and no proposal is shown

### Requirement: Coach LLM usage is bounded and reported
A coach question SHALL use at most one planning call, one build-coach call and one answer call, plus at most one re-plan under the same rule as Ask. When a question's only result is a set-edit proposal, the build coach's explanation SHALL be the answer, with no further answer call. Each coach answer SHALL report its LLM calls and token usage.

#### Scenario: Set change alone
- **WHEN** an LLM key is configured and the user asks "Give Garchomp a faster set"
- **THEN** the question uses the build-coach call and no planning or answer call, and reports 1 LLM call

#### Scenario: Draft
- **WHEN** an LLM key is configured and the user asks the coach to draft additions
- **THEN** the question reports at most 2 LLM calls

### Requirement: Coach shows its plan
The team coach SHALL show each reply's plan steps live, folded to a one-line summary once the reply is complete, as on Ask. Under reduced motion, state changes SHALL appear without animated transitions.

#### Scenario: Draft reply
- **WHEN** a draft question runs
- **THEN** the reply shows the team context and recommendation steps with their states, then folds to a summary line
