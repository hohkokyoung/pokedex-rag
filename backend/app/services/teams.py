"""Team CRUD, hydration, and relational validation (ability/nature/move legality)."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Ability,
    Item,
    Move,
    Nature,
    Pokemon,
    PokemonAbility,
    PokemonForm,
    PokemonMove,
    PokemonType,
    Team,
    TeamMember,
)
from app.models.team import MAX_SLOTS
from app.schemas.team import (
    SlotAbility,
    SlotItem,
    SlotMove,
    SlotNature,
    SlotUpdate,
    TeamCreate,
    TeamMemberOut,
    TeamOut,
    TeamSummary,
    TeamUpdate,
)
from app.services.pokemon_query import sprite_url
from app.services.stats import STAT_KEYS, final_stats


def _base_stats(p: Pokemon | PokemonForm) -> dict[str, int]:
    return {
        "hp": p.hp,
        "attack": p.attack,
        "defense": p.defense,
        "sp_attack": p.sp_attack,
        "sp_defense": p.sp_defense,
        "speed": p.speed,
    }


def _form_sprite(f: PokemonForm) -> str:
    return f"/sprites/{f.sprite_path}" if f.sprite_path else ""


async def _forms_for(session: AsyncSession, members: list[TeamMember]) -> dict[int, PokemonForm]:
    """The alternate forms members are set to, keyed by form id. A form that no longer
    exists or doesn't belong to the member's species is dropped (the slot reads as the
    species)."""
    rows = await _by_id(session, PokemonForm, {m.form_id for m in members if m.form_id})
    return {
        m.form_id: rows[m.form_id]
        for m in members
        if m.form_id in rows and rows[m.form_id].base_pokemon_id == m.pokemon_id
    }


async def _form_abilities(session: AsyncSession, form: PokemonForm) -> dict[int, bool]:
    """A form's abilities as {ability_id: is_hidden} (forms store them by identifier)."""
    hidden = {
        a["identifier"]: bool(a.get("is_hidden"))
        for a in form.abilities or []
        if a.get("identifier")
    }
    if not hidden:
        return {}
    rows = (
        await session.execute(
            select(Ability.id, Ability.identifier).where(Ability.identifier.in_(list(hidden)))
        )
    ).all()
    return {aid: hidden[ident] for aid, ident in rows}


async def _load_team(session: AsyncSession, team_id: int) -> Team | None:
    return (
        await session.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id == team_id)
        )
    ).scalars().first()


