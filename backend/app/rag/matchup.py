"""Matchup retrieval: "a special attacker with coverage against Water and Dark".

Uses the type-effectiveness chart to find the types that counter each named
target type, then returns the strongest attackers that can learn a move of
those counter-types (ranked by Special Attack when it's mentioned, else base
stat total).

A question about MOVES ("what moves beat Fire?") gets the best moves of each
counter type instead of attackers.

Both halves are citable context: a `type_chart` chunk per target states the
matchup itself (so "what beats Fire?" is answerable from the chart alone), and
each attacker chunk names the coverage move it actually learns.
"""

from __future__ import annotations

import re

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Move, Pokemon, PokemonMove, PokemonType, Type
from app.rag.learnset import move_chunk
from app.rag.retrieval import RetrievedChunk
from app.rag.sql_retrieval import _row_to_chunk
from app.services import matchups as matchups_service
from app.services import nlfilters

_TYPES = {
    "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
    "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark",
    "steel", "fairy",
}
_MARKERS = ("against", "coverage", "counter", "super effective", "effective against",
            "strong against", "beats", "good against", "deal with", "hits")

_SPATK_WORDS = ("sp att", "sp. att", "special att", "sp atk", "sp. atk", "spatk", "special attack")


def is_matchup(question: str) -> bool:
    t = question.lower()
    return any(m in t for m in _MARKERS) and any(
        re.search(rf"\b{ty}\b", t) for ty in _TYPES
    )


def wants_moves(question: str) -> bool:
    """"what moves beat fire" asks for moves; "a pokemon with moves that beat fire" doesn't."""
    t = question.lower()
    if not re.search(r"\bmoves?\b", t) or "attacker" in t:
        return False
    return not re.search(r"\b(which|what|a|an|best|strongest)\s+pok[eé]mon\b", t)


def target_types(question: str) -> list[str]:
    t = question.lower()
    return [ty for ty in _TYPES if re.search(rf"\b{ty}\b", t)]


def _names(idents: list[str]) -> str:
    """["water", "ground", "rock"] -> "Water, Ground and Rock"."""
    words = [i.title() for i in sorted(idents)]
    return words[0] if len(words) == 1 else f"{', '.join(words[:-1])} and {words[-1]}"


async def type_chart_chunk(session: AsyncSession, target: str) -> RetrievedChunk | None:
    """The defensive chart for one type, as a citable chunk (no Pokémon attached)."""
    stmt = select(Type).where(Type.identifier == target)
    type_row = (await session.execute(stmt)).scalars().first()
    if type_row is None:
        return None
    b = await matchups_service.defensive_for(session, [type_row.id])
    parts = []
    if b.weak_2x:
        parts.append(f"takes super-effective (2x) damage from {_names(b.weak_2x)} moves")
    if b.resist_half:
        parts.append(f"resists (0.5x) {_names(b.resist_half)} moves")
    if b.immune:
        parts.append(f"is immune to {_names(b.immune)} moves")
    content = f"Type chart: a {target.title()}-type Pokémon {'; '.join(parts)}."
    return RetrievedChunk(
        id=-(1_000_000 + type_row.id),  # synthetic, distinct from sql_row ids (-pokemon.id)
        pokemon_id=None,
        pokemon_name=None,
        dex_number=None,
        chunk_type="type_chart",
        source_ref=f"{target} defence",
        content=content,
        score=1.0,
    )


