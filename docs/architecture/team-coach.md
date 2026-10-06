# Team builder and coach

The `/teams` pages: saved teams, deterministic analysis and grades, an AI summary, and
a coach that is the [Ask agent](ask-agent.md) running in scope `team`. Rules it must
keep: `openspec/specs/team-coach/`.

## Data

A team (`app/models/team.py`) has up to 6 members. Each slot holds a species (or form),
ability, item, nature, EV/IV spreads and up to 4 moves. Every choice is validated
against ingested legal data — the species' learnset, abilities, natures, items
(`services/teams.py`, `services/builder.py`). Any team can be used as an opponent.

## Deterministic engines (no LLM)

| Module | Produces |
|---|---|
| `services/team_analysis.py` | type coverage, shared weaknesses (a type hitting 3+ members), role balance, per-slot ability/EV/nature suggestions, vs-opponent diff |
| `services/team_strategy.py` | six axes — offense, bulk, speed, setup, stall, support — from base stats plus curated move/ability lists. Set moves count fully, learnable ones partly (`now` vs `potential`); TM staples (Protect, Toxic, Rest, Sub) only when set |
| `services/recommend.py` | ranked candidate additions by role (sweeper / wall / wallbreaker) or by how well they patch the analysis |
| `services/battle.py` | turn-by-turn duels between two teams — a separate engine from the damage calculator, on purpose |
| `frontend/lib/teamEval.ts` | the letter grades: Coverage, Defence, Speed, Roles, Sets, Roster, and the overall /100 |

## The AI summary

`app/rag/team_summary.py` writes a short **descriptive** summary (what the team does,
no advice). The LLM only phrases facts the rules decided. It's stored on the `teams`
row with a roster fingerprint and rewritten in the background — debounced, at most 2
in flight — only when slots change. `GET /summary` never waits on the LLM, so opening
the page never calls it. Keep it that way.

## The coach

`POST /api/teams/{id}/ask` → `run_question(scope="team")`. The team, opponent, the
page's own report and the analysis travel in `AgentContext`.

- A built-in **`team_context`** step is always prepended (never planned): the page
  report first (authoritative), then members, analysis, suggestions and — with an
  opponent — their members and the matchup.
- The planner only adds *extra* steps. An empty plan is valid, and plain team
  questions take the fast path (0 planning calls).
- Most Ask dex tools are available here; lore search, look-alikes, profile picks and
  encounters are not (keeps the planning prompt ≤ 10.5k characters).

| Tool | Does | Writes? |
|---|---|---|
| `recommend_additions` | planner fills role/legendary/types → `recommend.py` → candidate cards with Add / Replace / Revert | only on the user's click |
| `propose_set_edit` | wraps `rag/build_suggest.py` (`attempts=1`), every field validated → a was → now card | only on Apply; Revert restores exactly |
| `add_member` | adds a Pokémon to the next empty slot | see the gate below |
| `duel` | runs `battle.py` against the opponent | no |

**Writes are gated in code, not in the prompt.** `add_member` saves only when
`is_imperative_add(question)` agrees ("add Garchomp" → yes; "should I add Garchomp?" →
no, you get an Add card). A real add emits `team_updated` and the reply offers Undo.
Nothing else writes; Apply / Replace / Revert are the user's clicks.

**Budget:** plan ≤ 1, build coach ≤ 1, answer ≤ 1. A set change alone or an add is
answered by code (0–1 calls); a draft ≤ 2. Coach answers are never cached.

**Without a key:** keyword plans; the answer is the page report, an analysis brief or
the candidate list; set changes say they need a key. `nlfilters` negation ("no
legendaries", "fuck legendaries" → exclude) still feeds the drafting args.
