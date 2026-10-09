# Architecture overview

A single-user, local-only app with no auth. Three Compose services:

```
browser ──► frontend  (Next.js 16 · React 19 · TS · Tailwind v4)     :3000
               │  fetch / SSE
               ▼   ◄── phone: mobile app (Flutter, mobile/) over the home network
            backend   (FastAPI · SQLAlchemy async · Pydantic)        :8000 (8001 here)
               │                     │
               │                     └──► LLM: Anthropic (preferred) or Groq — optional
               ▼
            db        (PostgreSQL 17 · pgvector)                     :5432 (5433 on host)
```

**PokéAPI is never called at runtime.** Its CSV dataset is ingested into Postgres
offline ([data-pipeline.md](../guides/data-pipeline.md)); the app reads only the DB.

**Everything works without an LLM key.** Plans fall back to the keyword planner and
answers to code-rendered or extractive text. A key adds LLM planning, narrated
answers, set/build suggestions and team summaries.

## Backend layout (`backend/app/`)

| Package | Holds |
|---|---|
| `api/` | routes: `health`, `pokemon` (read), `ask` (+ SSE), `profile`, `builder` (moves, abilities, items, natures, learners), `teams` (CRUD, analysis, strategy, summary, duel, coach SSE), `calc` (coach SSE) |
| `models/` | the ORM — tables and invariants in [data.md](data.md) |
| `services/` | deterministic logic: queries, builder lookups, team CRUD/validation, stats, analysis, team rating and profile, type chart, strategy, recommender, damage calc, duels, encounters |
| `agent/` | the planner + tools + runner behind Ask and both coaches — [ask-agent.md](ask-agent.md) |
| `rag/` | retrievers, the answer/LLM client, team summary, build suggestions — [retrieval.md](retrieval.md) |
| `ingest/` | CSV → DB, and chunk embedding |

The OpenAPI docs are at `http://localhost:<backend port>/docs`.

## Frontend layout (`frontend/`)

| Path | Holds |
|---|---|
| `app/` | routes: `/`, `/pokedex`, `/pokedex/[dex]`, `/ask`, `/teams`, `/teams/[id]` — see [../product/](../product/) |
| `components/` | page components; `components/agent/` draws plan steps, typed views and evidence for every agent surface |
| `lib/api.ts` | the typed backend client |
| `lib/damageCalc.ts` | the damage formula (mirrored in Python) — [damage-calc.md](damage-calc.md) |
| `lib/teamEval.ts` | display helpers for the team rating, which the backend computes — [team-coach.md](team-coach.md) |

Motion: entrance and scroll reveals use IntersectionObserver + CSS; GSAP is reserved
for high-impact moments (stat bars, artwork); Lenis for smooth scroll. All of it
respects `prefers-reduced-motion`.

## Mobile app (`mobile/`)

A Flutter client (iOS and Android) for the Pokédex, on the home network. It renders
values the backend computes and generates its API types and design tokens instead of
copying them ([ADR-010](../decisions/ADR-010.md)). What it does:
[product/mobile.md](../product/mobile.md). How to run and regenerate it:
[guides/mobile.md](../guides/mobile.md).

## Where the rules live

| Kind of fact | Home |
|---|---|
| What the system promises (SHALL + scenarios) | `openspec/specs/` |
| How it works and why | `docs/architecture/` |
| How to do things | `docs/guides/` |
| What each page does for a user | `docs/product/` |
| Conventions and gotchas for contributors | `CLAUDE.md` |
| Which code belongs to which docs/specs | `docs/components/*.yaml` |
| Decisions and why | `docs/decisions/` (older detail: `openspec/changes/archive/`) |
