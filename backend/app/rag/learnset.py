"""Learnset retrieval: which Pokémon learn a move, and which moves a Pokémon learns.

Answers three shapes straight from the ingested learnset (`pokemon_moves`), with
no LLM needed to find the data:

  - move named     "what pokemon learns earthquake"  → the move, how many learn
                   it by which method, and its best users
  - Pokémon named  "what moves can blaziken learn"   → its learnset, one chunk
                   per learn method (level-up, TM, tutor, egg)
  - both named     "can blaziken learn earthquake?"  → a yes/no from the data

Names are matched against the whole Pokémon and move lists (hyphens, apostrophes
and possessives normalised), so it runs before the LLM router, which doesn't know
this route.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Move, Pokemon, PokemonMove, PokemonType, Type
from app.models.moves import PokemonMoveLearn, VersionGroup
from app.rag.retrieval import RetrievedChunk
from app.rag.similarity import target_profile_chunk
from app.rag.sql_retrieval import _row_to_chunk
from app.services import nlfilters

_LEARN = re.compile(
    r"\b(learns?|learned|learnt|learning|learnsets?|movepools?|movesets?|can use|knows?)\b"
)
_MOVES = re.compile(r"\bmoves?\b")
# "moves" alone next to a Pokémon is a learnset question, unless it's a matchup one.
_MATCHUP = re.compile(r"\b(against|beats?|effective|weak|resists?|counters?|vs)\b")
_TYPES = (
    "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground",
    "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy",
)
_CLASSES = ("physical", "special", "status")

METHOD_LABEL = {"level-up": "level-up", "machine": "TM", "tutor": "tutor", "egg": "egg move"}
_METHOD_ORDER = ("level-up", "machine", "tutor", "egg")

_names: dict[str, list[tuple[str, int]]] = {}


def _norm(text: str) -> str:
    """Lowercase, drop possessives, punctuation → spaces: "Mud-Slap?" → " mud slap "."""
    text = re.sub(r"['’]s\b", "", text.lower())
    return " " + " ".join(re.sub(r"[^\w]+", " ", text).split()) + " "


async def _load_names(session: AsyncSession) -> None:
    if _names:
        return
    pokemon = (await session.execute(select(Pokemon.name, Pokemon.id))).all()
    moves = (await session.execute(select(Move.name, Move.id))).all()
    # Longest first, so "Hydro Pump" wins over a shorter name inside it.
    for key, rows in (("pokemon", pokemon), ("move", moves)):
        _names[key] = sorted(((_norm(n), i) for n, i in rows), key=lambda x: -len(x[0]))


def _find(kind: str, text: str) -> tuple[int, str] | None:
    """The longest name of this kind that appears in the normalised text."""
    for name, id_ in _names[kind]:
        if name in text:
            return id_, name
    return None


@dataclass
class LearnsetPlan:
    pokemon_id: int | None
    move_id: int | None
    types: list[str]  # extra type filter named in the question ("which fire pokemon …")
    damage_class: str | None  # "physical" / "special" / "status"
    legendary: bool | None = None  # learners: include only / exclude legendaries
    mythical: bool | None = None
    version_group_id: int | None = None  # one game's learnset; None = any game
    game: str | None = None  # that game's display name


@dataclass
class LearnsetOutcome:
    """Chunks + answer note, plus the structured data behind them (for views/renderers).

    ``kind`` is "pair" (can X learn Y), "learners" (who learns Y) or "learnset" (X's moves).
    """

    kind: str
    chunks: list[RetrievedChunk]
    note: str
    data: dict


class UnresolvedName(LookupError):
    def __init__(self, kind: str, name: str):
        super().__init__(f'unresolved {kind} "{name}"')
        self.kind, self.name = kind, name


async def plan(session: AsyncSession, question: str) -> LearnsetPlan | None:
    """Detect a learnset question; None when it isn't one."""
    await _load_names(session)
    text = _norm(question)
    move = _find("move", text)
    rest = text.replace(move[1], " ") if move else text
    mon = _find("pokemon", rest)
    if mon:
        rest = rest.replace(mon[1], " ")

    learn = bool(_LEARN.search(text))
    if move and not (learn or mon):
        return None  # a move name alone ("surf", "psychic") isn't a learnset question
    if not move and not (mon and (learn or (_MOVES.search(text) and not _MATCHUP.search(text)))):
        return None

    legendary, mythical = nlfilters.restricted_filters(question)
    return LearnsetPlan(
        pokemon_id=mon[0] if mon else None,
        move_id=move[0] if move else None,
        types=[t for t in _TYPES if f" {t} " in rest],
        damage_class=next((c for c in _CLASSES if f" {c} " in rest), None),
        legendary=legendary,
        mythical=mythical,
    )


def _exact(kind: str, name: str) -> int | None:
    key = _norm(name)
    return next((i for n, i in _names[kind] if n == key), None)


async def resolve_game(session: AsyncSession, game: str) -> VersionGroup | None:
    """A version group by name or identifier ("Scarlet / Violet", "scarlet-violet", "sv")."""
    key = game.strip().lower()
    groups = (await session.execute(select(VersionGroup))).scalars().all()
    for vg in groups:
        names = {vg.name.lower(), vg.identifier.lower(), vg.identifier.replace("-", " ")}
        initials = "".join(w[0] for w in vg.identifier.split("-") if w)
        if key in names or key == initials:
            return vg
    # A single game named inside a pair ("scarlet" → Scarlet / Violet), newest first.
    for vg in sorted(groups, key=lambda g: -g.sort_order):
        if key and (key in vg.identifier.split("-") or key in vg.name.lower().split()):
            return vg
    return None


async def plan_typed(
    session: AsyncSession,
    *,
    pokemon: str | None = None,
    move: str | None = None,
    game: str | None = None,
    types: list[str] | None = None,
    damage_class: str | None = None,
    legendary: bool | None = None,
    mythical: bool | None = None,
) -> LearnsetPlan:
    """A plan from explicit names and filters. Raises ``UnresolvedName`` for an unknown name.

    Names must match exactly after normalisation (case, hyphens, apostrophes);
    callers close-match beforehand when they want fuzziness.
    """
    await _load_names(session)
    pid = mid = None
    if pokemon:
        pid = _exact("pokemon", pokemon)
        if pid is None:
            raise UnresolvedName("pokemon", pokemon)
    if move:
        mid = _exact("move", move)
        if mid is None:
            raise UnresolvedName("move", move)
    if pid is None and mid is None:
        raise UnresolvedName("pokemon or move", "")
    vg = None
    if game:
        vg = await resolve_game(session, game)
        if vg is None:
            raise UnresolvedName("game", game)
    return LearnsetPlan(
        pokemon_id=pid,
        move_id=mid,
        types=[t.lower() for t in (types or []) if t.lower() in _TYPES],
        damage_class=damage_class if damage_class in _CLASSES else None,
        legendary=legendary,
        mythical=mythical,
        version_group_id=vg.id if vg else None,
        game=vg.name if vg else None,
    )


def _learn_rows(version_group_id: int | None):
    """(pokemon_id, move_id, learn_method, level) — any game, or one game's learnset.

    A move learnable several ways in one game keeps the most direct method
    (level-up, then TM, tutor, egg), matching the any-game table's single row.
    """
    if version_group_id is None:
        L = PokemonMove
        return select(
            L.pokemon_id.label("pokemon_id"), L.move_id.label("move_id"),
            L.learn_method.label("learn_method"), L.level.label("level"),
        ).subquery()
    L = PokemonMoveLearn
    rank = case(
        {m: i for i, m in enumerate(_METHOD_ORDER)}, value=L.learn_method, else_=literal(9)
    )
    return (
        select(
            L.pokemon_id.label("pokemon_id"), L.move_id.label("move_id"),
            L.learn_method.label("learn_method"), L.level.label("level"),
        )
        .where(L.version_group_id == version_group_id)
        .distinct(L.pokemon_id, L.move_id)
        .order_by(L.pokemon_id, L.move_id, rank, L.level)
        .subquery()
    )


def move_chunk(move: Move, move_type: str, learners: int, extra: str = "") -> RetrievedChunk:
    """A move's facts as a citable chunk (the /ask UI renders these as a move row)."""
    acc = f"{move.accuracy}% accuracy" if move.accuracy else "never misses"
    power = f"{move.power} power" if move.power else "no base power"
    effect = f" Effect: {move.short_effect}" if move.short_effect else ""
    return RetrievedChunk(
        id=-(2_000_000 + move.id),  # synthetic, distinct from Pokémon ids
        pokemon_id=None,
        pokemon_name=None,
        dex_number=None,
        chunk_type="move",
        source_ref=move.name,
        content=(
            f"{move.name} is a {move_type.title()}-type {move.damage_class} move: "
            f"{power}, {acc}, {move.pp} PP.{extra} Learned by {learners} Pokémon.{effect}"
        ),
        score=1.0,
        meta={"move": {
            "move_id": move.id, "name": move.name, "type": move_type,
            "damage_class": move.damage_class, "power": move.power, "accuracy": move.accuracy,
            "pp": move.pp, "learners": learners, "effect": move.short_effect,
        }},
    )


def _how(method: str | None, level: int | None) -> str:
    if method == "level-up":
        return f"by level-up at Lv {level}" if level else "by level-up"
    if method == "machine":
        return "by TM"
    if method == "egg":
        return "as an egg move"
    return f"by {method}" if method else "by an unknown method"


async def retrieve(
    session: AsyncSession, question: str, p: LearnsetPlan, *, k: int = 8
) -> tuple[list[RetrievedChunk], str]:
    """Text-path entry point (filters already parsed into ``p``)."""
    out = await retrieve_typed(session, p, k=k)
    return out.chunks, out.note


async def retrieve_typed(session: AsyncSession, p: LearnsetPlan, *, k: int = 8) -> LearnsetOutcome:
    if p.move_id is not None and p.pokemon_id is not None:
        return await _pair(session, p)
    if p.move_id is not None:
        return await _learners(session, p, k=k)
    return await _learnset(session, p)


def _in_game(p: LearnsetPlan) -> str:
    return f" in {p.game}" if p.game else ""


async def _move_with_type(
    session: AsyncSession, move_id: int, version_group_id: int | None = None
) -> tuple[Move, str, int]:
    move, mtype = (
        await session.execute(
            select(Move, Type.identifier)
            .join(Type, Type.id == Move.type_id)
            .where(Move.id == move_id)
        )
    ).one()
    L = _learn_rows(version_group_id)
    n = await session.scalar(
        select(func.count()).select_from(L).join(Pokemon, Pokemon.id == L.c.pokemon_id)
        .where(L.c.move_id == move_id)
    )
    return move, mtype, n or 0


async def _learners(session: AsyncSession, p: LearnsetPlan, *, k: int) -> LearnsetOutcome:
    """Who learns a move: the move, a by-method count, then its best users."""
    move, mtype, total = await _move_with_type(session, p.move_id, p.version_group_id)
    L = _learn_rows(p.version_group_id)

    base = (
        select(Pokemon, L.c.learn_method, L.c.level)
        .join(L, L.c.pokemon_id == Pokemon.id)
        .where(L.c.move_id == move.id)
    )
    scope = []
    if p.types:
        scope.append(f"{'/'.join(t.title() for t in p.types)}-type")
        typed = (
            select(PokemonType.pokemon_id)
            .join(Type, Type.id == PokemonType.type_id)
            .where(PokemonType.pokemon_id == Pokemon.id, Type.identifier.in_(p.types))
            .exists()
        )
        base = base.where(typed)
    if p.legendary is not None:
        base = base.where(Pokemon.is_legendary.is_(p.legendary))
        scope.append("legendary" if p.legendary else "non-legendary")
    if p.mythical is not None:
        base = base.where(Pokemon.is_mythical.is_(p.mythical))
        if p.legendary is None:
            scope.append("mythical" if p.mythical else "non-mythical")

    sq = base.subquery()
    counts = (
        await session.execute(select(sq.c.learn_method, func.count()).group_by(sq.c.learn_method))
    ).all()
    by_method = {m: n for m, n in counts}
    who = " ".join([str(sum(by_method.values())), *scope, "Pokémon"])
    breakdown = ", ".join(
        f"{by_method[m]} {'as egg moves' if m == 'egg' else 'by ' + METHOD_LABEL.get(m, m)}"
        for m in _METHOD_ORDER
        if by_method.get(m)
    )
    summary = RetrievedChunk(
        id=-(3_000_000 + move.id),
        pokemon_id=None,
        pokemon_name=None,
        dex_number=None,
        chunk_type="learners",
        source_ref=move.name,
        content=f"{who} can learn {move.name}{_in_game(p)}"
        + (f": {breakdown}." if breakdown else "."),
        score=1.0,
    )

    # Best users: the move's own type first (STAB), then the stat it scales with.
    stat = {"physical": Pokemon.attack, "special": Pokemon.sp_attack}.get(
        move.damage_class, Pokemon.base_stat_total
    )
    stab = (
        select(PokemonType.pokemon_id)
        .join(Type, Type.id == PokemonType.type_id)
        .where(PokemonType.pokemon_id == Pokemon.id, Type.identifier == mtype)
        .exists()
    )
    rows = (
        await session.execute(
            base.options(selectinload(Pokemon.types).selectinload(PokemonType.type))
            .order_by(stab.desc(), stat.desc(), Pokemon.id)
            .limit(k)
        )
    ).all()
    users = []
    for pokemon, method, level in rows:
        chunk = _row_to_chunk(pokemon)
        chunk.content += f" Learns {move.name} {_how(method, level)}{_in_game(p)}."
        users.append(chunk)

    stat_name = {"physical": "Attack", "special": "Special Attack"}.get(move.damage_class)
    note = (
        f"NOTE: The user asked which Pokémon learn {move.name}{_in_game(p)}. The CONTEXT has the "
        f"move, how many Pokémon learn it{' (' + ', '.join(scope) + ')' if scope else ''} and by "
        f"which method, then its strongest users: {mtype.title()}-types first (same-type bonus)"
        f"{', ranked by ' + stat_name if stat_name else ''}. Say how many learn it, then name "
        "the standout users and how each learns it. It's a sample, not the full list."
    )
    return LearnsetOutcome(
        "learners",
        [move_chunk(move, mtype, total), summary, *users],
        note,
        {
            "move": move, "move_type": mtype, "move_learners": total,
            "total": sum(by_method.values()), "by_method": by_method, "scope": scope,
            "game": p.game, "users": [(pk, m, lv) for pk, m, lv in rows],
        },
    )


async def _learnset(session: AsyncSession, p: LearnsetPlan) -> LearnsetOutcome:
    """A Pokémon's moves, one chunk per learn method."""
    pokemon = await session.get(Pokemon, p.pokemon_id)
    L = _learn_rows(p.version_group_id)
    stmt = (
        select(Move, Type.identifier, L.c.learn_method, L.c.level)
        .join(L, L.c.move_id == Move.id)
        .join(Type, Type.id == Move.type_id)
        .where(L.c.pokemon_id == pokemon.id)
    )
    if p.types:
        stmt = stmt.where(Type.identifier.in_(p.types))
    if p.damage_class:
        stmt = stmt.where(Move.damage_class == p.damage_class)
    rows = (await session.execute(stmt)).all()

    grouped: dict[str, list] = {}
    for move, mtype, method, level in rows:
        grouped.setdefault(method or "other", []).append((move, mtype, level))

    chunks: list[RetrievedChunk] = []
    own = await target_profile_chunk(session, pokemon)
    if own is not None:
        chunks.append(own)
    order = [m for m in _METHOD_ORDER if m in grouped]
    order += [m for m in grouped if m not in _METHOD_ORDER]
    groups = []
    for i, method in enumerate(order):
        moves = grouped[method]
        if method == "level-up":
            moves.sort(key=lambda r: (r[2] or 0, r[0].name))
        else:  # strongest damaging moves first, then status moves A–Z
            moves.sort(key=lambda r: (-(r[0].power or 0), r[0].name))
        listed = "; ".join(
            f"{m.name} ({t.title()}, {m.damage_class}"
            f"{f', {m.power} power' if m.power else ''})"
            f"{f' at Lv {lv}' if method == 'level-up' and lv else ''}"
            for m, t, lv in moves
        )
        label = METHOD_LABEL.get(method, method)
        groups.append((len(chunks), method, label, moves))
        chunks.append(
            RetrievedChunk(
                id=-(4_000_000 + pokemon.id * 10 + i),
                pokemon_id=pokemon.id,
                pokemon_name=pokemon.name,
                dex_number=pokemon.dex_number,
                chunk_type="learnset",
                source_ref=label,
                content=f"{pokemon.name} learns {len(moves)} moves by {label}{_in_game(p)}: "
                f"{listed}.",
                score=1.0,
            )
        )

    scope = " ".join(filter(None, [" / ".join(t.title() for t in p.types), p.damage_class]))
    total = sum(len(v) for v in grouped.values())
    note = (
        f"NOTE: The user asked about {pokemon.name}'s moves{_in_game(p)}"
        f"{f' ({scope} only)' if scope else ''}. The CONTEXT has {pokemon.name}'s profile, then "
        f"its learnset ({total} moves) grouped by how it learns them. Open with how many moves it "
        "learns, then highlight the notable ones per method (strongest attacks, key level-up "
        "moves with their level). Don't list every move; the full list is shown to the user."
        if total
        else f"NOTE: {pokemon.name} learns no {scope} moves{_in_game(p)} in the Pokédex data; "
        "say so plainly."
    )
    return LearnsetOutcome(
        "learnset", chunks, note,
        {"pokemon": pokemon, "game": p.game, "groups": groups, "has_profile": own is not None},
    )


async def _pair(session: AsyncSession, p: LearnsetPlan) -> LearnsetOutcome:
    """Can this Pokémon learn this move? Yes (with how) or no, from the learnset."""
    pokemon = await session.get(Pokemon, p.pokemon_id)
    move, mtype, total = await _move_with_type(session, p.move_id, p.version_group_id)
    L = _learn_rows(p.version_group_id)
    row = (
        await session.execute(
            select(L.c.learn_method, L.c.level).where(
                L.c.pokemon_id == p.pokemon_id, L.c.move_id == p.move_id
            )
        )
    ).first()
    how = _how(row[0], row[1]) if row else None
    verdict = (
        f"{pokemon.name} can learn {move.name} {how}{_in_game(p)}."
        if row
        else f"{pokemon.name} cannot learn {move.name}{_in_game(p)}: it is not in "
        f"{pokemon.name}'s learnset."
    )
    fact = RetrievedChunk(
        id=-(5_000_000 + p.pokemon_id),
        pokemon_id=pokemon.id,
        pokemon_name=pokemon.name,
        dex_number=pokemon.dex_number,
        chunk_type="learnset",
        source_ref="learnset check",
        content=verdict,
        score=1.0,
    )
    chunks = [fact, move_chunk(move, mtype, total)]
    own = await target_profile_chunk(session, pokemon)
    if own is not None:
        chunks.append(own)
    note = (
        f"NOTE: The user asked whether {pokemon.name} can learn {move.name}{_in_game(p)}. Answer "
        "yes or no first from the learnset check, and how it learns it if yes."
    )
    return LearnsetOutcome(
        "pair", chunks, note,
        {"pokemon": pokemon, "move": move, "move_type": mtype, "move_learners": total,
         "ok": row is not None, "how": how, "game": p.game},
    )
