"""Read queries backing the team-builder pickers: legal moves, abilities, natures."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Ability, Item, Move, Nature, Pokemon, PokemonAbility, PokemonMove
from app.models.pokemon import PokemonType
from app.schemas.builder import ItemOut, LearnsetMoveOut, MoveLearnerOut, MoveOut, NatureOut
from app.schemas.pokemon import AbilityOut
from app.services.pokemon_query import sprite_url

# Present damaging moves before status, then strongest first, then alphabetical.
_DAMAGE_ORDER = {"physical": 0, "special": 0, "status": 1}


async def legal_moves(
    session: AsyncSession, pokemon_id: int, q: str | None = None
) -> list[LearnsetMoveOut]:
    """The species' legal learnset, optionally filtered by a name substring."""
    stmt = (
        select(PokemonMove)
        .options(selectinload(PokemonMove.move).selectinload(Move.type))
        .where(PokemonMove.pokemon_id == pokemon_id)
    )
    if q and q.strip():
        stmt = stmt.join(Move, Move.id == PokemonMove.move_id).where(
            Move.name.ilike(f"%{q.strip()}%")
        )
    rows = (await session.execute(stmt)).scalars().all()

    out = [
        LearnsetMoveOut(
            move_id=pm.move_id,
            identifier=pm.move.identifier,
            name=pm.move.name,
            type=pm.move.type.identifier if pm.move.type else None,
            damage_class=pm.move.damage_class,
            power=pm.move.power,
            pp=pm.move.pp,
            accuracy=pm.move.accuracy,
            short_effect=pm.move.short_effect,
            learn_method=pm.learn_method,
            level=pm.level,
        )
        for pm in rows
    ]
    out.sort(
        key=lambda m: (
            _DAMAGE_ORDER.get(m.damage_class or "status", 1),
            -(m.power or 0),
            m.name,
        )
    )
    return out


async def legal_moves_for_form(
    session: AsyncSession, form_id: int, q: str | None = None
) -> list[LearnsetMoveOut]:
    """Display-only: a specific alternate form's learnset (from PokemonForm.learnset).

    Isolated from `legal_moves` so team-builder behaviour (default-form only) is
    untouched."""
    from app.models import PokemonForm

    form = await session.get(PokemonForm, form_id)
    if form is None or not form.learnset:
        return []
    by_move = {int(e["move_id"]): e for e in form.learnset}
    stmt = select(Move).options(selectinload(Move.type)).where(Move.id.in_(list(by_move)))
    if q and q.strip():
        stmt = stmt.where(Move.name.ilike(f"%{q.strip()}%"))
    moves = (await session.execute(stmt)).scalars().all()
    out = [
        LearnsetMoveOut(
            move_id=m.id,
            identifier=m.identifier,
            name=m.name,
            type=m.type.identifier if m.type else None,
            damage_class=m.damage_class,
            power=m.power,
            pp=m.pp,
            accuracy=m.accuracy,
            short_effect=m.short_effect,
            learn_method=by_move[m.id].get("method"),
            level=by_move[m.id].get("level"),
        )
        for m in moves
    ]
    out.sort(
        key=lambda mv: (
            _DAMAGE_ORDER.get(mv.damage_class or "status", 1),
            -(mv.power or 0),
            mv.name,
        )
    )
    return out


async def species_abilities(session: AsyncSession, pokemon_id: int) -> list[AbilityOut]:
    """A species' abilities (regular + hidden)."""
    rows = (
        await session.execute(
            select(PokemonAbility, Ability)
            .join(Ability, Ability.id == PokemonAbility.ability_id)
            .where(PokemonAbility.pokemon_id == pokemon_id)
            .order_by(PokemonAbility.slot)
        )
    ).all()
    return [
        AbilityOut(
            id=ability.id,
            identifier=ability.identifier,
            name=ability.name,
            effect=ability.effect,
            is_hidden=pa.is_hidden,
        )
        for pa, ability in rows
    ]


async def search_moves(
    session: AsyncSession, q: str | None = None, limit: int = 8
) -> list[MoveOut]:
    """Global move lookup by name substring (damaging moves first, strongest first)."""
    stmt = select(Move).options(selectinload(Move.type))
    if q and q.strip():
        stmt = stmt.where(Move.name.ilike(f"%{q.strip()}%"))
    rows = (await session.execute(stmt)).scalars().all()
    out = [
        MoveOut(
            id=m.id,
            identifier=m.identifier,
            name=m.name,
            type=m.type.identifier if m.type else None,
            damage_class=m.damage_class,
            power=m.power,
            pp=m.pp,
            accuracy=m.accuracy,
            priority=m.priority,
            short_effect=m.short_effect,
        )
        for m in rows
    ]
    out.sort(
        key=lambda m: (
            _DAMAGE_ORDER.get(m.damage_class or "status", 1),
            -(m.power or 0),
            m.name,
        )
    )
    return out[: max(1, limit)]


async def search_abilities(
    session: AsyncSession, q: str | None = None, limit: int = 8
) -> list[AbilityOut]:
    """Global ability lookup by name substring."""
    stmt = select(Ability)
    if q and q.strip():
        stmt = stmt.where(Ability.name.ilike(f"%{q.strip()}%"))
    stmt = stmt.order_by(Ability.name).limit(max(1, limit))
    rows = (await session.execute(stmt)).scalars().all()
    return [
        AbilityOut(
            id=a.id,
            identifier=a.identifier,
            name=a.name,
            effect=a.effect,
            is_hidden=False,
        )
        for a in rows
    ]


async def search_items(
    session: AsyncSession, q: str | None = None, limit: int = 8
) -> list[ItemOut]:
    """Global item lookup by name substring (named items first, alphabetical)."""
    stmt = select(Item)
    if q and q.strip():
        stmt = stmt.where(Item.name.ilike(f"%{q.strip()}%"))
    stmt = stmt.order_by(Item.name).limit(max(1, limit))
    rows = (await session.execute(stmt)).scalars().all()
    return [ItemOut.model_validate(i, from_attributes=True) for i in rows]


async def move_learners(
    session: AsyncSession, move_id: int, limit: int = 120
) -> list[MoveLearnerOut]:
    """Every species that can legally learn a given move (reverse learnset)."""
    stmt = (
        select(Pokemon, PokemonMove.learn_method, PokemonMove.level)
        .join(PokemonMove, PokemonMove.pokemon_id == Pokemon.id)
        .where(PokemonMove.move_id == move_id)
        .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
        .order_by(Pokemon.dex_number)
        .limit(max(1, limit))
    )
    rows = (await session.execute(stmt)).all()
    return [
        MoveLearnerOut(
            id=p.id,
            dex_number=p.dex_number,
            name=p.name,
            types=[pt.type.identifier for pt in p.types],
            sprite_url=sprite_url(p),
            learn_method=learn_method,
            level=level,
        )
        for p, learn_method, level in rows
    ]


async def all_natures(session: AsyncSession) -> list[NatureOut]:
    rows = (await session.execute(select(Nature).order_by(Nature.identifier))).scalars().all()
    return [NatureOut.model_validate(n, from_attributes=True) for n in rows]
