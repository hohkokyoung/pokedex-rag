"""Resolve names against the ingested data: Pokémon (and forms), moves, abilities, items, types.

Two entry points:
  * ``resolve(session, name)``   — one name a planner gave: exact (normalised) match
                                   across kinds, else the closest spelling.
  * ``find_in_text(session, q)`` — every name mentioned in free text, longest first,
                                   for the keyword planner. A name that is several
                                   things at once ("Psychic": a type *and* a move)
                                   comes back once per kind.

Names are normalised the same way as the learnset matcher (case, hyphens,
apostrophes, possessives), and the index is built once per process — the data
never changes at runtime.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ability, Move, Pokemon, PokemonForm, Type
from app.models.item import Item

KINDS = ("pokemon", "form", "move", "ability", "item", "type")
STANDARD_TYPES = (
    "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground",
    "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy",
)


@dataclass(frozen=True)
class Match:
    kind: str
    id: int
    name: str  # display name, e.g. "Charizard", "Will-O-Wisp", "Fire"
    exact: bool = True


# kind -> [(normalised key, id, display name)], longest key first
_index: dict[str, list[tuple[str, int, str]]] = {}


def norm(text: str) -> str:
    """Lowercase, drop possessives/punctuation, pad with spaces: "Mud-Slap?" → " mud slap "."""
    text = re.sub(r"['’]s\b", "", text.lower())
    text = text.replace("é", "e")
    return " " + " ".join(re.sub(r"[^\w]+", " ", text).split()) + " "


async def load(session: AsyncSession) -> None:
    if _index:
        return
    rows: dict[str, list[tuple[str, int]]] = {
        "pokemon": (await session.execute(select(Pokemon.name, Pokemon.id))).all(),
        "form": (await session.execute(select(PokemonForm.name, PokemonForm.id))).all(),
        "move": (await session.execute(select(Move.name, Move.id))).all(),
        "ability": (await session.execute(select(Ability.name, Ability.id))).all(),
        "item": (await session.execute(select(Item.name, Item.id))).all(),
        "type": [
            (n.title(), i)
            for n, i in (await session.execute(select(Type.identifier, Type.id))).all()
            if n in STANDARD_TYPES
        ],
    }
    for kind, pairs in rows.items():
        entries = [(norm(n), i, n) for n, i in pairs if norm(n).strip()]
        _index[kind] = sorted(entries, key=lambda e: -len(e[0]))


async def resolve(
    session: AsyncSession, name: str, kinds: tuple[str, ...] = KINDS, *, cutoff: float = 0.85
) -> list[Match]:
    """Exact matches across ``kinds``; failing that, the closest spelling (``exact=False``)."""
    await load(session)
    key = norm(name)
    if not key.strip():
        return []
    exact = [
        Match(kind, i, display)
        for kind in kinds
        for k, i, display in _index[kind]
        if k == key
    ]
    if exact:
        return exact

    # Compare without the padding spaces, which would inflate every ratio.
    bare = key.strip()
    best: list[tuple[float, Match]] = []
    for kind in kinds:
        keys = {k.strip(): (i, display) for k, i, display in _index[kind]}
        for k in difflib.get_close_matches(bare, keys, n=1, cutoff=cutoff):
            ratio = difflib.SequenceMatcher(None, bare, k).ratio()
            i, display = keys[k]
            best.append((ratio, Match(kind, i, display, exact=False)))
    if not best:
        return []
    top = max(r for r, _ in best)
    return [m for r, m in best if r == top]


async def resolve_one(session: AsyncSession, name: str, kind: str) -> Match | None:
    matches = await resolve(session, name, (kind,))
    return matches[0] if matches else None


async def find_in_text(
    session: AsyncSession, text: str, kinds: tuple[str, ...] = KINDS
) -> list[Match]:
    """Names mentioned in ``text``, in order of appearance; longest names claim their span.

    The same span may match several kinds (one Match each); a shorter name inside
    a longer one already claimed ("Mew" in "Mewtwo", "Fire" in "Fire Punch") is skipped.
    """
    await load(session)
    padded = norm(text)
    candidates = sorted(
        ((k, kind, i, display) for kind in kinds for k, i, display in _index[kind]),
        key=lambda c: -len(c[0]),
    )
    claimed: list[tuple[int, int, str]] = []  # (start, end, key)
    found: list[tuple[int, Match]] = []
    for key, kind, i, display in candidates:
        start = padded.find(key)
        while start != -1:
            end = start + len(key)
            clash = [c for c in claimed if c[0] < end and start < c[1]]
            if not clash or all(c[:2] == (start, end) and c[2] == key for c in clash):
                if not clash:
                    claimed.append((start, end, key))
                if not any(m.kind == kind and m.id == i for _, m in found):
                    found.append((start, Match(kind, i, display)))
            start = padded.find(key, start + 1)
    return [m for _, m in sorted(found, key=lambda f: f[0])]
