# Proposal

## Why

"Which special attacker has coverage against Dark?" started answering with a list of
moves instead of Pokémon. The LLM planner chose `coverage_vs_types(want="moves")` once
(after six runs choosing `"pokemon"`), and the plan and answer caches then replayed that
answer for every repeat. Whether coverage lists Pokémon or moves is decided by wording
the keyword planner already reads deterministically, so it shouldn't be left to the LLM.

## What Changes

- Before an LLM plan runs or is cached, the runner sets every `coverage_vs_types`
  step's `want` from the question (`matchup.wants_moves`), the same rule the keyword
  planner uses. A question about attackers or Pokémon gets Pokémon; one that asks for
  moves gets moves.
- Only the corrected plan is cached, so a drifted pick can't be replayed.
- The plan trace records each LLM argument that code overrode (`corrected`), next to
  the LLM's original plan.

Out of scope: prompt wording (the planning prompt is nearly at `PROMPT_BUDGET`), other
tool args, re-plan steps (they only follow a failed lookup), team and calc coach
behaviour beyond sharing the same runner path.

## Capabilities

### New Capabilities

### Modified Capabilities
- `assistant/retrieval-planning`: coverage's Pokémon-or-moves choice follows the question, not the LLM.
- `assistant/plan-trace`: the trace lists LLM arguments code overrode.

## Impact

- `backend/app/agent/runner.py` (`_pin_coverage_want`, `PlanChoice.corrected`)
- `backend/app/agent/trace.py` (`corrected` field)
- `backend/tests/test_agent_runner.py`, `backend/eval/dataset.py` (x3)
- `docs/architecture/ask-agent-traces.md`
- No new LLM calls, no API or UI change.
