# Design

## Context

`coverage_vs_types` has `want: "pokemon" | "moves"`. The keyword planner sets it with
`matchup.wants_moves(question)`; the LLM planner set it freely, with no prompt guidance
and one few-shot using `"moves"`. LLM plans are cached per question (plan cache), and
finished answers too (answer cache).

## Goals / Non-Goals

**Goals:** one deterministic answer to "Pokémon or moves?" for a given question, on
every planner path; a trace that shows when code overrode the LLM.

**Non-Goals:** prompt changes; correcting other args; correcting re-plan steps.

## Decisions

- **Correct in the runner, not the tool.** Tools never see the question text; the
  runner already reads it (`is_imperative_add`). `_pin_coverage_want` runs in
  `_choose_plan` after the LLM plan is validated and before it is cached.
- **Reuse `matchup.wants_moves`** rather than a new rule, so keyword and LLM paths
  can't disagree.
- **Copy, don't mutate.** The corrected step is rebuilt with `make_step` into a copy
  of the plan; the LLM's original plan stays in `PlanChoice.llm_plan` for the trace.
- **No prompt change.** Code is authoritative and costs no prompt budget.

Docs affected: `docs/architecture/ask-agent-traces.md` (trace fields).

LLM budget: unchanged — 0 extra calls, 0 extra prompt characters.

## Risks / Trade-offs

- A question whose wording `wants_moves` misreads now gets the keyword planner's
  reading even when the LLM read it better. Accepted: consistency over occasional
  LLM insight, and the rule is already exercised by the keyword path and eval.
