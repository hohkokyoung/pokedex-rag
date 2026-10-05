# CLAUDE.md — pokérag

Guidance for working in this repo. See `README.md` for the full feature tour.

## What this is

A premium Pokédex (Next.js) + a retrieval-augmented "Ask pokérag" assistant
(FastAPI + PostgreSQL/pgvector + Claude). Single-user, local-only, no auth.
PokéAPI data is ingested into Postgres and **never called at runtime**.

## Architecture

```
frontend/  Next.js 16 · React 19 · TS · Tailwind v4 · GSAP · Lenis · Vanta
backend/   FastAPI · SQLAlchemy (async) · Alembic · Pydantic
  app/api/         health, pokemon (read), ask (RAG + SSE), profile,
                   builder (legal moves/abilities/natures), teams (CRUD +
                   /analysis + /ask coach SSE)
  app/models/      pokemon (relational), knowledge (pgvector chunks), user,
                   moves (moves + learnsets + natures), team (teams, members)
  app/services/    pokemon_query (read queries), builder (picker lookups),
                   teams (CRUD + hydration + validation), stats (competitive
                   stat maths), team_analysis (coverage/weakness/roles/vs)
  app/agent/       Ask's retrieval planner: tools (registry), ask_tools (read-only
                   adapters over app/rag + services), names (DB name lookup),
                   keyword_planner, llm_planner, executor, render (code answers),
                   cache, runner (plan → run → answer as events), views, sse
  app/rag/         embeddings, retrieval (vector), hybrid (FTS + RRF),
                   sql_retrieval (structured), learnset, matchup, similarity,
                   personalize, answer (Claude/Groq, streaming), coach (team-aware
                   grounded context), router (team coach only — see below)
  app/ingest/      run (CSV → DB; incl. moves/learnsets/natures),
                   build_chunks (chunks → embeddings)
  eval/            labeled eval set (expect_tools) + harness (plans, recall,
                   LLM calls/tokens, answers) + coach path
data/raw/pokeapi/  CSV dataset (git-ignored)   data/sprites/  artwork (git-ignored)
```

**Ask = a retrieval plan, not routes** (`app/agent/`, spec in `openspec/`). Every
question becomes a plan of 1–6 tool calls; the tools fetch from the DB; the answer is
grounded in what they returned. `runner.run_question` picks the cheapest planner:
answer cache → plan cache → the **keyword planner** (always run, free: resolves
Pokémon/form/move/ability/item/type names first via `names.py`, then picks tools from
cues — "What does Earthquake do?" → `move_info`, "Psychic" → type chart *and* move). If
its plan is `confident` (one unambiguous name in a fixed simple phrasing) it's used
as-is — the **fast path**, no planning call. Otherwise the **LLM planner** makes one
strict-JSON call (Groq `json_schema` / Anthropic forced tool; each step an `anyOf` of
per-tool arg schemas; SDK retries off). No key, `ASK_AGENT_ENABLED=false`, or a
failed/429/timed-out plan → the keyword plan, never a retry. Re-plan at most once, only
for LLM plans with an error step (empty results are answers). Steps run concurrently,
one DB session each.

Answers: if every step is **closed-form** (rankings/counts, learn checks, learner lists,
move info, type charts) `render.py` writes it in code — names, numbers and `[n]` can't
be hallucinated (`structured_answer.py` for rankings). Otherwise the LLM answers only
from the tool chunks, cites `[n]`, abstains when the data can't answer; if it's
unavailable or 429s, an extractive answer over the same sources. Budget: ≤ 3 LLM calls
per question (plan, re-plan, answer); fast-path closed-form questions use 0. Usage is
reported in `done` and logged.

Tools (`ask_tools.py`) are read-only, never see the question text (filters are typed
args — `legendary`, `types`, `attacker_class` …), and return `ToolResult`: citable
`RetrievedChunk`s **plus typed views** (`views.py`: ranking, pokemon_list, type_chart,
move_list, learnset, learners, learn_check) that the UI draws directly — nothing on the
frontend parses snippet text. SSE: `plan` (with `planner: llm|keyword`, `cached`) →
`step`* → `view`* → `sources` (each with `step`/`step_index`) → `delta`* → `done{usage}`;
there is no `route`. `rag/router.py` survives only for the team coach's dex retrieval
until the coach moves onto the agent.

Two cross-cutting NL filters live in `app/services/nlfilters.py` (a dep-free leaf
shared by the keyword planner and the team recommender): **legendary/mythical negation**
("non-legendary" excludes legendaries *and*, colloquially, mythicals — `plan.py` applies
the same rule to LLM-planned args) and — in the matchup retriever — **movepool-based
coverage**: a Pokémon "covers" type X if it can
*learn* a damaging move (special-only when a special attacker is asked for) whose type
is super-effective vs X, judged from the ingested learnset rather than STAB typing.

