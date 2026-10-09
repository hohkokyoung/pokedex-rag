# Proposal

## Why

Learnset questions with a level or a game in them were answered as broader questions
without saying so. "Does Garchomp learn Crunch below lvl 30?" came back "Yes — by
level-up" because nothing could carry the level. "…in old Diamond and Pearl" was
answered for Brilliant Diamond / Shining Pearl. "…in new Diamond and Pearl" lost the
game when the planner fell back after a 429. Each answer looked confident and
answered the wrong question. This change is written retroactively: the code and
tests already exist, and the specs now catch up with them.

## What Changes

- The learnset lookup takes a **level cap** ("below lvl 30" → learned at or below
  Lv 29; "by level 30" → Lv 30). A cap means level-up only.
- **Evolution moves** (learned the moment a Pokémon evolves) read "on evolving
  (Lv N)" with the evolution level. They count against a cap at that level.
- A capped "no" also says when the Pokémon does learn the move ("…by Lv 29; it
  learns it on evolving (Lv 48)").
- **Game names:** a bare name means the original game ("Diamond" → Diamond /
  Pearl, not the remake). "new …" or "… remake" means the remake. Leading filler
  ("old", "original", "the") is ignored.
- A game the question clearly names but that matches nothing is **reported as not
  applied** (the existing "couldn't be applied" note), never silently dropped. This
  now also holds for the keyword plan, not just the LLM plan.

Out of scope:
- The no-filter any-game answer still reads an evolution move as "Lv 1" (for
  example "Can Garchomp learn Crunch?"). That comes from the any-game summary
  table and is tracked separately.
- Level floors ("above level 50") and level ranges.
- The team coach and calc coach surfaces. The learnset tool is shared with them,
  but no coach planning, prompts or UI change.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `assistant/retrieval-planning`: the filters requirement gains a level cap; game
  names resolve to the original game unless a remake is asked for; a named but
  unmatched game is stated as not applied by either planner; evolution moves name
  their evolution level.

## Impact

- Backend: `app/rag/learnset.py` (level cap, evolution level, game resolution),
  `app/agent/ask_tools.py` (`learnset` argument), `app/agent/keyword_planner.py`
  (level-cap and unmatched-game handling), `app/agent/views.py` and
  `app/agent/render.py` (the capped "no" answer).
- Frontend: the learn-check strip (`components/agent/views/Strips.tsx`) and its
  type (`lib/api.ts`) show the cap on a "no".
- LLM: the planning schema gains one optional argument. The prompt stays under
  budget (ask ≈ 10.0k, team ≈ 10.7k, calc ≈ 10.5k of 11k characters). There are
  no extra calls.
- Eval: one new learnset case (`v5b`).
