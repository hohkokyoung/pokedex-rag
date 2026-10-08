"""Learnset retrieval: which Pokémon learn a move, and which moves a Pokémon learns.

Answers three shapes straight from the ingested learnset (`pokemon_moves`), with
no LLM needed to find the data:

  - move named     "what pokemon learns earthquake"  → the move, how many learn
                   it by which method, and its best users
  - Pokémon named  "what moves can blaziken learn"   → its learnset, one chunk
                   per learn method (level-up, TM, tutor, egg)
  - both named     "can blaziken learn earthquake?"  → a yes/no from the data

Names are matched against the whole Pokémon and move lists (hyphens, apostrophes
and possessives normalised). The agent's ``learnset`` tool (``app/agent/ask_tools.py``)
calls ``plan_typed`` / ``retrieve_typed`` with typed arguments; only the keyword
planner reads question text here (``find_game_in_text``, the learn cues).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Move, Pokemon, PokemonMove, PokemonType, Type
from app.models.moves import PokemonMoveLearn, VersionGroup
from app.models.pokemon import PokemonEvolution
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
    method: str | None = None  # only this learn method ("level-up", "machine", "tutor", "egg")
    max_level: int | None = None  # learned by level-up at or below this level (implies level-up)


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


def _gnorm(text: str) -> str:
    """"Scarlet/Violet" / "scarlet-violet" / "Scarlet & Violet" → "scarlet violet"."""
    text = text.lower().replace("é", "e").replace("’", "'").replace("&", " ").replace(" and ", " ")
    return " ".join(re.sub(r"[^a-z0-9']+", " ", text).replace("'", "").split())


async def resolve_game(
    session: AsyncSession, game: str, *, remake: bool = False
) -> VersionGroup | None:
    """A version group by name, identifier, initials or common short name ("Scarlet / Violet",
    "scarlet-violet", "Scarlet/Violet", "sv", "SwSh", "BDSP"). With ``remake``, the newest
    remake whose name contains every word ("diamond pearl" → Brilliant Diamond / Shining
    Pearl), or None if there isn't one."""
    key = _gnorm(game).removeprefix("pokemon ")
    groups = (await session.execute(select(VersionGroup))).scalars().all()
    if remake:
        words = set(key.split())
        remakes = [vg for vg in groups if words
                   and words < set(_gnorm(vg.identifier).split())]
        return max(remakes, key=lambda g: (len(g.identifier.split("-")), g.sort_order),
                   default=None)
    for vg in groups:
        initials = "".join(w[0] for w in vg.identifier.split("-") if w)
        short = _SHORT_GAME.get(vg.identifier, "").lower()
        if key in {_gnorm(vg.name), _gnorm(vg.identifier), initials, short}:
            return vg
    # The start of a longer name ("let's go" → Let's Go, Pikachu / Eevee).
    for vg in groups:
        if len(key.split()) >= 2 and _gnorm(vg.name).startswith(key):
            return vg
    # A game named inside a group ("scarlet" → Scarlet / Violet). A bare name is the
    # original, not a remake that contains it ("diamond" → DP, not Brilliant Diamond):
    # fewest other words first, then newest.
    words = key.split()

    def contains(vg: VersionGroup) -> bool:
        ids = _gnorm(vg.identifier).split()
        return any(ids[i:i + len(words)] == words for i in range(len(ids)))

    hits = [vg for vg in groups if words and contains(vg)]
    return min(hits, key=lambda g: (len(g.identifier.split("-")), -g.sort_order), default=None)


# "in Scarlet/Violet", "available in SwSh", "from Pokémon Emerald" — the phrase after the cue.
_GAME_CUE = re.compile(r"\b(?:in|from|on)\s+(?:the\s+)?((?:pok[eé]mon\s+)?[\w'’/&-]+"
                       r"(?:\s*(?:/|&|and)\s*[\w'’-]+|\s+[\w'’-]+){0,3})", re.I)
# Single words that are also everyday words ("in the sun", "in red") only count with "Pokémon".
_COMMON = {"red", "blue", "yellow", "gold", "silver", "crystal", "black", "white", "x", "y",
           "sun", "moon", "sword", "shield", "scarlet", "violet"}
_FILLER = {"old", "original", "classic", "the", "of"}
_REMAKE = {"new", "remake", "remakes", "remade"}  # "new Diamond and Pearl" → BDSP
_GAME_WORDS = {"game", "games", "version", "versions", "remake", "remakes"}


