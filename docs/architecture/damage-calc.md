# Damage calculator and its coach

The home page's damage calculator runs in the browser; its coach is the
[Ask agent](ask-agent.md) running in scope `calc`. Rules: `openspec/specs/calc-coach/`.

## One formula, two languages

| Where | File | Used by |
|---|---|---|
| Browser | `frontend/lib/damageCalc.ts` | the calculator UI |
| Backend | `backend/app/services/damage_calc.py` | the coach's `damage_calc` / `survive_threshold` tools |

The **turn** (move order, doubles targeting, HP carried from hit to hit, Focus Sash, KO
calls) is shared the same way: `frontend/lib/calcTurn.ts` (`playTurn`, used by the
calculator) and `backend/app/services/calc_turn.py` (`POST /api/calc/turn`, used by the
mobile app). `GET /api/calc/options` lists the items and abilities the maths models
(`damage_calc.CALC_ITEMS` / `CALC_ABILITIES`; a test checks each one changes damage).

They must agree exactly. `make damage-fixtures` runs
`frontend/scripts/damage-fixtures.ts` under Node type stripping (Node ≥ 22.18) and
writes `backend/tests/fixtures/damage_cases.json` (~250 hand-picked and seeded hits) and
`turn_cases.json` (~65 whole turns, singles and doubles);
`tests/test_damage_calc.py` and `tests/test_calc_turn.py` check the Python ports against
every one.

**To change the maths or the turn:** edit the TS → port the change to Python → `make
damage-fixtures` → `make test`.

Team duels (`services/battle.py`) are a separate engine and stay separate.

## The coach

`POST /api/calc/ask`. The page sends the calculator's state with each question: the
four sets, chosen moves, aims, field, the hits it shows, and the coach's current build
proposal and thread.

- **Client stats are never trusted.** `services/calc_state.resolve_state` re-reads
  types, base stats (forms included) and move data from the DB.
- A built-in **`calc_context`** step is always prepended (never planned).
- Tools (plus the team-scope dex tools):

| Tool | Answers | LLM calls |
|---|---|---|
| `damage_calc` | "can X OHKO Y?", what-ifs via typed `changes` (item, ability, nature, EVs, HP, field) | 0 (closed-form) |
| `survive_threshold` | least HP + Def/SpD EVs from the *free* EVs, then a bulk nature; "already survives" has no Apply | 0 (closed-form) |
| `propose_build` | wraps `rag/build_suggest.py` (`attempts=1`) with the current proposal + thread; its `why` is the answer | 1 |

The keyword planner knows the calc phrasings: OHKO / survive / build, `with
<item/nature/EVs>`, and — when a proposal is on the table — imperative tweaks like "no
Choice item" or "swap X for Y".

**Nothing is saved.** Cards Apply into the calculator only, with Revert. Calc answers
are never cached.