async def _coverage_moves(
    session: AsyncSession,
    pokemon_ids: list[int],
    counter_types: list[str],
    move_classes: tuple[str, ...],
) -> dict[int, list[tuple[str, str, str, int | None]]]:
    """Per Pokémon: its strongest learnable move of each counter type.

    Returns {pokemon_id: [(move name, move type, damage class, power), ...]}.
    """
    rows = (
        await session.execute(
            select(
                PokemonMove.pokemon_id, Move.name, Type.identifier, Move.damage_class, Move.power
            )
            .join(Move, Move.id == PokemonMove.move_id)
            .join(Type, Type.id == Move.type_id)
            .where(
                PokemonMove.pokemon_id.in_(pokemon_ids),
                Type.identifier.in_(counter_types),
                Move.damage_class.in_(move_classes),
            )
            .order_by(Move.power.desc().nulls_last(), Move.name)
        )
    ).all()
    best: dict[int, dict[str, tuple[str, str, str, int | None]]] = {}
    for pid, name, mtype, dclass, power in rows:
        best.setdefault(pid, {}).setdefault(mtype, (name, mtype, dclass, power))
    return {pid: list(by_type.values()) for pid, by_type in best.items()}


# Moves learned by fewer Pokémon than this are signature/event moves: listed only
# after the widely available ones.
_COMMON_LEARNERS = 50


async def move_chunks(
    session: AsyncSession, counters: dict[str, list[str]], *, per_type: int = 4
) -> list[RetrievedChunk]:
    """The best damaging moves of each counter type, one citable chunk per move.

    Ranked by expected power (power x accuracy), widely learned moves first. Max
    and Z-moves have no learners and are skipped.
    """
    counter_types = sorted({c for cs in counters.values() for c in cs})
    hits = {c: [t for t, cs in counters.items() if c in cs] for c in counter_types}
    learners = func.count(PokemonMove.pokemon_id)
    rows = (
        await session.execute(
            select(Move, Type.identifier, learners)
            .join(Type, Type.id == Move.type_id)
            .join(PokemonMove, PokemonMove.move_id == Move.id)
            .where(
                Type.identifier.in_(counter_types),
                Move.damage_class.in_(("physical", "special")),
                Move.power.is_not(None),
            )
            .group_by(Move.id, Type.identifier)
            .order_by(
                (learners >= _COMMON_LEARNERS).desc(),
                (Move.power * func.coalesce(Move.accuracy, 100)).desc(),
                Move.name,
            )
        )
    ).all()

    picked: dict[str, list] = {t: [] for t in counter_types}
    for move, mtype, n in rows:
        if len(picked[mtype]) < per_type:
            picked[mtype].append((move, n))

    return [
        move_chunk(move, mtype, n, f" Super-effective vs {_names(hits[mtype])}.")
        for mtype in counter_types
        for move, n in picked[mtype]
    ]


async def coverage(
    session: AsyncSession, question: str, targets: list[str], *, k: int = 8
) -> tuple[list[RetrievedChunk], str]:
    """Text entry point: read the filters from the question, then ``coverage_typed``."""
    low = question.lower()
    special = any(w in low for w in _SPATK_WORDS)
    legendary, mythical = nlfilters.restricted_filters(question)
    return await coverage_typed(
        session,
        targets,
        attacker_class="special" if special else None,
        want="moves" if wants_moves(question) else "pokemon",
        legendary=legendary,
        mythical=mythical,
        off_type="coverage" in low,
        k=k,
    )