def _game_phrases(question: str):
    """Per "in/from/on …" cue: (its words without filler, wants a remake, names a game,
    the phrase as written)."""
    for m in _GAME_CUE.finditer(question):
        words = m.group(1).split()
        while words and words[0].lower() in _FILLER:  # "in (the) old Diamond and Pearl"
            words = words[1:]
        lowered = [w.lower() for w in words]
        remake = any(w in _REMAKE for w in lowered)
        named = any(w in _GAME_WORDS for w in lowered)
        words = [w for w in words if w.lower() not in _REMAKE]
        while words and words[0].lower() in _FILLER:  # "the remake of Diamond"
            words = words[1:]
        yield words, remake, named or remake, m.group(1).strip()


async def find_game_in_text(session: AsyncSession, question: str) -> VersionGroup | None:
    """The game a question restricts to, if it names one after "in/from/on" — longest phrase
    first. A bare everyday word ("in the sun") only counts as a game after "Pokémon"."""
    for words, remake, _named, _raw in _game_phrases(question):
        for n in range(len(words), 0, -1):
            phrase = " ".join(words[:n])
            key = _gnorm(phrase)
            if key in _COMMON and not remake:  # needs "Pokémon …" or a pair ("Sun/Moon")
                continue
            vg = await resolve_game(session, phrase, remake=remake)
            if vg is not None:
                return vg
    return None


async def unresolved_game(session: AsyncSession, question: str) -> str | None:
    """A game the question clearly names ("in the gizmo game", "in the new …") that no
    version group matches — so a planner can say it couldn't apply it instead of dropping it."""
    if await find_game_in_text(session, question) is not None:
        return None
    return next((raw for _w, _r, named, raw in _game_phrases(question) if named), None)


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
    method: str | None = None,
    max_level: int | None = None,
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
        method="level-up" if max_level else method if method in METHOD_LABEL else None,
        max_level=max_level or None,
    )


