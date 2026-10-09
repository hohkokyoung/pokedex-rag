# Spec Delta

## MODIFIED Requirements

### Requirement: Every answered question records a plan trace
When a question finishes on any surface (Ask, team coach, calc coach), the system SHALL record a trace with that question's log entry. The trace SHALL contain:
- the scope;
- which planner produced the plan: `cached`, `keyword` (fast path, or no LLM available) or `llm`;
- whether the keyword plan was confident, and the keyword plan itself (each step's tool, arguments and reason);
- the LLM plan when one was made (each step's tool, arguments and reason), and the constraints it reported as unhandled;
- any LLM plan arguments code overrode before running the plan, with the LLM's original and the value used;
- any re-plan steps;
- each executed step's final state (done, empty or error), summary and duration;
- how the answer was produced: code-rendered, LLM-written, without an LLM, or a code abstain for an inexpressible question;
- the LLM calls and tokens used, and the total time.

Recording SHALL make no LLM calls and SHALL NOT change the answer, its events or its timing as seen by the client.

#### Scenario: Fast path
- **WHEN** an LLM key is configured and the user asks "Can Garchomp learn Earthquake?"
- **THEN** the recorded trace shows planner `keyword`, the keyword plan as confident with one learnset step, no LLM plan, answer tier code-rendered and 0 LLM calls

#### Scenario: LLM plan
- **WHEN** the LLM planner plans "Which Fire types learn Will-O-Wisp, and what is Fire weak to?"
- **THEN** the trace shows planner `llm`, the keyword plan marked not confident, the LLM plan's two steps with their tools, arguments and reasons, each step's final state and summary, and the LLM calls and tokens used

#### Scenario: Unhandled constraint
- **WHEN** the LLM planner reports "trade evolution" as unhandled
- **THEN** the trace lists "trade evolution" among the unhandled constraints

#### Scenario: Team and calc coach
- **WHEN** a question is asked in the team coach or the calc coach
- **THEN** its trace has that scope and includes the built-in context step with the planned steps

#### Scenario: Cached answer
- **WHEN** a repeated Ask question is served from the answer cache
- **THEN** its trace shows planner `cached` and 0 LLM calls

#### Scenario: Overridden argument
- **WHEN** the LLM plans coverage with moves for "Which special attacker has coverage against Dark?"
- **THEN** the trace shows the LLM plan with moves, the override to Pokémon, and the executed step
