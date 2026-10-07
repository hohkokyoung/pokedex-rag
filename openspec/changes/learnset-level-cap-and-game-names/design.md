# Design

## Context

See proposal.md (Why). The learnset lookup has two tables. One is a per-game table
where an evolution move is stored as level 0. The other is an any-game summary
table that keeps one row per Pokémon × move. The planners (keyword and LLM) only
know what the lookup can do through its arguments, so a constraint with no
argument was always dropped. The "couldn't be applied" note existed, but only the
LLM planner filled it.

## Goals / Non-Goals

**Goals:** carry level caps and game names through both planners the same way;
never answer a narrower question with a broader one without saying so.

**Non-Goals:** fixing the any-game "Lv 1" reading of evolution moves (needs an
ingest or summary-table change, tracked separately); level floors or ranges.

## Decisions

- **One optional `max_level` on the existing learnset arguments**, not a new tool.
  It goes through the same schema the LLM planner already sees, at about 70
  characters of prompt. A cap forces level-up, because only level-up has a level.
  *Alternative:* a separate "learned by level" tool, which would cost more prompt
  budget and duplicate the learnset lookup.
- **A cap reads the per-game table and treats level 0 as the evolution level**,
  from the existing evolution data (`pokemon_evolutions.min_level`). Item, trade
  and friendship evolutions have no level, so they don't satisfy a cap. *Why:*
  saying "yes, below 30" for a move that only comes on a Lv 48 evolution would be
  wrong.
- **A capped "no" runs a second, uncapped lookup** to say when the move is
  learned. That's one extra indexed query and no LLM.
- **Game resolution ranks by fewest extra title words, then newest.** "diamond"
  matches both `diamond-pearl` and `brilliant-diamond-shining-pearl`; the
  shorter title is the original. "new"/"remake" flips it to the longest title
  that contains every word. *Alternative:* a hand-kept list of remakes, which is
  data the version-group names already encode.
- **The keyword planner reports an unmatched named game as `unhandled`**, using
  the existing note and abstain logic in the runner. A phrase counts as a named
  game only when it says "game/version/remake" or "new …", which keeps everyday
  phrases ("in the sun") out.

Reused: `learnset.resolve_game`, `find_game_in_text`, the runner's gap note,
`render._learn_check`, `LearnCheckView`/`LearnersView`. Nothing becomes
fallback-only or is removed.

**LLM budget:** unchanged. A capped question isn't fast-pathed, so it costs 1
planning call. The answer is code-rendered, so 0 answer calls; ≈ 2.6k input
tokens per question as seen in traces. On a 429 the keyword plan is used, with 0
calls.

**Docs affected:** `docs/architecture/retrieval.md` (learnset row: cap, evolution
moves, game names), `docs/architecture/ask-agent-planners.md` (keyword parsing,
unmatched games, prompt sizes), `docs/architecture/ask-agent.md` (tools table),
`docs/product/ask.md` (an example question).

## Risks / Trade-offs

- [The LLM may still pass an odd game string ("DP remake")] → it goes through the
  same resolver. An unresolvable game is an unresolved-name error step, which can
  trigger the one re-plan.
- [The "game/version" cue may miss an unmatched game phrased without those words
  ("in gizmo")] → that game is dropped as before. The narrow cue is deliberate, to
  avoid false notes.
- [The team and calc planning prompts grew slightly] → still under
  `PROMPT_BUDGET`; the budget test guards it.