async def hydrate(session: AsyncSession, team: Team) -> TeamOut:
    """Expand a team's stored slots into fully-named, stat-computed members."""
    members = sorted(team.members, key=lambda m: m.slot)
    pokemon_ids = {m.pokemon_id for m in members}
    ability_ids = {m.ability_id for m in members if m.ability_id}
    nature_ids = {m.nature_id for m in members if m.nature_id}
    move_ids: set[int] = set()
    for m in members:
        move_ids.update(m.move_ids or [])

    pokemon_map: dict[int, Pokemon] = {}
    if pokemon_ids:
        rows = (
            await session.execute(
                select(Pokemon)
                .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
                .where(Pokemon.id.in_(pokemon_ids))
            )
        ).scalars().all()
        pokemon_map = {p.id: p for p in rows}

    form_map = await _forms_for(session, members)
    ability_map = await _by_id(session, Ability, ability_ids)
    nature_map = await _by_id(session, Nature, nature_ids)
    item_map = await _by_id(session, Item, {m.item_id for m in members if m.item_id})
    move_rows = (
        (
            await session.execute(
                select(Move).options(selectinload(Move.type)).where(Move.id.in_(move_ids))
            )
        ).scalars().all()
        if move_ids
        else []
    )
    move_map = {mv.id: mv for mv in move_rows}

    out_members: list[TeamMemberOut] = []
    for m in members:
        p = pokemon_map.get(m.pokemon_id)
        if p is None:
            continue
        # An alternate form brings its own typing, stats, abilities and artwork.
        form = form_map.get(m.form_id) if m.form_id else None
        base = _base_stats(form or p)
        nature = nature_map.get(m.nature_id)
        ivs = m.iv_spread or {}
        evs = m.ev_spread or {}
        computed = final_stats(
            base,
            ivs=ivs,
            evs=evs,
            increased_stat=nature.increased_stat if nature else None,
            decreased_stat=nature.decreased_stat if nature else None,
        )
        ability = ability_map.get(m.ability_id)
        item = item_map.get(m.item_id) if m.item_id else None
        if form is not None and form.abilities:
            is_hidden = (await _form_abilities(session, form)).get(m.ability_id, False)
        else:
            is_hidden = await _ability_is_hidden(session, m.pokemon_id, m.ability_id)
        out_members.append(
            TeamMemberOut(
                slot=m.slot,
                pokemon_id=p.id,
                form_id=form.id if form else None,
                dex_number=p.dex_number,
                name=form.name if form else p.name,
                types=list(form.types) if form else [pt.type.identifier for pt in p.types],
                sprite_url=(_form_sprite(form) if form else "") or sprite_url(p),
                base_stats=base,
                final_stats=computed,
                ability=(
                    SlotAbility(id=ability.id, name=ability.name, is_hidden=is_hidden)
                    if ability
                    else None
                ),
                nature=(
                    SlotNature(
                        id=nature.id,
                        name=nature.name,
                        increased_stat=nature.increased_stat,
                        decreased_stat=nature.decreased_stat,
                    )
                    if nature
                    else None
                ),
                item=(
                    SlotItem(
                        id=item.id,
                        name=item.name,
                        category=item.category,
                        short_effect=item.short_effect,
                    )
                    if item
                    else None
                ),
                ev_spread={k: evs.get(k, 0) for k in STAT_KEYS},
                iv_spread={k: ivs.get(k, 31) for k in STAT_KEYS},
                moves=[
                    SlotMove(
                        move_id=mid,
                        name=move_map[mid].name,
                        type=move_map[mid].type.identifier if move_map[mid].type else None,
                        damage_class=move_map[mid].damage_class,
                        power=move_map[mid].power,
                        accuracy=move_map[mid].accuracy,
                        priority=move_map[mid].priority or 0,
                    )
                    for mid in (m.move_ids or [])
                    if mid in move_map
                ],
            )
        )

    return TeamOut(
        id=team.id,
        name=team.name,
        kind=team.kind,
        notes=team.notes,
        members=out_members,
    )


async def _by_id(session: AsyncSession, model, ids: set[int]) -> dict[int, object]:
    if not ids:
        return {}
    rows = (await session.execute(select(model).where(model.id.in_(ids)))).scalars().all()
    return {r.id: r for r in rows}


async def _ability_is_hidden(
    session: AsyncSession, pokemon_id: int, ability_id: int | None
) -> bool:
    if ability_id is None:
        return False
    row = (
        await session.execute(
            select(PokemonAbility.is_hidden).where(
                PokemonAbility.pokemon_id == pokemon_id,
                PokemonAbility.ability_id == ability_id,
            )
        )
    ).scalar_one_or_none()
    return bool(row)


# --- list / create / read / update / delete ---


async def list_teams(session: AsyncSession, kind: str | None = None) -> list[TeamSummary]:
    stmt = select(Team).options(selectinload(Team.members)).order_by(Team.updated_at.desc())
    if kind:
        stmt = stmt.where(Team.kind == kind)
    teams = (await session.execute(stmt)).scalars().all()

    pokemon_ids = {m.pokemon_id for t in teams for m in t.members}
    sprite_by_id: dict[int, str] = {}
    if pokemon_ids:
        rows = (
            await session.execute(select(Pokemon).where(Pokemon.id.in_(pokemon_ids)))
        ).scalars().all()
        sprite_by_id = {p.id: sprite_url(p) for p in rows}
    form_map = await _forms_for(session, [m for t in teams for m in t.members])

    def _sprite(m: TeamMember) -> str:
        form = form_map.get(m.form_id) if m.form_id else None
        return (_form_sprite(form) if form else "") or sprite_by_id.get(m.pokemon_id, "")

    summaries = []
    for t in teams:
        ordered = sorted(t.members, key=lambda m: m.slot)
        summaries.append(
            TeamSummary(
                id=t.id,
                name=t.name,
                kind=t.kind,
                size=len(t.members),
                sprites=[_sprite(m) for m in ordered],
            )
        )
    return summaries


