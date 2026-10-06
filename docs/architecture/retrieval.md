# Retrieval

What the tools actually fetch, and from where. Code: `backend/app/rag/` (retrievers)
and `backend/app/agent/ask_tools.py` (the tools that call them).

The short version: **most questions are answered by exact database queries, not
vector search.** Vectors cover the fuzzy cases — lore, descriptions, look-alikes.
Everything comes back in one shape, `RetrievedChunk`, so answering and citations
work the same whichever retriever produced it.

## The common shape

```python
@dataclass
class RetrievedChunk:          # app/rag/retrieval.py
    id: int                    # chunk row id (negative for SQL rows: -pokemon_id)
    pokemon_id: int | None
    pokemon_name: str | None
    dex_number: int | None
    chunk_type: str            # profile | dex_entry | sql_row | move | type_chart | …
    source_ref: str | None     # where it came from: "similar", "target", a game, a move…
    content: str               # the text the answer LLM reads and cites
    score: float               # relevance; meaning depends on the retriever
    values: dict | None        # raw numbers (SQL rows) for code-rendered answers
    meta: dict | None          # extras for the UI (types, move facts); never shown to the LLM
```

Who reads what: the **LLM** sees only `content`, numbered `[n]`. The **UI** draws the
tool's `views` and lists chunks as sources. **Code-rendered answers** read `values` and
`data`, never `content`.

## Structured retrieval (most questions)

| Retriever | Example questions | How |
|---|---|---|
| `sql_retrieval.py` | "fastest non-legendary Fire types", "Speed above 100 in Gen 4" | A typed `StructuredQuery` (types, generation, legendary/mythical, stat filters, sort, limit ≤ 25, game) → a parameterised SQLAlchemy query. No raw SQL from users or the LLM. Rows come back as `sql_row` chunks with `values`, score 1.0. |
| `learnset.py` | "can Pikachu learn Surf in Scarlet?", "who learns Earthquake?", "Garchomp's moves" | Joins over learnsets, moves and version groups. Game-aware: level-up levels and availability come from the named game (or the newest). |
| `matchup.py` | "what is Fire weak to?", "special attackers that cover Dragon" | The ingested type chart; coverage is **movepool-based** — a Pokémon covers a type if it can *learn* a super-effective damaging move (special-only when asked for), not just by its own typing. |
| `personalize.py` | "recommend a Pokémon for me" | Your favourites and preferred types (single local profile). |

Name lookups go through `app/agent/names.py`: exact match first, then the closest
spelling by `difflib` ratio ≥ 0.85 ("garchmop" → Garchomp, but "pikachu" ↛ Pichu). A
fuzzy match is labelled in the step summary ("closest match for …").

## Text retrieval (lore and look-alikes)

### What's stored

`knowledge_chunks` (`app/models/knowledge.py`), built by `make chunks`
(`app/ingest/build_chunks.py`):

| `chunk_type` | Count | Content |
|---|---|---|
| `profile` | 1,025 | one per Pokémon, written from the DB: types, category, base stats, abilities, size, habitat, evolution |
| `dex_entry` | ~8,500 | each distinct English Pokédex flavour text |

Each row has an `embedding` (384 dims, `BAAI/bge-small-en-v1.5` via fastembed — runs
locally, no API) with an HNSW cosine index, and a `content_tsv` full-text column
(DB-managed; excluded from Alembic autogenerate).

### `semantic_search` → hybrid search (`hybrid.py`)

1. **Vector**: embed the query, nearest chunks by cosine distance (top 12). Finds
   matching *meaning* — "volcano" also finds "lives near magma".
2. **Full-text**: Postgres `ts_rank_cd` over the query words joined with OR (top 12).
   Finds exact words — names and rare terms vectors can miss.
3. **Reciprocal Rank Fusion**: each chunk scores `Σ 1/(60 + rank)` over the lists it
   appears in; top 6 are kept. Ranks, not raw scores, because the two scores aren't on
   the same scale. A chunk ranked well in both lists wins.

The keyword planner sends a question here when it asks about lore (*origin, habitat,
diet, personality…*), alongside a profile or ranking step, or as the last resort when
nothing in the question is recognised. The LLM planner uses it for lore and for
non-Pokémon questions (which the answer then declines).

### `similar_to` → profile neighbours (`similarity.py`)

No query text is embedded: it takes the target's stored **profile** vector and returns
the nearest other profiles, excluding the target's own evolution line. The target's
own profile is always included first in the evidence (not as a card) so the answer can
compare both sides.

## Why it's split this way

Vector search returns things that *sound* similar, which is the wrong tool for "top 5
by Speed" or "can X learn Y". Those have exact answers in tables, so they're SQL.
Vectors handle only what exists solely in prose. If you removed them you'd lose lore
search and look-alikes; nothing else would break.
