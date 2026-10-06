"""Deterministic answers for ``query_pokemon`` (SQL) results — no LLM.

Called by ``app/agent/render.py`` when a plan's steps are all closed-form.

The planner's ``StructuredQuery`` already says exactly what was asked (which
stat, which direction, which filters) and the rows come straight from the
``pokemon`` table, so the answer is rendered in code: every name, number, count
and ``[n]`` citation is taken from the data, and none of it can be hallucinated.

The shape matches the LLM answer prompt so the /ask console renders both the
same way: one opening sentence that answers the question, then
``- **Name** — value [n]`` bullets for the rest of the list.
"""

from __future__ import annotations

from app.rag.retrieval import RetrievedChunk
from app.rag.sql_retrieval import StructuredQuery

_LABEL = {
    "hp": "HP", "attack": "Attack", "defense": "Defense", "sp_attack": "Sp. Atk",
    "sp_defense": "Sp. Def", "speed": "Speed", "base_stat_total": "base stat total",
    "height_m": "height", "weight_kg": "weight", "capture_rate": "capture rate",
}
# Filter phrasing: "have Speed above 100", "have a height of at least 2 m".
_FILTER_NOUN = {
    **_LABEL,
    "base_stat_total": "a base stat total", "height_m": "a height",
    "weight_kg": "a weight", "capture_rate": "a capture rate",
}
_OP = {"gt": "above", "gte": "of at least", "lt": "below", "lte": "of at most", "eq": "of exactly"}
_SUPERLATIVE = {
    ("height_m", "desc"): "the tallest", ("height_m", "asc"): "the shortest",
    ("weight_kg", "desc"): "the heaviest", ("weight_kg", "asc"): "the lightest",
}


def _fmt(stat: str, value: float | None) -> str:
    if value is None:
        return "unknown"
    unit = {"height_m": " m", "weight_kg": " kg"}.get(stat, "")
    return f"{value:g}{unit}"


def _value(chunk: RetrievedChunk, stat: str) -> float | None:
    return (chunk.values or {}).get(stat)


def _superlative(stat: str, order: str) -> tuple[str, str]:
    """(verb, phrase): ("has", "the highest Attack") or ("is", "the tallest")."""
    if (stat, order) in _SUPERLATIVE:
        return "is", _SUPERLATIVE[(stat, order)]
    return "has", f"the {'highest' if order == 'desc' else 'lowest'} {_LABEL[stat]}"


def _scope(q: StructuredQuery) -> str | None:
    """"legendary Fire-type Pokémon from Generation 1", or None when unfiltered."""
    words: list[str] = []
    if q.legendary is True:
        words.append("legendary")
    elif q.legendary is False:
        words.append("non-legendary")
    if q.mythical is True:
        words.append("mythical")
    elif q.mythical is False and q.legendary is not False:
        words.append("non-mythical")
    if q.types_all:
        words.append("/".join(t.capitalize() for t in q.types_all) + "-type")
    gen = f" from Generation {q.generation}" if q.generation is not None else ""
    if q.game:
        gen += f" in {q.game}"
    if not words and not gen:
        return None
    return " ".join([*words, "Pokémon"]) + gen


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _name(chunk: RetrievedChunk) -> str:
    return f"**{chunk.pokemon_name}**"


def _bullets(rows: list[RetrievedChunk], start: int, fmt) -> str:
    return "\n".join(
        f"- {_name(c)} — {fmt(c)} [{i}]" for i, c in enumerate(rows[start:], start=start + 1)
    )


def _ranking(q: StructuredQuery, rows: list[RetrievedChunk]) -> str:
    stat = q.sort_by
    assert stat is not None
    scope = _scope(q)
    prefix = f"Among {scope}, " if scope else ""
    verb, phrase = _superlative(stat, q.order)
    # "the highest Attack of any Pokémon" but "the tallest Pokémon".
    suffix = "" if scope else (" Pokémon" if verb == "is" else " of any Pokémon")

    top = _value(rows[0], stat)
    lead = 1
    while lead < len(rows) and _value(rows[lead], stat) == top:
        lead += 1
    if lead == 1:
        opening = f"{prefix}{_name(rows[0])} {verb} {phrase}{suffix} at {_fmt(stat, top)} [1]."
    else:
        names = _join([f"{_name(c)} [{i}]" for i, c in enumerate(rows[:lead], start=1)])
        opening = f"{prefix}{names} are tied for {phrase}{suffix} at {_fmt(stat, top)}."

    rest = _bullets(rows, lead, lambda c: _fmt(stat, _value(c, stat)))
    return opening + (f"\n\n{rest}" if rest else "")


def _threshold(q: StructuredQuery, rows: list[RetrievedChunk], total: int) -> str:
    scope = _scope(q) or "Pokémon"
    condition = " and ".join(
        f"{_FILTER_NOUN[f.stat]} {_OP[f.op]} {_fmt(f.stat, f.value)}" for f in q.stat_filters
    )
    if not rows:
        return f"No {scope} have {condition}."

    shown = list(dict.fromkeys([*([q.sort_by] if q.sort_by else []),
                                *(f.stat for f in q.stat_filters)]))
    key = shown[0]
    if total == 1:
        return (
            f"Only 1 {scope} has {condition}: {_name(rows[0])} at "
            f"{_fmt(key, _value(rows[0], key))} [1]."
        )

    opening = f"{total} {scope} have {condition}"
    start = 0
    if q.sort_by:
        verb, phrase = _superlative(q.sort_by, q.order)
        opening += (
            f"; {_name(rows[0])} {verb} {phrase} among them at "
            f"{_fmt(q.sort_by, _value(rows[0], q.sort_by))} [1]"
        )
        start = 1
    parts = [opening + "."]

    def values(c: RetrievedChunk) -> str:
        return ", ".join(f"{_LABEL[s]} {_fmt(s, _value(c, s))}" for s in shown)

    if rows[start:]:
        parts.append(_bullets(rows, start, values))
    if total > len(rows):
        which = "top" if q.sort_by else "first"
        parts.append(f"Showing the {which} {len(rows)} of {total}.")
    return "\n\n".join(parts)


def _listing(q: StructuredQuery, rows: list[RetrievedChunk], total: int) -> str:
    scope = _scope(q) or "Pokémon"
    if not rows:
        return f"There are no {scope}."
    if total == 1:
        return f"There is only 1 {scope}: {_name(rows[0])} (#{rows[0].dex_number}) [1]."
    if total > len(rows):
        opening = (
            f"There are {total} {scope}. The first {len(rows)} by National Dex number:"
        )
    else:
        opening = f"There are {total} {scope}:"
    return opening + "\n\n" + _bullets(rows, 0, lambda c: f"#{c.dex_number}")


def render(q: StructuredQuery, rows: list[RetrievedChunk], total: int) -> str:
    """Answer a structured question from its plan, result rows and match count.

    ``rows`` are ``sql_retrieval.execute`` results (in order, so ``[n]`` lines up
    with the sources list); ``total`` is ``sql_retrieval.count`` for the same plan.
    """
    if q.stat_filters:
        return _threshold(q, rows, total)
    if q.sort_by and rows:
        return _ranking(q, rows)
    return _listing(q, rows, total)