def _learn_rows(version_group_id: int | None, method: str | None = None,
                max_level: int | None = None):
    """(pokemon_id, move_id, learn_method, level) — any game, or one game's learnset.

    A move learnable several ways in one game keeps the most direct method
    (level-up, then TM, tutor, egg), matching the any-game table's single row. With
    ``method``, only that method counts — read per game, since the any-game table keeps
    one method per move (a level-up learner that also takes the TM would be missed).
    ``max_level`` keeps level-up rows learned at or below it; an evolution move (level 0)
    counts at the level the Pokémon evolves (unknown for item/trade evolutions → excluded).
    """
    if max_level is not None:
        method = "level-up"
    if version_group_id is None and method is None:
        L = PokemonMove
        return select(
            L.pokemon_id.label("pokemon_id"), L.move_id.label("move_id"),
            L.learn_method.label("learn_method"), L.level.label("level"),
        ).subquery()
    L = PokemonMoveLearn
    rank = case(
        {m: i for i, m in enumerate(_METHOD_ORDER)}, value=L.learn_method, else_=literal(9)
    )
    stmt = select(
        L.pokemon_id.label("pokemon_id"), L.move_id.label("move_id"),
        L.learn_method.label("learn_method"), L.level.label("level"),
    )
    if version_group_id is not None:
        stmt = stmt.where(L.version_group_id == version_group_id)
    if method is not None:
        stmt = stmt.where(L.learn_method == method)
    if max_level is not None:
        evo = PokemonEvolution
        learned_at = case((L.level == 0, evo.min_level), else_=L.level)
        stmt = stmt.outerjoin(evo, evo.to_pokemon_id == L.pokemon_id).where(
            learned_at <= max_level
        )
    return (
        stmt.distinct(L.pokemon_id, L.move_id)
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


# Short game names for level histories ("Lv 1 in SwSh/BDSP").
_SHORT_GAME = {
    "red-blue": "RB", "yellow": "Yellow", "gold-silver": "GS", "crystal": "Crystal",
    "ruby-sapphire": "RS", "emerald": "Emerald", "firered-leafgreen": "FRLG",
    "diamond-pearl": "DP", "platinum": "Platinum", "heartgold-soulsilver": "HGSS",
    "black-white": "BW", "black-2-white-2": "B2W2", "x-y": "XY",
    "omega-ruby-alpha-sapphire": "ORAS", "sun-moon": "SM", "ultra-sun-ultra-moon": "USUM",
    "lets-go-pikachu-lets-go-eevee": "LGPE", "sword-shield": "SwSh",
    "brilliant-diamond-shining-pearl": "BDSP", "legends-arceus": "PLA", "scarlet-violet": "SV",
}


async def _histories(
    session: AsyncSession, pokemon_ids: list[int], move_ids: list[int]
) -> dict[tuple[int, int], list[tuple[int, str, int]]]:
    """(pokemon, move) → (level, game, release order) for every game it's learned by level-up."""
    if not pokemon_ids or not move_ids:
        return {}
    L = PokemonMoveLearn
    rows = (
        await session.execute(
            select(L.pokemon_id, L.move_id, L.level, VersionGroup.identifier,
                   VersionGroup.sort_order)
            .join(VersionGroup, VersionGroup.id == L.version_group_id)
            .where(L.move_id.in_(move_ids), L.pokemon_id.in_(pokemon_ids),
                   L.learn_method == "level-up", L.level > 0)
        )
    ).all()
    out: dict[tuple[int, int], list[tuple[int, str, int]]] = {}
    for pid, mid, level, game, order in rows:
        out.setdefault((pid, mid), []).append((level, game, order))
    return out


async def _level_history(
    session: AsyncSession, move_id: int, pokemon_ids: list[int]
) -> dict[int, list[tuple[int, str, int]]]:
    """Per Pokémon: the move's level-up history (see ``_histories``)."""
    return {pid: h for (pid, _m), h in (await _histories(session, pokemon_ids, [move_id])).items()}


def _newest_level(history: list[tuple[int, str, int]] | None) -> int | None:
    return max(history, key=lambda r: r[2])[0] if history else None


def _levels_by_game(history: list[tuple[int, str, int]] | None) -> str | None:
    """'Lv 1 in SwSh/BDSP; Lv 51–52 in other games', or None if one level fits every game."""
    how = _how_by_game(history)
    return how.removeprefix("by level-up (").removesuffix(")") if how else None


def _how_by_game(history: list[tuple[int, str, int]] | None) -> str | None:
    """'by level-up (Lv 1 in SwSh/BDSP; Lv 51–52 in other games)' when the level depends on
    the game — the any-game table keeps only the lowest level, which reads as "Lv 1"."""
    levels = sorted({lv for lv, _, _ in history or ()})
    if len(levels) <= 1:
        return None
    newest = max(history, key=lambda r: r[2])[0]
    games = [_SHORT_GAME.get(g, g) for lv, g, _ in sorted(history, key=lambda r: r[2])
             if lv == newest]
    others = [lv for lv in levels if lv != newest]
    span = f"Lv {others[0]}" if len(others) == 1 else f"Lv {others[0]}–{others[-1]}"
    return f"by level-up (Lv {newest} in {'/'.join(games)}; {span} in other games)"


def _by(method: str, max_level: int | None = None) -> str:
    """'by level-up' / 'by TM' / 'as an egg move' / 'by level-up by Lv 29'."""
    by = "as an egg move" if method == "egg" else f"by {METHOD_LABEL.get(method, method)}"
    return f"{by} by Lv {max_level}" if max_level else by


def _at_level(move_id: int, level: int | None, varies: dict[int, str]) -> str:
    if move_id in varies:  # "Lv 1 in SwSh/BDSP; Lv 51–52 in other games" → bracket the rest
        newest, _, rest = varies[move_id].partition("; ")
        return f" at {newest} ({rest})"
    return f" at Lv {level}" if level else ""


def _how(method: str | None, level: int | None, evo_level: int | None = None) -> str:
    if method == "level-up":
        if level == 0:  # an evolution move: learned the moment it evolves
            return f"on evolving (Lv {evo_level})" if evo_level else "on evolving"
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
    L = _learn_rows(p.version_group_id, p.method, p.max_level)

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
    only = f" {_by(p.method, p.max_level)}" if p.method else ""
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
        content=f"{who} can learn {move.name}{only}{_in_game(p)}"
        + (f": {breakdown}." if breakdown and not p.method else "."),
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
    history = (
        await _level_history(session, move.id, [pk.id for pk, m, _ in rows if m == "level-up"])
        if p.version_group_id is None else {}
    )
    hows = {
        pk.id: (_how_by_game(history.get(pk.id)) if m == "level-up" else None) or _how(m, lv)
        for pk, m, lv in rows
    }
    users = []
    for pokemon, _method, _level in rows:
        chunk = _row_to_chunk(pokemon)
        chunk.content += f" Learns {move.name} {hows[pokemon.id]}{_in_game(p)}."
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
            "game": p.game, "users": [(pk, m, lv) for pk, m, lv in rows], "hows": hows,
            "method": p.method, "max_level": p.max_level,
        },
    )


