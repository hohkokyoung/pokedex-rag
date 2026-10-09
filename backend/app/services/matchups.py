"""Type-matchup computation from the ingested effectiveness chart.

Defensive matchups: combine a Pokémon's 1-2 types into weaknesses / resistances
/ immunities. Offensive counters: which attacking types are super-effective
against a given type. The chart is tiny and static, so it's loaded once and
cached per process.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Type, TypeEffectiveness

# The 18 battle types in display order: the type chart, the team rating's coverage and
# threat rows, and the Type Calculator all list types this way.
ATTACK_ORDER = [
    "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground",
    "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy",
]

_chart: dict[tuple[int, int], float] | None = None
_id2ident: dict[int, str] = {}
_ident2id: dict[str, int] = {}


async def _ensure_loaded(session: AsyncSession) -> None:
    global _chart
    if _chart is not None:
        return
    types = (await session.execute(select(Type))).scalars().all()
    _id2ident.update({t.id: t.identifier for t in types})
    _ident2id.update({t.identifier: t.id for t in types})
    rows = (await session.execute(select(TypeEffectiveness))).scalars().all()
    _chart = {(r.damage_type_id, r.target_type_id): r.factor for r in rows}


@dataclass
class DefenseBuckets:
    weak_4x: list[str] = field(default_factory=list)
    weak_2x: list[str] = field(default_factory=list)
    resist_half: list[str] = field(default_factory=list)
    resist_quarter: list[str] = field(default_factory=list)
    immune: list[str] = field(default_factory=list)


async def defensive_for(session: AsyncSession, defender_type_ids: list[int]) -> DefenseBuckets:
    """Bucket every attacking type by its multiplier against this typing."""
    await _ensure_loaded(session)
    assert _chart is not None
    buckets = DefenseBuckets()
    for atk_id, atk_ident in _id2ident.items():
        factor = 1.0
        hit = False
        for def_id in defender_type_ids:
            f = _chart.get((atk_id, def_id))
            if f is not None:
                factor *= f
                hit = True
        if not hit or factor == 1.0:
            continue
        if factor == 0:
            buckets.immune.append(atk_ident)
        elif factor >= 4:
            buckets.weak_4x.append(atk_ident)
        elif factor > 1:
            buckets.weak_2x.append(atk_ident)
        elif factor <= 0.25:
            buckets.resist_quarter.append(atk_ident)
        else:
            buckets.resist_half.append(atk_ident)
    return buckets


async def counters_for(session: AsyncSession, target_idents: list[str]) -> dict[str, list[str]]:
    """For each target type, the attacking types that are super-effective against it."""
    await _ensure_loaded(session)
    assert _chart is not None
    out: dict[str, list[str]] = {}
    for target in target_idents:
        tid = _ident2id.get(target)
        if tid is None:
            continue
        out[target] = [
            atk_ident
            for atk_id, atk_ident in _id2ident.items()
            if _chart.get((atk_id, tid), 1.0) > 1
        ]
    return out


async def defense_multipliers(
    session: AsyncSession, defender_type_ids: list[int]
) -> dict[str, float]:
    """Every attacking type's damage multiplier against this typing (incl. 1.0)."""
    await _ensure_loaded(session)
    assert _chart is not None
    out: dict[str, float] = {}
    for atk_id, atk_ident in _id2ident.items():
        factor = 1.0
        for def_id in defender_type_ids:
            f = _chart.get((atk_id, def_id))
            if f is not None:
                factor *= f
        out[atk_ident] = factor
    return out


async def offense_multipliers(
    session: AsyncSession, attack_idents: list[str]
) -> dict[str, float]:
    """For each defending type, the best multiplier these attacking types can land on it."""
    await _ensure_loaded(session)
    assert _chart is not None
    atk_ids = [_ident2id[a] for a in attack_idents if a in _ident2id]
    out: dict[str, float] = {}
    for def_id, def_ident in _id2ident.items():
        if not atk_ids:
            out[def_ident] = 1.0
            continue
        out[def_ident] = max(_chart.get((aid, def_id), 1.0) for aid in atk_ids)
    return out


async def type_chart(session: AsyncSession) -> dict[str, dict[str, float]]:
    """attacking type → defending type → multiplier, for the 18 battle types in
    ``ATTACK_ORDER`` (every pair, 1× included). Non-battle types are left out."""
    await _ensure_loaded(session)
    assert _chart is not None
    ids = [_ident2id[t] for t in ATTACK_ORDER]
    return {
        atk: {d: _chart.get((aid, did), 1.0) for d, did in zip(ATTACK_ORDER, ids, strict=True)}
        for atk, aid in zip(ATTACK_ORDER, ids, strict=True)
    }


async def all_type_idents(session: AsyncSession) -> list[str]:
    await _ensure_loaded(session)
    return list(_id2ident.values())


async def ids_for(session: AsyncSession, idents: list[str]) -> list[int]:
    """Resolve type identifiers (e.g. 'fire') to their numeric ids."""
    await _ensure_loaded(session)
    return [_ident2id[i] for i in idents if i in _ident2id]


def known_types() -> set[str]:
    return set(_ident2id.keys())