async def create_team(session: AsyncSession, payload: TeamCreate) -> TeamOut:
    team = Team(name=payload.name, kind=payload.kind, notes=payload.notes)
    session.add(team)
    await session.commit()
    await session.refresh(team, attribute_names=["members"])
    return await hydrate(session, team)


async def get_team(session: AsyncSession, team_id: int) -> TeamOut | None:
    team = await _load_team(session, team_id)
    return await hydrate(session, team) if team else None


async def update_team(
    session: AsyncSession, team_id: int, payload: TeamUpdate
) -> TeamOut | None:
    team = await _load_team(session, team_id)
    if team is None:
        return None
    if payload.name is not None:
        team.name = payload.name
    if payload.kind is not None:
        team.kind = payload.kind
    if payload.notes is not None:
        team.notes = payload.notes
    await session.commit()
    await session.refresh(team, attribute_names=["members"])
    return await hydrate(session, team)


async def delete_team(session: AsyncSession, team_id: int) -> bool:
    team = await session.get(Team, team_id)
    if team is None:
        return False
    await session.delete(team)
    await session.commit()
    return True


async def set_slot(
    session: AsyncSession, team_id: int, slot: int, payload: SlotUpdate
) -> TeamOut | None:
    if not (1 <= slot <= MAX_SLOTS):
        raise HTTPException(status_code=422, detail=f"slot must be 1..{MAX_SLOTS}")
    team = await _load_team(session, team_id)
    if team is None:
        return None

    await _validate_slot(session, payload)

    existing = next((m for m in team.members if m.slot == slot), None)
    if existing is None:
        existing = TeamMember(slot=slot, pokemon_id=payload.pokemon_id)
        team.members.append(existing)
    existing.pokemon_id = payload.pokemon_id
    existing.form_id = payload.form_id
    existing.ability_id = payload.ability_id
    existing.item_id = payload.item_id
    existing.nature_id = payload.nature_id
    existing.ev_spread = payload.ev_spread
    existing.iv_spread = payload.iv_spread
    existing.move_ids = payload.move_ids
    await session.commit()
    await session.refresh(team, attribute_names=["members"])
    return await hydrate(session, team)


async def clear_slot(session: AsyncSession, team_id: int, slot: int) -> TeamOut | None:
    team = await _load_team(session, team_id)
    if team is None:
        return None
    await session.execute(
        delete(TeamMember).where(TeamMember.team_id == team_id, TeamMember.slot == slot)
    )
    await session.commit()
    await session.refresh(team, attribute_names=["members"])
    return await hydrate(session, team)


async def _validate_slot(session: AsyncSession, payload: SlotUpdate) -> None:
    """Relational validation: species (and form) exist, ability/nature/moves are legal.

    A form is checked against its own abilities and learnset; when the dataset has no
    learnset for it (e.g. newer Megas) it falls back to the species', which Megas share."""
    if await session.get(Pokemon, payload.pokemon_id) is None:
        raise HTTPException(status_code=422, detail="Unknown pokemon_id")

    form: PokemonForm | None = None
    if payload.form_id is not None:
        form = await session.get(PokemonForm, payload.form_id)
        if form is None or form.base_pokemon_id != payload.pokemon_id:
            raise HTTPException(status_code=422, detail="Form does not belong to this Pokémon")

    if payload.ability_id is not None:
        if form is not None and form.abilities:
            legal = list(await _form_abilities(session, form))
        else:
            legal = (
                await session.execute(
                    select(PokemonAbility.ability_id).where(
                        PokemonAbility.pokemon_id == payload.pokemon_id
                    )
                )
            ).scalars().all()
        if payload.ability_id not in set(legal):
            raise HTTPException(
                status_code=422, detail="Ability is not available to this Pokémon"
            )

    if payload.nature_id is not None and await session.get(Nature, payload.nature_id) is None:
        raise HTTPException(status_code=422, detail="Unknown nature_id")

    if payload.item_id is not None and await session.get(Item, payload.item_id) is None:
        raise HTTPException(status_code=422, detail="Unknown item_id")

    if payload.move_ids:
        if form is not None and form.learnset:
            legal_moves = [int(e["move_id"]) for e in form.learnset]
        else:
            legal_moves = (
                await session.execute(
                    select(PokemonMove.move_id).where(
                        PokemonMove.pokemon_id == payload.pokemon_id
                    )
                )
            ).scalars().all()
        illegal = [mid for mid in payload.move_ids if mid not in set(legal_moves)]
        if illegal:
            raise HTTPException(
                status_code=422,
                detail=f"Moves not in this Pokémon's learnset: {illegal}",
            )