async def _learnset(session: AsyncSession, p: LearnsetPlan) -> LearnsetOutcome:
    """A Pokémon's moves, one chunk per learn method."""
    pokemon = await session.get(Pokemon, p.pokemon_id)
    L = _learn_rows(p.version_group_id, p.method, p.max_level)
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

    # Any game: the summary table keeps each move's lowest level across games ("Lv 1" from
    # SwSh for Swampert's Earthquake). Show the newest game's level, noting when it varies.
    lv_ids = [m.id for m, _t, me, _l in rows if me == "level-up"]
    history = (
        await _histories(session, [pokemon.id], lv_ids) if p.version_group_id is None else {}
    )
    varies: dict[int, str] = {}
    grouped: dict[str, list] = {}
    for move, mtype, method, level in rows:
        if method == "level-up" and (h := history.get((pokemon.id, move.id))):
            level = _newest_level(h)
            if note := _levels_by_game(h):
                varies[move.id] = note
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
            f"{_at_level(m.id, lv, varies) if method == 'level-up' else ''}"
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
        {"pokemon": pokemon, "game": p.game, "groups": groups, "has_profile": own is not None,
         "varies": varies},
    )


async def _evo_level(session: AsyncSession, pokemon_id: int) -> int | None:
    """The level this Pokémon evolves at (None for item/trade/friendship evolutions)."""
    return await session.scalar(
        select(PokemonEvolution.min_level).where(PokemonEvolution.to_pokemon_id == pokemon_id)
    )


async def _pair_how(session: AsyncSession, p: LearnsetPlan, max_level: int | None) -> str | None:
    """How this Pokémon learns this move ("by TM", "on evolving (Lv 48)"), or None."""
    L = _learn_rows(p.version_group_id, p.method, max_level)
    row = (
        await session.execute(
            select(L.c.learn_method, L.c.level).where(
                L.c.pokemon_id == p.pokemon_id, L.c.move_id == p.move_id
            )
        )
    ).first()
    if row is None:
        return None
    evo = await _evo_level(session, p.pokemon_id) if row[1] == 0 else None
    how = _how(row[0], row[1], evo)
    if row[0] == "level-up" and p.version_group_id is None:
        history = await _level_history(session, p.move_id, [p.pokemon_id])
        how = _how_by_game(history.get(p.pokemon_id)) or how
    return how


async def _pair(session: AsyncSession, p: LearnsetPlan) -> LearnsetOutcome:
    """Can this Pokémon learn this move? Yes (with how) or no, from the learnset."""
    pokemon = await session.get(Pokemon, p.pokemon_id)
    move, mtype, total = await _move_with_type(session, p.move_id, p.version_group_id)
    how = await _pair_how(session, p, p.max_level)
    # Capped and not learned by then: say when it does learn it, so "no" isn't the whole story.
    instead = (await _pair_how(session, p, None)) if how is None and p.max_level else None
    row = how is not None
    absent = False
    if not row and p.version_group_id is not None:  # not in that game at all?
        absent = not await session.scalar(
            select(PokemonMoveLearn.pokemon_id).where(
                PokemonMoveLearn.pokemon_id == p.pokemon_id,
                PokemonMoveLearn.version_group_id == p.version_group_id,
            ).limit(1)
        )
    if row:
        verdict = f"{pokemon.name} can learn {move.name} {how}{_in_game(p)}."
    elif absent:
        verdict = (f"{pokemon.name} can't learn {move.name}{_in_game(p)}: {pokemon.name} isn't "
                   f"in {p.game} at all.")
    elif p.method:
        verdict = (f"{pokemon.name} doesn't learn {move.name} {_by(p.method, p.max_level)}"
                   f"{_in_game(p)}" + (f"; it learns it {instead}." if instead else "."))
    else:
        verdict = (f"{pokemon.name} cannot learn {move.name}{_in_game(p)}: it is not in "
                   f"{pokemon.name}'s learnset.")
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
        f"NOTE: The user asked whether {pokemon.name} can learn {move.name}"
        f"{f' by Lv {p.max_level}' if p.max_level else ''}{_in_game(p)}. Answer "
        "yes or no first from the learnset check, and how it learns it if yes."
    )
    return LearnsetOutcome(
        "pair", chunks, note,
        {"pokemon": pokemon, "move": move, "move_type": mtype, "move_learners": total,
         "ok": row, "how": how or instead, "game": p.game, "method": p.method,
         "max_level": p.max_level, "absent": absent},
    )
