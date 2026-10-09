# pokérag

A Pokédex with an assistant that answers from real data. Browse all 1,025 Pokémon,
build and rate teams, run damage and catch-rate calculations, and ask questions in
plain English — every answer cites the records it came from, and says so when the data
can't answer.

Local and single-user. All Pokémon data is ingested from the
[PokéAPI](https://github.com/PokeAPI/pokeapi) CSV dataset into Postgres; nothing calls
PokéAPI at runtime. Everything works without an LLM key; a key adds narrated answers,
smarter planning, set suggestions and team summaries.

## Showcase

[![pokérag in 34 seconds: the Pokédex, a Garchomp detail page, Ask answering with citations, team grades and the dashboard calculators](docs/media/pokerag-promo.webp)](docs/media/pokerag-promo.mp4)

[Motion video in full quality (MP4, 1440p)](docs/media/pokerag-promo.mp4) ·
[Two-minute screen tour of every page (MP4, 1080p)](docs/media/pokerag-tour.mp4)

Both are rendered from the running app: `make video-promo` and `make video-tour`
([how](docs/guides/media.md)).

## What's in it

- **Home** — a dashboard: your teams at a glance, a type calculator, the Ask tile, a
  singles/doubles **damage calculator** with its own coach, a move/ability/item lookup,
  a nature helper and a catch-rate calculator. → [docs/product/home.md](docs/product/home.md)
- **Pokédex** — search, filter and sort every species; detail pages with stats,
  matchups, abilities, per-game movesets, evolutions, dex entries and where to catch
  it. → [docs/product/pokedex.md](docs/product/pokedex.md)
- **Ask** — questions about rankings, learnsets, moves, matchups, look-alikes, lore
  and more, answered from a retrieval plan with citations. → [docs/product/ask.md](docs/product/ask.md)
- **Teams** — build teams of six with legal sets, get graded, compare against another
  team, and ask a coach that can propose set changes and drafts (nothing saved until
  you apply). → [docs/product/teams.md](docs/product/teams.md)
- **Mobile app** — the Pokédex on iOS and Android (Flutter), read from your own
  pokérag server on the home network. → [docs/product/mobile.md](docs/product/mobile.md)

## Quick start

```bash
cp .env.example .env
```

```bash
make up
```

```bash
make data
```

`make data` (first run only) migrates, ingests the CSVs, downloads sprites and builds
the search index; it runs on the host against the Compose database. Then open
http://localhost:3000. The API docs are at http://localhost:8000/docs.

To enable LLM features, set **one** of `ANTHROPIC_API_KEY` (preferred) or
`GROQ_API_KEY` (free tier) in `.env` and restart the backend. Ports, keys and dev
workflow: [docs/guides/local-dev.md](docs/guides/local-dev.md).

## How the RAG works

Ask, the team coach and the damage-calc coach all run on one retrieval agent. There
are no hand-written routes per question type: each question becomes a **plan** of
typed tool calls, the tools read the database, and the answer is built only from what
they return.

```
question ──► answer cache? ──► plan cache? ──► keyword planner ──► LLM planner (only if needed)
                                                     │
                                         plan: 1–6 typed tool calls
                                                     │
                     ┌───────────────┬───────────────┼────────────────┬──────────────┐
                     ▼               ▼               ▼                ▼              ▼
               query_pokemon     learnset      type_matchup    semantic_search   similar_to …
               (SQL filters)   (SQL joins)    (type chart)   (vector + FTS)   (embeddings)
                     └───────────────┴───────┬───────┴────────────────┴──────────────┘
                                             ▼
                      RetrievedChunks (numbered [n]) + typed views for the UI
                                             │
              every step closed-form? ──► code writes the answer (0 LLM calls)
              otherwise ──────────────► LLM answers from the chunks only, citing [n]
              no key / 429 / timeout ─► extractive answer that quotes the chunks
```

**Planning.** A free keyword planner always runs, and its plan is used as-is when
it's confident (or when there's no LLM key). Otherwise one LLM call plans, falling back
to the keyword plan on a 429, timeout or bad output, and it can re-plan once if a step fails.
That caps a question at **3 LLM calls** (plan, re-plan, answer), and closed-form
questions use none. Tools get validated Pydantic arguments, never the question text,
so both planners produce the same lookups for the same arguments. Independent steps
run concurrently with an 8 s timeout each.