async def coverage_typed(
    session: AsyncSession,
    targets: list[str],
    *,
    attacker_class: str | None = None,
    want: str = "pokemon",
    legendary: bool | None = None,
    mythical: bool | None = None,
    off_type: bool = False,
    k: int = 8,
) -> tuple[list[RetrievedChunk], str]:
    """Attackers (or moves, ``want="moves"``) that hit the target types super-effectively.

    ``attacker_class`` ("physical"/"special") needs a coverage move of that class and
    ranks by the matching attack stat; otherwise any damaging move, ranked by BST.
    ``off_type`` ranks purely by stats; by default Pokémon that ARE a counter type
    (same-type bonus) come first.
    """
    targets = [t.lower() for t in targets if t.lower() in _TYPES]
    counters = await matchups_service.counters_for(session, targets)
    counter_types = sorted({c for lst in counters.values() for c in lst})
    if not counter_types:
        return [], ""

    lines = "; ".join(
        f"{t.title()} is countered by {', '.join(cs)}-type moves" for t, cs in counters.items()
    )
    charts = [c for t in counters if (c := await type_chart_chunk(session, t)) is not None]

    if want == "moves":
        note = (
            "NOTE: The user is asking about MOVES, not Pokémon. Per the type chart: "
            f"{lines}. The CONTEXT starts with the type chart for each target (cite it for which "
            "types beat the target), then the strongest widely learned damaging moves of each "
            "super-effective type. Answer which types beat the target first, then one bullet "
            "per move, grouped by type: \"**Move name** — Type, category, power; any drawback "
            "(recoil, charge turn, low accuracy) from its effect [n]\". Don't recommend Pokémon."
        )
        return [*charts, *await move_chunks(session, counters)], note

    sort_col = {"special": Pokemon.sp_attack, "physical": Pokemon.attack}.get(
        attacker_class or "", Pokemon.base_stat_total
    )
    # A special attacker needs a *special* coverage move; otherwise any damaging move.
    move_classes = (attacker_class,) if attacker_class in ("physical", "special") else (
        "physical", "special"
    )

    # Movepool-based coverage: the Pokémon can LEARN a damaging move whose type is
    # super-effective against a target (uses the ingested learnset, not just STAB typing).
    has_counter = (
        select(PokemonMove.pokemon_id)
        .join(Move, Move.id == PokemonMove.move_id)
        .join(Type, Type.id == Move.type_id)
        .where(
            and_(
                PokemonMove.pokemon_id == Pokemon.id,
                Type.identifier.in_(counter_types),
                Move.damage_class.in_(move_classes),
            )
        )
        .exists()
    )
    stmt = (
        select(Pokemon)
        .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
        .where(has_counter)
    )
    if legendary is not None:
        stmt = stmt.where(Pokemon.is_legendary.is_(legendary))
    if mythical is not None:
        stmt = stmt.where(Pokemon.is_mythical.is_(mythical))
    # A plain "what beats Fire?" is best answered by Pokémon that ARE a counter
    # type (STAB), so rank those first. An explicit coverage / attacker-class
    # question keeps the pure stat ranking, which surfaces off-type coverage.
    if not off_type and attacker_class is None:
        is_counter_type = (
            select(PokemonType.pokemon_id)
            .join(Type, Type.id == PokemonType.type_id)
            .where(PokemonType.pokemon_id == Pokemon.id, Type.identifier.in_(counter_types))
            .exists()
        )
        stmt = stmt.order_by(is_counter_type.desc())
    stmt = stmt.order_by(sort_col.desc()).limit(k)
    rows = (await session.execute(stmt)).scalars().all()

    # Name the move behind each attacker's coverage, so the claim is citable.
    moves = await _coverage_moves(session, [p.id for p in rows], counter_types, move_classes)
    hits = {c: [t for t, cs in counters.items() if c in cs] for c in counter_types}
    chunks = []
    for p in rows:
        chunk = _row_to_chunk(p)
        learned = moves.get(p.id, [])[:3]
        if learned:
            listed = "; ".join(
                f"{name} ({mtype.title()}, {dclass}{f', {power} power' if power else ''}) "
                f"— super-effective vs {_names(hits[mtype])}"
                for name, mtype, dclass, power in learned
            )
            chunk.content += f" Coverage moves it can learn: {listed}."
            chunk.meta = {**(chunk.meta or {}), "coverage": [
                {"move": name, "type": mtype} for name, mtype, _dc, _pw in learned
            ]}
        chunks.append(chunk)

    move_kind = attacker_class or "damaging"
    note = (
        "NOTE: This is a type-matchup question. Per the type chart: "
        f"{lines}. The CONTEXT starts with the type chart for each target (cite it for which "
        f"types beat the target), then strong attackers that can LEARN a {move_kind} move of a "
        "super-effective type (coverage judged by learnset, not just typing), each with the "
        "moves named. Answer which types beat the target first, then recommend attackers and "
        "the coverage move each would use; if none covers every target at once, say so plainly."
    )
    return [*charts, *chunks], note
