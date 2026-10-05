"""Structured (SQL) retrieval for the RAG pipeline.

Answers structured questions — rankings, thresholds, type/generation filters,
comparisons — by building a *safe, parameterised* query over the relational
``pokemon`` table (never raw SQL from user/LLM input). Results are returned as
``RetrievedChunk`` objects so they flow through the same context/citation path
as semantic hits.

Two entry points:
  * ``execute(session, query)`` — run a validated ``StructuredQuery``.
  * ``plan(question)``          — heuristic NL → ``StructuredQuery`` for the
                                  canonical structured phrasings (works with no
                                  LLM); the Phase 6 router can layer an
                                  LLM planner on top.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Pokemon, PokemonType, Type
from app.rag.retrieval import RetrievedChunk
from app.services import nlfilters

# Sortable / filterable numeric attributes -> ORM columns.
NUMERIC_COLUMNS = {
    "hp": Pokemon.hp,
    "attack": Pokemon.attack,
    "defense": Pokemon.defense,
    "sp_attack": Pokemon.sp_attack,
    "sp_defense": Pokemon.sp_defense,
    "speed": Pokemon.speed,
    "base_stat_total": Pokemon.base_stat_total,
    "height_m": Pokemon.height_m,
    "weight_kg": Pokemon.weight_kg,
    "capture_rate": Pokemon.capture_rate,
}

_OPS = {"gt": ">", "gte": "≥", "lt": "<", "lte": "≤", "eq": "="}

StatName = Literal[
    "hp", "attack", "defense", "sp_attack", "sp_defense", "speed",
    "base_stat_total", "height_m", "weight_kg", "capture_rate",
]


class StatFilter(BaseModel):
    stat: StatName
    op: Literal["gt", "gte", "lt", "lte", "eq"]
    value: float


class StructuredQuery(BaseModel):
    types_all: list[str] = Field(default_factory=list)  # must have ALL of these
    generation: int | None = None
    legendary: bool | None = None
    mythical: bool | None = None
    stat_filters: list[StatFilter] = Field(default_factory=list)
    sort_by: StatName | None = None
    order: Literal["asc", "desc"] = "desc"
    limit: int = 5

    def is_empty(self) -> bool:
        return not (
            self.types_all
            or self.generation
            or self.legendary is not None
            or self.mythical is not None
            or self.stat_filters
            or self.sort_by
        )


def _column(name: str):
    return NUMERIC_COLUMNS[name]


def _apply_filters(stmt, query: StructuredQuery):
    for t in query.types_all:
        exists = (
            select(PokemonType.pokemon_id)
            .join(Type, Type.id == PokemonType.type_id)
            .where(and_(PokemonType.pokemon_id == Pokemon.id, Type.identifier == t))
            .exists()
        )
        stmt = stmt.where(exists)

    if query.generation is not None:
        stmt = stmt.where(Pokemon.generation_id == query.generation)
    if query.legendary is not None:
        stmt = stmt.where(Pokemon.is_legendary.is_(query.legendary))
    if query.mythical is not None:
        stmt = stmt.where(Pokemon.is_mythical.is_(query.mythical))

    for f in query.stat_filters:
        col = _column(f.stat)
        if f.op == "gt":
            stmt = stmt.where(col > f.value)
        elif f.op == "gte":
            stmt = stmt.where(col >= f.value)
        elif f.op == "lt":
            stmt = stmt.where(col < f.value)
        elif f.op == "lte":
            stmt = stmt.where(col <= f.value)
        elif f.op == "eq":
            stmt = stmt.where(col == f.value)
    return stmt


async def execute(session: AsyncSession, query: StructuredQuery) -> list[RetrievedChunk]:
    stmt = select(Pokemon).options(selectinload(Pokemon.types).selectinload(PokemonType.type))
    stmt = _apply_filters(stmt, query)

    if query.sort_by:
        col = _column(query.sort_by)
        stmt = stmt.order_by((col.desc() if query.order == "desc" else col.asc()).nulls_last())
    stmt = stmt.order_by(Pokemon.dex_number)

    stmt = stmt.limit(max(1, min(query.limit, 25)))
    rows = (await session.execute(stmt)).scalars().all()
    return [_row_to_chunk(p) for p in rows]


async def count(session: AsyncSession, query: StructuredQuery) -> int:
    """How many Pokémon match the query's filters, ignoring its limit."""
    matching = _apply_filters(select(Pokemon.id), query).subquery()
    return (await session.execute(select(func.count()).select_from(matching))).scalar_one()