_EV_KEYS = {"hp": "hp", "atk": "attack", "def": "defense", "spa": "sp_attack", "spd": "sp_defense",
            "spe": "speed", "attack": "attack", "defense": "defense", "sp_attack": "sp_attack",
            "sp_defense": "sp_defense", "speed": "speed"}


async def resolve_build(
    session: AsyncSession,
    member: TeamMember,
    *,
    moves: list[str] | None = None,
    ability: str | None = None,
    nature: str | None = None,
    item: str | None = None,
    evs: dict[str, int] | None = None,
) -> SlotUpdate:
    """A named set (as the coach/engine suggests it) resolved onto ``member`` as a
    validated SlotUpdate. Fields left as None keep what the slot already has; an
    unknown name or an illegal ability/move raises HTTPException (422)."""

    async def named(model, name: str):
        """Case-insensitive exact name match."""
        q = select(model).where(model.name.ilike(name.strip()))
        return (await session.execute(q)).scalars().first()

    ability_id = member.ability_id
    if ability:
        row = await named(Ability, ability)
        if row is None:
            raise HTTPException(status_code=422, detail=f"Unknown ability: {ability}")
        ability_id = row.id
    nature_id = member.nature_id
    if nature:
        row = await named(Nature, nature)
        if row is None:
            raise HTTPException(status_code=422, detail=f"Unknown nature: {nature}")
        nature_id = row.id
    item_id = member.item_id
    if item:
        if item.strip().lower() in ("none", "no item"):
            item_id = None
        else:
            row = await named(Item, item)
            if row is None:
                raise HTTPException(status_code=422, detail=f"Unknown item: {item}")
            item_id = row.id
    move_ids = member.move_ids
    if moves:
        rows = (await session.execute(select(Move).where(Move.name.in_(moves)))).scalars().all()
        ids = {r.name.lower(): r.id for r in rows}
        missing = [mv for mv in moves if mv.lower() not in ids]
        if missing:
            raise HTTPException(status_code=422, detail=f"Unknown moves: {missing}")
        move_ids = [ids[mv.lower()] for mv in moves][:4]
    ev_spread = member.ev_spread
    if evs:
        ev_spread = {_EV_KEYS[k]: int(v) for k, v in evs.items() if k in _EV_KEYS and v} or None

    payload = SlotUpdate(
        pokemon_id=member.pokemon_id, form_id=member.form_id, ability_id=ability_id,
        nature_id=nature_id, item_id=item_id, ev_spread=ev_spread, iv_spread=member.iv_spread,
        move_ids=move_ids,
    )
    await _validate_slot(session, payload)
    return payload


async def member_row(session: AsyncSession, team_id: int, slot: int) -> TeamMember | None:
    team = await _load_team(session, team_id)
    return next((m for m in team.members if m.slot == slot), None) if team else None


async def apply_build(
    session: AsyncSession,
    team_id: int,
    slot: int,
    *,
    moves: list[str] | None = None,
    ability: str | None = None,
    nature: str | None = None,
    item: str | None = None,
    evs: dict[str, int] | None = None,
) -> TeamOut | None:
    """Apply a named set (as the coach/engine suggests it) to an existing slot."""
    team = await _load_team(session, team_id)
    if team is None:
        return None
    member = next((m for m in team.members if m.slot == slot), None)
    if member is None:
        raise HTTPException(status_code=404, detail="No Pokémon in that slot")
    payload = await resolve_build(
        session, member, moves=moves, ability=ability, nature=nature, item=item, evs=evs
    )
    return await set_slot(session, team_id, slot, payload)