**Retrieval.** Most questions have exact answers, so most retrieval is SQL. Vector
search covers only what exists solely in prose.

| Retriever | Answers | How |
|---|---|---|
| Structured SQL | "fastest non-legendary Fire types", "Speed above 100 in Gen 4" | a typed query (types, generation, legendary, stat filters, sort, game) → parameterised SQLAlchemy; no raw SQL from users or the LLM |
| Learnsets | "can Pikachu learn Surf in Scarlet?", "who learns Earthquake?" | game-aware joins over learnsets, moves and version groups, with level caps |
| Matchups | "what is Fire weak to?", "special attackers that cover Dragon" | the ingested type chart; coverage is movepool-based |
| Hybrid search | "Fire types that live near volcanoes" | pgvector cosine (top 12) + Postgres full-text (top 12), merged by Reciprocal Rank Fusion |
| Similarity | "Pokémon like Jigglypuff" | nearest profile embeddings, excluding the target's evolution line |

The text index is about 9,500 chunks: one generated profile per Pokémon plus every
distinct English Pokédex entry. They're embedded locally with `BAAI/bge-small-en-v1.5`
(384 dims, fastembed, no API) under an HNSW index.

**Grounding.** The LLM sees only the retrieved chunk text, numbered `[n]`, and must
cite it or abstain. Rankings, learn checks, move info, type charts, damage and
survival results are written by code, not the LLM. Writes (adding a team member,
applying a set) are gated in code and need the user's click. Every answer stores a
plan trace (`make traces`), and a labelled eval set grades plans, retrieval recall,
answers, citations and abstention.

More: [overview](docs/architecture/overview.md) ·
[ask agent](docs/architecture/ask-agent.md) · [retrieval](docs/architecture/retrieval.md) ·
[team coach](docs/architecture/team-coach.md) · [damage calc](docs/architecture/damage-calc.md) ·
[decisions (ADRs)](docs/decisions/README.md)

## Tech stack

| Layer | Technology | Used for |
|---|---|---|
| Frontend | Next.js 16 · React 19 · TypeScript | App Router pages, typed API client, SSE streaming of plan steps and answers |
| UI | Tailwind CSS v4 · GSAP · Lenis | design tokens, stat-bar and artwork animation, smooth scroll (all respect reduced motion) |
| Backend | Python 3.12 · FastAPI · Pydantic | REST + SSE routes, typed tool arguments and responses |
| Database | PostgreSQL 17 · SQLAlchemy (async) · Alembic | all Pokémon data, teams, plan traces, migrations |
| Vectors | pgvector (HNSW) · Postgres full-text search | hybrid lore search and look-alikes |
| Embeddings | fastembed · `BAAI/bge-small-en-v1.5` | local 384-dim embeddings, no API calls |
| LLM (optional) | Anthropic Claude or Groq `gpt-oss-120b` | planning, narrated answers, set suggestions, team summaries |
| Data | PokéAPI CSV dataset | ingested offline; never called at runtime |
| Tooling | uv · npm · Docker Compose · ruff · ESLint · pytest · OpenSpec | env and deps, lint, tests, spec-driven feature work |

The damage formula exists in TypeScript (instant UI) and Python (the calc coach's
tools), kept in sync by shared reference fixtures.

## Development

```bash
make test
```

```bash
make lint
```

```bash
make eval
```

`make eval` grades plans, retrieval and answers against a labelled set (spends LLM
tokens if a key is set; `--keyless` mode doesn't) — [docs/guides/eval.md](docs/guides/eval.md).

Contributors and coding agents: start with [CLAUDE.md](CLAUDE.md). All docs:
[docs/](docs/index.md). Feature work goes through OpenSpec (`openspec/`).
