# assistant/plan-trace Specification

## Purpose
Keeps a durable record of how the assistant planned and answered each question (which planner ran, why it fell back, the plans, step outcomes, answer tier and LLM usage) so its decisions can be reviewed after the fact on every surface.

## Requirements

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

### Requirement: Fallbacks are recorded with their reason
When the LLM planner was attempted but a cheaper path stood in, the trace SHALL record that a fallback happened and why: the provider rate-limited the call, the call timed out, the provider failed, or the LLM's plan had no valid steps. When the answer call failed and the answer was produced from the data instead, the trace SHALL record that too. When no LLM is configured, the trace SHALL say the keyword plan was used because no LLM was available, not that a fallback happened.

#### Scenario: Rate-limited planner
- **WHEN** an LLM key is configured, the keyword plan is not confident, and the planning call returns a 429
- **THEN** the trace shows planner `keyword`, fallback reason "rate-limited" and the keyword plan that was used

#### Scenario: No valid steps
- **WHEN** the LLM returns a plan with no valid steps for an Ask question
- **THEN** the trace shows fallback reason "no valid steps", the LLM's (invalid) plan and the keyword plan that was used

#### Scenario: No key
- **WHEN** no LLM key is configured and a question is asked
- **THEN** the trace shows planner `keyword`, no fallback, the reason "no LLM configured", and answer tier code-rendered or without an LLM

#### Scenario: Answer call rate-limited
- **WHEN** the answer call returns a 429 mid-answer
- **THEN** the trace records an answer fallback with reason "rate-limited" and answer tier without an LLM

### Requirement: Recording never affects answering
Recording a trace SHALL be best-effort. If the trace can't be built or written, the question SHALL still be answered and logged as before, and no error SHALL reach the user. Recording SHALL happen before the final `done` event, like the existing question log.

#### Scenario: Database write fails
- **WHEN** writing the trace raises an error
- **THEN** the answer streams normally to `done`, and a warning is logged on the server

### Requirement: Traces are retained for recent questions
Only the most recent 2,000 question log entries SHALL keep their trace. Older entries SHALL keep their question, route and time with the trace removed, so question history (used for personalization) is unaffected.

#### Scenario: Over the limit
- **WHEN** a new trace is recorded and 2,000 newer-or-equal entries already have traces
- **THEN** the oldest traced entry's trace is cleared and its question remains

### Requirement: Traces can be read locally
Traces SHALL be readable without database tools:
- a command-line listing of recent questions with scope, planner, fallback reason, step tools and LLM calls, filterable by scope, planner and fallback, plus a full view of one trace;
- a read-only API: a list endpoint (newest first, the same filters, a limit) and a single-trace endpoint.

Reading SHALL never modify traces or call an LLM.

#### Scenario: Filter fallbacks
- **WHEN** the user lists traces filtered to fallbacks
- **THEN** only questions whose trace records a planner or answer fallback are listed, newest first, with their reasons

#### Scenario: One trace
- **WHEN** the user requests one trace by its id
- **THEN** the full trace is returned: the keyword plan, the LLM plan, unhandled constraints, steps, answer tier and usage

#### Scenario: Unknown id
- **WHEN** the user requests a trace id that doesn't exist or has no trace
- **THEN** the API responds 404 and the command line says so
