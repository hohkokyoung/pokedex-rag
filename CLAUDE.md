# CLAUDE.md — pokérag

Guidance for working in this repo. Read the doc for the area you're touching before
changing it:

| Area | Doc | Rules (specs) |
|---|---|---|
| System map | `docs/architecture/overview.md` | |
| Ask agent (planners, tools, answers) | `docs/architecture/ask-agent.md` | `openspec/specs/assistant/` |
| Retrieval (SQL, learnsets, matchups, vectors) | `docs/architecture/retrieval.md` | `openspec/specs/assistant/` |
| Team builder & coach | `docs/architecture/team-coach.md` | `openspec/specs/team-coach/` |
| Damage calc & its coach | `docs/architecture/damage-calc.md` | `openspec/specs/calc-coach/` |
| What each page does | `docs/product/` | |
| Dev setup, data pipeline, eval | `docs/guides/` | |

## What this is

A Pokédex (Next.js) + an assistant (FastAPI + PostgreSQL/pgvector + an LLM) that
answers only from ingested data. Single-user, local-only, no auth. PokéAPI data is
ingested into Postgres and **never called at runtime**.

```
frontend/  Next.js 16 · React 19 · TS · Tailwind v4 · GSAP · Lenis · Vanta
backend/   FastAPI · SQLAlchemy (async) · Alembic · Pydantic
  app/api/       routes          app/models/    ORM
  app/services/  deterministic logic (queries, teams, analysis, strategy, damage, duels)
  app/agent/     planners, tools, runner — Ask + team coach + calc coach
  app/rag/       retrievers, LLM answer client, team summary, build suggestions
  app/ingest/    CSV → DB, chunk embedding
  eval/          labelled eval set + harness
data/raw/pokeapi/  CSV dataset (git-ignored)   data/sprites/  artwork (git-ignored)
```

## Commands

```bash
make up        # docker compose up --build -d  (db + backend + frontend)
make data      # migrate + ingest + sprites + chunks  (host, against Compose DB)
make test      # backend pytest
make eval      # eval report (LLM if keyed; paced to Groq TPM — spends tokens)
               # cd backend && uv run python -m eval.run --keyless  (no LLM)
make lint      # ruff + eslint
make damage-fixtures  # regenerate the calc's TS→Python reference cases (Node ≥ 22.18)
```

Backend runs in Docker; the data pipeline scripts run on the **host** against the
Compose DB (published on host port **5433**; backend on **8001**, frontend **3000**
in this environment — overridable in `.env`).

## Rules that hold everywhere

- **Never call PokéAPI at runtime** — all data is pre-ingested.
- **Grounded answers.** Answers use only tool evidence, cite `[n]`, and abstain when
  the data can't answer. Closed-form results (rankings, learn checks, move info, type
  charts, damage, survival) are written by code, not the LLM.
- **New Ask capabilities are new tools**, not routes: `app/agent/ask_tools.py`,
  read-only, typed args, return `RetrievedChunk`s (+ a view for visuals). Tools never
  see the question text. Mark `closed_form` only if you add a renderer.
- **Writes are gated in code, not prompts.** Only `add_member` writes, and only when
  `is_imperative_add(question)` agrees; everything else is the user's Apply / Add /
  Replace / Revert click. Coach and calc answers are never cached.
- **Keyless works.** Every LLM feature has a fallback (keyword plan, code-rendered or
  extractive answer). A 429 or timeout means fall back — never retry in a loop.
- **LLM budget.** ≤ 3 calls per Ask question (plan, re-plan, answer); fast-path
  closed-form questions use 0. Planning prompt ~2.4k input tokens (`PROMPT_BUDGET`).
  LLM: Anthropic Claude (preferred) or Groq `gpt-oss-120b` via the async SDKs
  (`app/rag/answer.py`); this environment runs Groq, so keep calls Groq-friendly.
- **Team summary never blocks a page.** `GET /summary` must not call the LLM; it's
  rewritten in the background only when slots change. Team grades stay deterministic
  (`frontend/lib/teamEval.ts`).
- **One damage formula, two languages.** Change `frontend/lib/damageCalc.ts` → port to
  `backend/app/services/damage_calc.py` → `make damage-fixtures` → `make test`. Team
  duels (`services/battle.py`) are a separate engine.

## Conventions

- Migrations: Alembic autogenerate, but the FTS `content_tsv` column is DB-managed and
  excluded via `include_object` in `alembic/env.py` — don't let autogenerate drop it.
- Backend lint excludes `alembic/`; FastAPI `Depends()` defaults are allowed (bugbear
  `extend-immutable-calls`).
- Frontend: entrance/scroll reveals use IntersectionObserver + CSS; GSAP is reserved
  for high-impact moments (stat bars, artwork). Respect `prefers-reduced-motion`.
- Feature work goes through OpenSpec (`openspec/`): propose → apply → archive, one
  change per shippable phase.
- **Docs:** when behaviour described in `docs/` changes, update that page in the same
  commit. Each fact has one home — link, don't copy.

## Gotchas

- Container `.venv` / `node_modules` are anonymous volumes. After adding deps:
  rebuild the image, and for the backend also recreate with
  `--renew-anon-volumes` so `.venv` refreshes.
- A full `make ingest` fails once `knowledge_chunks` exist (FK to `pokemon`); use the
  standalone ingest targets for incremental changes (`docs/guides/data-pipeline.md`).
- Next 16 dynamic route `params` is a `Promise` — `await` it.