def _row_to_chunk(p: Pokemon) -> RetrievedChunk:
    types = "/".join(pt.type.identifier for pt in p.types) or "unknown"
    content = (
        f"{p.name} (#{p.dex_number}, {types}-type): HP {p.hp}, Attack {p.attack}, "
        f"Defense {p.defense}, Sp. Atk {p.sp_attack}, Sp. Def {p.sp_defense}, "
        f"Speed {p.speed}, base stat total {p.base_stat_total}."
    )
    # Height/weight/capture rate too, so a ranking on them cites a row that states it.
    extras = []
    if p.height_m is not None:
        extras.append(f"Height {p.height_m:g} m")
    if p.weight_kg is not None:
        extras.append(f"weight {p.weight_kg:g} kg")
    if p.capture_rate is not None:
        extras.append(f"capture rate {p.capture_rate}")
    if extras:
        content += " " + ", ".join(extras) + "."
    return RetrievedChunk(
        id=-p.id,
        pokemon_id=p.id,
        pokemon_name=p.name,
        dex_number=p.dex_number,
        chunk_type="sql_row",
        source_ref="structured query",
        content=content,
        score=1.0,
        values={name: getattr(p, name) for name in NUMERIC_COLUMNS},
        meta={"types": [pt.type.identifier for pt in p.types]},
    )


# --------------------------------------------------------------------------
# Heuristic NL → StructuredQuery (no LLM required)
# --------------------------------------------------------------------------

_TYPES = {
    "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
    "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark",
    "steel", "fairy",
}

_STAT_WORDS = {
    "hp": "hp", "health": "hp",
    "attack": "attack", "atk": "attack",
    "defense": "defense", "defence": "defense", "def": "defense",
    "special attack": "sp_attack", "sp attack": "sp_attack", "sp. atk": "sp_attack",
    "special defense": "sp_defense", "sp defense": "sp_defense", "sp. def": "sp_defense",
    "speed": "speed", "spe": "speed", "fastest": "speed", "slowest": "speed",
    "quickest": "speed",
    "base stat total": "base_stat_total", "stat total": "base_stat_total",
    "bst": "base_stat_total", "total stats": "base_stat_total", "strongest": "base_stat_total",
    "height": "height_m", "tallest": "height_m",
    "weight": "weight_kg", "heaviest": "weight_kg",
}

_HIGH_WORDS = (
    "highest", "most", "top", "best", "strongest", "greatest", "maximum",
    "max", "tallest", "heaviest", "largest", "biggest", "fastest", "quickest",
)
_LOW_WORDS = (
    "lowest", "least", "weakest", "smallest", "minimum", "min", "shortest", "lightest",
    "slowest",
)

_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9}


def _find_stat(text: str) -> str | None:
    # longest phrase first to catch "special attack" before "attack"
    for phrase in sorted(_STAT_WORDS, key=len, reverse=True):
        if phrase in text:
            return _STAT_WORDS[phrase]
    return None


def plan(question: str) -> StructuredQuery | None:
    """Best-effort structured plan for common phrasings; None if it doesn't look structured."""
    text = question.lower()
    q = StructuredQuery()

    # types
    for t in _TYPES:
        if re.search(rf"\b{t}[- ]?type\b", text) or re.search(rf"\b{t}\b", text):
            if t in _TYPES:
                q.types_all.append(t)
    # de-dup, cap at 2
    q.types_all = list(dict.fromkeys(q.types_all))[:2]

    q.legendary, q.mythical = nlfilters.restricted_filters(text)

    m = re.search(r"gen(?:eration)?\s*([1-9]|i{1,3}|iv|v|vi{0,3}|ix)\b", text)
    if m:
        tok = m.group(1)
        q.generation = int(tok) if tok.isdigit() else _ROMAN.get(tok)

    # stat threshold comparisons, e.g. "speed above 100", "attack greater than 120"
    for m in re.finditer(
        r"(hp|health|attack|atk|defense|defence|def|special attack|sp attack|"
        r"special defense|sp defense|speed|spe|base stat total|bst|weight|height)\s*"
        r"(?:that is |which is )?"
        r"(above|over|greater than|more than|at least|below|under|less than|at most|>=|<=|>|<|=)?"
        r"\s*(\d+(?:\.\d+)?)",
        text,
    ):
        stat = _STAT_WORDS.get(m.group(1))
        if not stat:
            continue
        word = (m.group(2) or "gt").strip()
        op = {
            "above": "gt", "over": "gt", "greater than": "gt", "more than": "gt", ">": "gt",
            "at least": "gte", ">=": "gte",
            "below": "lt", "under": "lt", "less than": "lt", "<": "lt",
            "at most": "lte", "<=": "lte",
            "=": "eq",
        }.get(word, "gt")
        q.stat_filters.append(StatFilter(stat=stat, op=op, value=float(m.group(3))))

    # ranking / superlative
    has_high = any(w in text for w in _HIGH_WORDS)
    has_low = any(w in text for w in _LOW_WORDS)
    stat = _find_stat(text)
    if has_high or has_low:
        q.sort_by = stat or "base_stat_total"
        q.order = "asc" if has_low and not has_high else "desc"
        if re.search(r"\btop\s+(\d+)", text):
            q.limit = min(int(re.search(r"\btop\s+(\d+)", text).group(1)), 25)
        elif re.search(
            r"\b(highest|strongest|lowest|weakest|tallest|heaviest|fastest|slowest)\b", text
        ):
            q.limit = 5

    # If there are filters but no explicit ranking, still sort by BST for a useful set.
    if q.stat_filters and not q.sort_by:
        q.sort_by = q.stat_filters[0].stat
        q.order = "desc"
        q.limit = 10

    return None if q.is_empty() else q
