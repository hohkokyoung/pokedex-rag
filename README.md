# pokérag

A premium Pokémon Pokédex combined with an AI research assistant ("Ask pokérag") grounded in real Pokémon data via a genuinely good RAG architecture.

> **Status: Complete — Phases 0–9.** Foundation → data → premium Pokédex → RAG → citations + streaming → SQL retrieval → routing + hybrid → personalization → evaluation → polish. Everything runs from a single `docker compose up`. To enable answer generation, add **either** an `ANTHROPIC_API_KEY` (preferred) **or** a free `GROQ_API_KEY` to `.env` — the backend uses Anthropic if present, else Groq. Retrieval, routing, and the whole UI work without any key.

## LLM providers

The Ask assistant is provider-agnostic (`app/rag/answer.py`): it prefers **Anthropic Claude** and falls back to **Groq** (free tier, OpenAI-compatible) when only a Groq key is set. `GET /api/ask/status` reports the active provider; the Ask UI shows a "powered by" line.

| Provider | Key | Default model (env override) |
| --- | --- | --- |
| Anthropic | `ANTHROPIC_API_KEY` ([console](https://console.anthropic.com/)) | `claude-opus-5` (`ANTHROPIC_MODEL`) |
| Groq (free) | `GROQ_API_KEY` ([console](https://console.groq.com/keys)) | `openai/gpt-oss-120b` (`GROQ_MODEL`) |

## Evaluation

A labeled eval set (`backend/eval/`) of 18 retrieval cases across structured / semantic / hybrid / personalized / refusal, plus 4 team-coach cases, with a harness measuring routing accuracy, retrieval recall, coach grounding, and — when a key is set — answer correctness, citation presence, and abstention. Current results (Groq `gpt-oss-120b`): **routing 100%, retrieval recall 100%, answer correctness 100%, citations 93%, abstention 100%**. A pytest guard (`test_eval.py`) fails the build if routing or recall regress.

The eval drove real fixes: it caught the model answering general-knowledge questions from world knowledge (abstention was 33%), which a stronger grounding/refusal prompt lifted to 100%; and it caught citations emitted as fullwidth `【n】` rather than `[n]`, now parsed both ways in the UI and the eval.

```bash
make eval    # prints the evaluation report
```

## Final polish (Phase 9)

Responsive down to 375px with no horizontal overflow; keyboard focus rings; `prefers-reduced-motion` honored across Lenis/GSAP/reveals; retrieval debugging surfaced in the Ask UI (route badge + per-source scores/types); lightweight request-timing middleware + `X-Process-Time-Ms` header; 66 backend tests; `CLAUDE.md` for contributors.

**Premium motion pass:** buttery lerp-based Lenis scroll; masked/clipped line reveal on the hero headline with a gradient wordmark; scroll-scrubbed parallax; a scroll-progress bar; per-route page transitions (`app/template.tsx`); magnetic CTAs; blur-clearing scroll reveals on a shared easing system; and an ambient drifting aurora for warmth. Resting states are authored so content (including stat bars/numbers) is correct even if animation frames never run.

## Retrieval architecture (Phases 3–6)

```
question → router.classify()
             ├── sql       → StructuredQuery over pokemon table
             ├── semantic  → RRF( vector cosine , full-text ts_rank )
             └── hybrid    → SQL rows  +  RRF(vector, full-text)
                                   ↓
                    numbered context → Claude → streamed answer + [n] citations
```

There is also a **matchup** route for type-coverage questions ("a non-legendary
special attacker with coverage against Dark"). Coverage is **movepool-based** — a
Pokémon covers a type if it can *learn* a super-effective damaging move (special-only
when a special attacker is asked for), judged from the ingested learnset rather than
just its own typing — and it honours **negation** ("non-legendary" excludes
legendaries and mythicals) via the shared `app/services/nlfilters.py` helper.

## RAG (Phase 3)

Local embeddings (`fastembed`, `BAAI/bge-small-en-v1.5`) → `knowledge_chunks` table with a pgvector `vector(384)` HNSW/cosine index. `POST /api/ask` embeds the question, retrieves top-k chunks by cosine similarity, builds a numbered context, and asks Claude to answer **only** from that context with inline `[n]` citations (or abstain). `GET /api/ask/status` reports whether the LLM is configured.

```bash
make chunks   # build + embed knowledge chunks (first run downloads the model)
```

Set `ANTHROPIC_API_KEY` in `.env` (optionally `ANTHROPIC_MODEL`, default `claude-opus-5`) and restart the backend to enable answers. The `/ask` page shows an "offline" note until then.

## Team Builder & Coach

Build competitive teams and have the assistant coach them. At `/teams` the single
user saves teams of up to six Pokémon and configures each slot's **ability**,
**nature**, **EV** and **IV** spreads, and up to four **moves** drawn from that
species' legal learnset — plus **opponent** teams to plan against. Moves, learnsets
and natures are ingested from the local PokéAPI CSVs (`app/ingest/run.py`); as
everywhere, **PokéAPI is never called at runtime**.

`app/services/team_analysis.py` is a deterministic engine — no LLM — that reports,
straight from the ingested type chart, base stats and `ev_yield`:

- defensive profile: each member's weaknesses and the team's **shared weaknesses**
  (a type that hits 3+ members super-effectively);
- offensive coverage: attacking types available across chosen damaging moves
  (falling back to STAB when none are set) and types the team can't hit neutrally;
- role balance: each member classified from its stats, and missing roles flagged;
- per-slot suggestions: a best ability + EV/nature spread grounded in base stats;
- vs-opponent: which opponent Pokémon threaten which of yours, and what to fix.

The **coach** (`POST /api/teams/{id}/ask`, SSE) feeds the team, that analysis, and
an optional opponent into the same grounded `RetrievedChunk` → Claude path as Ask,
so answers cite `[n]` and abstain when the data can't say (it won't invent
competitive tiers or real-world movesets the DB doesn't hold). `make eval` exercises
this coach path against a fixed player + opponent team.

**Coach-assisted drafting** — ask the coach to fill out the team ("draft the other
best 5, sweepers, non-legendary") and a deterministic recommender (`recommend.py`)
ranks real candidate Pokémon: by the role you asked for (sweeper / wall /
wallbreaker) or, by default, by how well they patch the analysis (resist shared
weaknesses, cover gaps); legendaries and current members are excluded. The draft
filters (role, legendary/mythical, types) are read from your wording. A **sentiment-
aware** keyword parser (`nlfilters.py`) handles negation on its own — "fuck legendaries",
"skip the legendaries" and "no legendaries" all exclude them, while "legendary dragons"
stays include — and the LLM (`draft_intent.py`) refines intent when available, using
**Groq strict `json_schema` structured output** so its JSON is shape-guaranteed and it
catches phrasings the keywords miss ("no ubers" → exclude). Either way the LLM only reads
the intent; a SQL query still picks the actual Pokémon. Candidates
are streamed as a `candidates` SSE event and shown as recommendation cards with
one-click **Add** buttons. You can also add conversationally — "add Garchomp"
resolves the species and fills the next empty slot (a `team_updated` SSE event
refreshes the view); "should I add Garchomp?" is treated as a question, not a
command. Nothing is added without a click or an explicit command.

Endpoints: `GET/POST /api/teams`, `GET/PUT/DELETE /api/teams/{id}`,
`PUT/DELETE /api/teams/{id}/slots/{slot}`, `GET /api/teams/{id}/analysis`
(`?opponent_id=`), `POST /api/teams/{id}/ask`; builder lookups
`GET /api/pokemon/{id}/moves` (`?q=`), `GET /api/pokemon/{id}/abilities`,
`GET /api/natures`.

## Frontend (Phase 2)

Read API (`backend/app/api/pokemon.py`): `GET /api/pokemon` (search `q`, `type` ×N, `generation`, `legendary`, `sort`, `order`, paginated), `GET /api/pokemon/{id_or_name}` (full detail + evolutions), `GET /api/types`, `GET /api/generations`.

UI (`frontend/`): App Router pages — `/` (hero + featured legends), `/pokedex` (browse/search/filter), `/pokedex/[dex]` (detail), `/ask` (Phase 3 placeholder). Motion: Lenis (smooth scroll), GSAP (stat bars + artwork scale-in), IntersectionObserver (scroll reveals), CSS 3D card tilt. Each Pokémon's first type drives an oklch accent across cards and detail pages.

## Data pipeline (Phase 1)

The [PokéAPI](https://github.com/PokeAPI/pokeapi) CSV dataset is downloaded into `data/raw/pokeapi/csv/` and ingested into PostgreSQL — **PokéAPI is never called at runtime**. Only default-form Pokémon (national dex 1–1025) are ingested, so `pokemon.id == species_id == dex number`.

```bash
make data        # migrate + ingest + download sprites
# or individually:
make migrate     # alembic upgrade head
make ingest      # app.ingest.run  -> 1025 pokemon, 8490 flavour texts, 484 evolutions
make sprites     # official-artwork PNGs -> data/sprites/ (served at /sprites/...)
```

Schema highlights: base stats are denormalised onto `pokemon` (with `base_stat_total`) for fast structured queries; types/abilities are many-to-many; multiple English flavour texts are retained per Pokémon as the seed corpus for Phase 3 embeddings.

## Stack

| Layer     | Technology                                              |
| --------- | ------------------------------------------------------- |
| Frontend  | Next.js 16 · React 19 · TypeScript · Tailwind CSS v4    |
| Backend   | Python 3.12 · FastAPI · SQLAlchemy (async) · Pydantic   |
| Database  | PostgreSQL 17 · pgvector                                |
| Tooling   | uv (Python) · Docker Compose                            |

## Project layout

```text
pokedex-rag/
├── backend/            FastAPI app (uv-managed)
│   ├── app/
│   │   ├── main.py         App entrypoint + CORS
│   │   ├── api/health.py   Liveness + readiness endpoints
│   │   └── core/           Settings & async DB engine/session
│   └── tests/
├── frontend/           Next.js app (App Router)
│   ├── app/                Layout + Phase-0 status page
│   └── lib/api.ts          Backend API client
├── data/raw/pokeapi/   Raw PokéAPI dataset (ingested in Phase 1)
├── docker-compose.yml  db + backend + frontend
└── .env.example        Copy to .env
```

## Quick start (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000 (shows live backend/DB status)
- Backend API: http://localhost:8000 · Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health · Readiness: http://localhost:8000/health/ready

## Running services locally (without Docker)

Backend:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

> When running the backend locally against the Compose database, set
> `DATABASE_URL=postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex` in `.env`
> (the Compose DB is published on host port **5433** to avoid clashing with a local Postgres).

## Tests & lint

```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && npm run lint
```

## Roadmap

Built one phase at a time (see project plan): **0** Foundation → **1** Pokémon data → **2** Premium Pokédex → **3** Basic RAG → **4** Citations + streaming → **5** SQL retrieval → **6** Query routing + hybrid retrieval → **7** Personalization → **8** Evaluation → **9** Final polish.
