"""Read queries backing the team-builder pickers: legal moves, abilities, natures."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Ability,
    Item,
    Move,
    MoveMachine,
    Nature,
    Pokemon,
    PokemonAbility,
    PokemonForm,
    PokemonMove,
    PokemonMoveLearn,
    VersionGroup,
)
from app.models.pokemon import PokemonType
from app.schemas.builder import (
    AbilityHolderOut,
    GameLearnerOut,
    GameMoveOut,
    GameOut,
    ItemOut,
    LearnMethodOut,
    LearnsetMoveOut,
    MoveGameLearnersOut,
    MoveGameOut,
    MoveLearnerOut,
    MoveOut,
    NatureOut,
    PokemonGameMovesOut,
    PokemonGameOut,
    SignatureZOut,
    ZUserOut,
)
from app.schemas.pokemon import AbilityOut
from app.services.pokemon_query import sprite_url
from app.services.zmoves import SIGNATURE_Z

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
            target=pm.move.target,
            priority=pm.move.priority or 0,
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
            target=m.target,
            priority=m.priority or 0,
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


async def move_games(session: AsyncSession) -> list[MoveGameOut]:
    """Every game with learnset data (newest first) and the moves learnable in it.

    "In the game" means some Pokémon or form can learn it there, so moves nothing
    learns (Z-Moves, Max Moves) aren't listed — the client places those itself.
    """
    rows = (
        await session.execute(
            select(VersionGroup, func.array_agg(func.distinct(PokemonMoveLearn.move_id)))
            .join(PokemonMoveLearn, PokemonMoveLearn.version_group_id == VersionGroup.id)
            .group_by(VersionGroup.id)
            .order_by(VersionGroup.sort_order.desc())
        )
    ).all()
    return [
        MoveGameOut(
            id=vg.id,
            identifier=vg.identifier,
            name=vg.name,
            generation=vg.generation,
            move_ids=sorted(ids),
        )
        for vg, ids in rows
    ]


async def moves_by_game(
    session: AsyncSession, pokemon_id: int, version_group_id: int | None = None
) -> PokemonGameMovesOut:
    """A Pokémon's (or alternate form's) learnset in one game, with its TM labels.

    ``pokemon_id`` may be a species or a form id (> 10000). A form without its own
    per-game rows (Megas, Gigantamax) uses its base species'. ``version_group_id``
    None — or a game it isn't in — picks the newest game it has a learnset in.
    """
    pid = pokemon_id
    has_rows = select(PokemonMoveLearn.pokemon_id).where(PokemonMoveLearn.pokemon_id == pid)
    if (await session.execute(has_rows.limit(1))).first() is None:
        form = await session.get(PokemonForm, pid)
        if form is not None:
            pid = form.base_pokemon_id

    game_rows = (
        await session.execute(
            select(VersionGroup, func.count(func.distinct(PokemonMoveLearn.move_id)))
            .join(PokemonMoveLearn, PokemonMoveLearn.version_group_id == VersionGroup.id)
            .where(PokemonMoveLearn.pokemon_id == pid)
            .group_by(VersionGroup.id)
            .order_by(VersionGroup.sort_order.desc())
        )
    ).all()
    games = [
        PokemonGameOut(
            id=vg.id, identifier=vg.identifier, name=vg.name, generation=vg.generation, moves=n
        )
        for vg, n in game_rows
    ]
    if not games:
        return PokemonGameMovesOut(version_group_id=None, games=[], moves=[])
    vg_id = version_group_id if any(g.id == version_group_id for g in games) else games[0].id

    rows = (
        await session.execute(
            select(PokemonMoveLearn.learn_method, PokemonMoveLearn.level, Move, MoveMachine.label)
            .join(Move, Move.id == PokemonMoveLearn.move_id)
            .outerjoin(
                MoveMachine,
                (MoveMachine.move_id == PokemonMoveLearn.move_id)
                & (MoveMachine.version_group_id == PokemonMoveLearn.version_group_id),
            )
            .options(selectinload(Move.type))
            .where(PokemonMoveLearn.pokemon_id == pid, PokemonMoveLearn.version_group_id == vg_id)
        )
    ).all()
    moves = [
        GameMoveOut(
            move_id=m.id,
            identifier=m.identifier,
            name=m.name,
            type=m.type.identifier if m.type else None,
            damage_class=m.damage_class,
            power=m.power,
            pp=m.pp,
            accuracy=m.accuracy,
            short_effect=m.short_effect,
            target=m.target,
            priority=m.priority or 0,
            learn_method=method,
            level=level,
            machine=label if method == "machine" else None,
        )
        for method, level, m, label in rows
    ]
    moves.sort(key=lambda mv: (_METHOD_ORDER.get(mv.learn_method or "", 9), mv.level or 0, mv.name))
    return PokemonGameMovesOut(version_group_id=vg_id, games=games, moves=moves)


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
            short_effect=ability.short_effect,
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
    out = out[: max(1, limit)]
    for m in out:
        if m.identifier in SIGNATURE_Z:
            m.signature_z = await signature_z(session, m.identifier)
    return out


async def signature_z(session: AsyncSession, identifier: str) -> SignatureZOut | None:
    """Who can use a signature Z-Move (see ``app.services.zmoves``)."""
    z = SIGNATURE_Z.get(identifier)
    if z is None:
        return None
    base = (
        await session.execute(select(Move.name).where(Move.identifier == z.base_move))
    ).scalar_one_or_none()
    species = {
        p.id: p
        for p in (await session.execute(select(Pokemon).where(Pokemon.id.in_(z.users)))).scalars()
    }
    forms = {
        f.id: f
        for f in (
            await session.execute(select(PokemonForm).where(PokemonForm.id.in_(z.users)))
        ).scalars()
    }
    form_dex = {
        p.id: p.dex_number
        for p in (
            await session.execute(
                select(Pokemon).where(Pokemon.id.in_({f.base_pokemon_id for f in forms.values()}))
            )
        ).scalars()
    }
    users: list[ZUserOut] = []
    for uid in z.users:
        if uid in species:
            p = species[uid]
            users.append(
                ZUserOut(id=p.id, dex_number=p.dex_number, name=p.name, sprite_url=sprite_url(p))
            )
        elif uid in forms and forms[uid].base_pokemon_id in form_dex:
            f = forms[uid]
            users.append(
                ZUserOut(
                    id=f.id,
                    dex_number=form_dex[f.base_pokemon_id],
                    name=f.name,
                    sprite_url=f"/sprites/{f.sprite_path}" if f.sprite_path else "",
                    form_id=f.id,
                )
            )
    return SignatureZOut(crystal=z.crystal, base_move=base or z.base_move, users=users)


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
            short_effect=a.short_effect,
            is_hidden=False,
        )
        for a in rows
    ]


# Item categories a Pokémon can hold in battle (PokéAPI ``item_categories``); the rest are
# TMs, balls, ingredients, key items and the like.
HELD_CATEGORIES = (
    "Held items",
    "Choice",
    "Scarves",
    "Bad held items",
    "Type enhancement",
    "Type protection",
    "In a pinch",
    "Picky healing",
    "Medicine",
    "Plates",
    "Jewels",
    "Species-specific",
    "Mega Stones",
    "Z-Crystals",
    "Memories",
    "Effort training",
)


async def search_items(
    session: AsyncSession,
    q: str | None = None,
    limit: int = 8,
    held: bool = False,
) -> list[ItemOut]:
    """Global item lookup by name substring (named items first, alphabetical).

    ``held`` keeps only items a Pokémon can hold in battle (the team editor's item list)."""
    stmt = select(Item)
    if held:
        stmt = stmt.where(Item.category.in_(HELD_CATEGORIES))
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
    out = [
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
    # Moves only an alternate form learns (Freeze Shock, Shadow Bone, Blood Moon) have
    # no default-species row above; add those forms from the per-game learnset.
    have = {o.id for o in out}
    learners = select(PokemonMoveLearn.pokemon_id).where(PokemonMoveLearn.move_id == move_id)
    form_rows = (
        await session.execute(
            select(PokemonForm, Pokemon.dex_number)
            .join(Pokemon, Pokemon.id == PokemonForm.base_pokemon_id)
            .where(PokemonForm.id.in_(learners))
            .order_by(Pokemon.dex_number, PokemonForm.sort_order, PokemonForm.id)
        )
    ).all()
    for f, dex in form_rows:
        if f.base_pokemon_id in have or len(out) >= limit:
            continue
        have.add(f.base_pokemon_id)
        out.append(
            MoveLearnerOut(
                id=f.id,
                dex_number=dex,
                name=f.name,
                types=list(f.types or []),
                sprite_url=f"/sprites/{f.sprite_path}" if f.sprite_path else "",
                form_id=f.id,
            )
        )
    out.sort(key=lambda o: (o.dex_number, o.form_id or 0))
    return out


_METHOD_ORDER = {"level-up": 0, "machine": 1, "egg": 2, "tutor": 3}


async def move_learners_by_game(
    session: AsyncSession, move_id: int, version_group_id: int | None = None
) -> MoveGameLearnersOut:
    """Who learns a move and how (level, TM, egg, tutor) — in one game, or across
    every game when ``version_group_id`` is None (the default).

    "Any game" merges each Pokémon's rows so it appears once: one entry per method,
    with the lowest and highest level-up level seen. An alternate form that
    learns it exactly like its base species is folded into the base row (``also``)
    so cosmetic forms (Minior colours) don't flood the list.
    """
    # Distinct species per game: fold forms onto their base species id.
    species = func.coalesce(PokemonForm.base_pokemon_id, PokemonMoveLearn.pokemon_id)
    game_rows = (
        await session.execute(
            select(VersionGroup, func.count(func.distinct(species)))
            .join(PokemonMoveLearn, PokemonMoveLearn.version_group_id == VersionGroup.id)
            .outerjoin(PokemonForm, PokemonForm.id == PokemonMoveLearn.pokemon_id)
            .where(PokemonMoveLearn.move_id == move_id)
            .group_by(VersionGroup.id)
            .order_by(VersionGroup.sort_order.desc())
        )
    ).all()
    games = [
        GameOut(
            id=vg.id,
            identifier=vg.identifier,
            name=vg.name,
            generation=vg.generation,
            learners=n,
        )
        for vg, n in game_rows
    ]
    if not games:
        return MoveGameLearnersOut(
            move_id=move_id, version_group_id=None, games=[], total=0, learners=[]
        )
    # None (or an unknown game) = every game at once.
    vg_id = version_group_id if any(g.id == version_group_id for g in games) else None
    total = (
        await session.execute(
            select(func.count(func.distinct(species)))
            .select_from(PokemonMoveLearn)
            .outerjoin(PokemonForm, PokemonForm.id == PokemonMoveLearn.pokemon_id)
            .where(PokemonMoveLearn.move_id == move_id)
        )
    ).scalar_one()

    machines = (
        await session.execute(
            select(MoveMachine.label, VersionGroup.name, VersionGroup.id)
            .join(VersionGroup, VersionGroup.id == MoveMachine.version_group_id)
            .where(MoveMachine.move_id == move_id)
            .order_by(VersionGroup.sort_order.desc())
        )
    ).all()
    machine = next((label for label, _name, gid in machines if gid == vg_id), None)
    # "Not a TM here, was TMxx up to …" only makes sense for one game.
    last = None if machine or vg_id is None else next(iter(machines), None)

    stmt = select(
        PokemonMoveLearn.pokemon_id, PokemonMoveLearn.learn_method, PokemonMoveLearn.level
    ).where(PokemonMoveLearn.move_id == move_id)
    if vg_id is not None:
        stmt = stmt.where(PokemonMoveLearn.version_group_id == vg_id)
    # pokemon_id -> method -> (lowest level, highest level)
    merged: dict[int, dict[str, tuple[int | None, int | None]]] = {}
    for pid, method, level in (await session.execute(stmt)).all():
        lo, hi = merged.setdefault(pid, {}).get(method, (None, None))
        if level is not None:
            lo = level if lo is None else min(lo, level)
            hi = level if hi is None else max(hi, level)
        merged[pid][method] = (lo, hi)
    by_mon = {
        pid: sorted(
            ((m, lo, hi) for m, (lo, hi) in ms.items()),
            key=lambda x: (_METHOD_ORDER.get(x[0], 9), x[1] or 0),
        )
        for pid, ms in merged.items()
    }

    forms = {
        f.id: f
        for f in (
            await session.execute(select(PokemonForm).where(PokemonForm.id.in_(by_mon)))
        ).scalars()
    }
    base_ids = {pid for pid in by_mon if pid not in forms}
    base_ids |= {f.base_pokemon_id for f in forms.values()}
    bases = {
        p.id: p
        for p in (
            await session.execute(
                select(Pokemon)
                .where(Pokemon.id.in_(base_ids))
                .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
            )
        ).scalars()
    }

    rows: dict[int, GameLearnerOut] = {}
    for pid, ms in by_mon.items():
        if pid in forms:
            continue
        p = bases.get(pid)
        if p is None:
            continue
        rows[pid] = GameLearnerOut(
            id=p.id,
            dex_number=p.dex_number,
            name=p.name,
            types=[pt.type.identifier for pt in p.types],
            sprite_url=sprite_url(p),
            methods=[LearnMethodOut(method=m, level=lo, level_max=hi) for m, lo, hi in ms],
        )
    for fid, f in sorted(forms.items(), key=lambda kv: (kv[1].sort_order, kv[0])):
        base = bases.get(f.base_pokemon_id)
        if base is None:
            continue
        ms = by_mon[fid]
        if f.base_pokemon_id in rows and by_mon.get(f.base_pokemon_id) == ms:
            rows[f.base_pokemon_id].also.append(f.name)
            continue
        rows[fid] = GameLearnerOut(
            id=fid,
            dex_number=base.dex_number,
            name=f.name,
            types=list(f.types or []),
            sprite_url=f"/sprites/{f.sprite_path}" if f.sprite_path else sprite_url(base),
            form_id=fid,
            methods=[LearnMethodOut(method=m, level=lo, level_max=hi) for m, lo, hi in ms],
        )

    def order(r: GameLearnerOut) -> tuple:
        lv = next((m.level for m in r.methods if m.method == "level-up"), None)
        return (lv is None, lv or 0, r.dex_number, r.form_id or 0)

    return MoveGameLearnersOut(
        move_id=move_id,
        version_group_id=vg_id,
        games=games,
        total=total,
        machine=machine,
        last_machine=last[0] if last else None,
        last_machine_game=last[1] if last else None,
        learners=sorted(rows.values(), key=order),
    )


async def ability_holders(
    session: AsyncSession, ability_id: int, limit: int = 250
) -> list[AbilityHolderOut]:
    """Every species that has a given ability (reverse ability lookup)."""
    stmt = (
        select(Pokemon, PokemonAbility.is_hidden)
        .join(PokemonAbility, PokemonAbility.pokemon_id == Pokemon.id)
        .where(PokemonAbility.ability_id == ability_id)
        .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
        .order_by(Pokemon.dex_number)
        .limit(max(1, limit))
    )
    rows = (await session.execute(stmt)).all()
    return [
        AbilityHolderOut(
            id=p.id,
            dex_number=p.dex_number,
            name=p.name,
            types=[pt.type.identifier for pt in p.types],
            sprite_url=sprite_url(p),
            is_hidden=is_hidden,
        )
        for p, is_hidden in rows
    ]


async def all_natures(session: AsyncSession) -> list[NatureOut]:
    rows = (await session.execute(select(Nature).order_by(Nature.identifier))).scalars().all()
    return [NatureOut.model_validate(n, from_attributes=True) for n in rows]