**Team Builder & Coach** (`/teams`): the single user saves teams of up to 6 —
each slot has an ability, nature, EV/IV spreads and up to 4 moves from the
species' legal learnset — plus opponent teams. `team_analysis` is a deterministic
engine (type coverage, shared weaknesses, role balance, per-slot EV/ability
suggestions, vs-opponent diff) built only from ingested data; the coach
(`/api/teams/{id}/ask`) feeds the team + that analysis (+ opponent) into the same
grounded `RetrievedChunk` → answer path, so advice is cited and abstains honestly
(e.g. it won't invent competitive tiers/movesets the DB lacks). Moves, learnsets
and natures come from the local PokéAPI CSVs — **never** a runtime PokéAPI call.

**Drafting & the add action** (`app/services/recommend.py`): when the user asks the
coach to draft/recommend additions, a deterministic recommender ranks real Pokémon.
Its filters (role, legendary/mythical include-exclude, preferred types) are extracted
from the question by the LLM (`app/rag/draft_intent.py`) and passed in as `DraftPrefs`.
It uses **Groq strict `json_schema` structured output** (`answer.quick_complete(json_schema=…)`,
`response_format` `json_schema`/`strict`, supported by `gpt-oss-120b`) so the JSON is
shape-guaranteed — this handles open-ended sentiment the keyword parser can't (e.g. "no
ubers" → exclude). The keyword parsers (`parse_role`/`allow_legendary`) remain the fallback
when there's no key or the call is rate-limited. `nlfilters` negation is itself
**sentiment-aware and proximity-based** so that fallback is still good on its own: a
rejecting token (no/without/skip/hate/fuck/…) in the 1-2 words before "legendar"/"mythical"
means exclude, so "fuck legendaries" excludes them with no LLM, while "legendary dragons"
and a trailing "which legendary is not a dragon" still read as include. (role — sweeper/wall/wallbreaker — else patch-holes; legendaries
excluded by default, current members excluded) and those candidates are (a) injected as
citable chunks so the coach recommends from real data and (b) emitted to the UI as a
`candidates` SSE event → recommendation cards with one-click **Add** buttons. The coach
also acts on a conversational imperative (`add <name>`, distinguished from a "should I
add …?" question): it resolves the species, fills the next empty slot, and emits a
`team_updated` SSE event. The UI reloads the team (slots + analysis) after any add.
Nothing is added without a click or an explicit command.

**Team strategy & summary** (`/teams`): `app/services/team_strategy.py` scores six axes
(offense/bulk/speed/setup/stall/support) from base stats plus curated move/ability lists —
set moves count fully, learnable ones partly (`now` vs `potential`), and TM staples
(Protect/Toxic/Rest/Sub) only when set. `app/rag/team_summary.py` writes a short
*descriptive* summary (no advice): the LLM only phrases rule-decided facts. It is stored
on the `teams` row with a roster fingerprint and rewritten in the background (debounced,
max 2 in flight) only when slots change — `GET /summary` never waits on the LLM, so opening
the page doesn't call it. Keep it that way. Grades stay deterministic (`frontend/lib/teamEval.ts`).

## Commands

```bash
make up        # docker compose up --build -d  (db + backend + frontend)
make data      # migrate + ingest + sprites + chunks  (host, against Compose DB)
make test      # backend pytest
make eval      # eval report (LLM if keyed; paced to Groq TPM — spends tokens)
               # cd backend && uv run python -m eval.run --keyless  (no LLM)
make lint      # ruff + eslint
```

Backend runs in Docker; the data pipeline scripts run on the **host** against the
Compose DB (published on host port **5433**; backend on **8001**, frontend **3000**
in this environment — overridable in `.env`).

## Conventions

- **Never call PokéAPI at runtime** — all data is pre-ingested.
- Retrieval components return `RetrievedChunk` so every tool shares one answer +
  citation path. New Ask capabilities are new **tools** (`app/agent/ask_tools.py`,
  read-only, typed args, a view when there's a visual) — not new intents/routes. Mark a
  tool `closed_form` only if code can fully answer from its result (add a renderer).
- LLM: Anthropic Claude (preferred) or Groq `gpt-oss-120b` via the async SDKs
  (`answer.py`); this environment runs Groq. Keep LLM calls bounded and Groq-friendly
  (free-tier TPM): planning ~2.4k input tokens. Without a key everything still works
  (keyword plans, code-rendered or extractive answers).
- Migrations: Alembic autogenerate, but the FTS `content_tsv` column is
  DB-managed and excluded via `include_object` in `alembic/env.py` — don't let
  autogenerate drop it.
- Backend lint excludes `alembic/`; FastAPI `Depends()` defaults are allowed
  (bugbear `extend-immutable-calls`).
- Frontend: entrance/scroll reveals use IntersectionObserver + CSS; GSAP is
  reserved for high-impact moments (stat bars, artwork). Respect
  `prefers-reduced-motion`.

## Gotchas

- Container `.venv` / `node_modules` are anonymous volumes. After adding deps:
  rebuild the image, and for the backend also recreate with
  `--renew-anon-volumes` so `.venv` refreshes.
- Next 16 dynamic route `params` is a `Promise` — `await` it.
