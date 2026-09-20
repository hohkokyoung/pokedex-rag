"""Read queries for the Pokédex API (list / detail / evolutions)."""

from __future__ import annotations

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Pokemon,
    PokemonEvolution,
    PokemonForm,
    PokemonType,
    Type,
)
from app.schemas.pokemon import (
    AbilityOut,
    EvolutionMember,
    EvolutionStage,
    FormAbilityOut,
    FormOut,
    GenerationOut,
    MatchupsOut,
    PokemonDetail,
    PokemonSummary,
    StatsOut,
)
from app.services import matchups as matchups_service

SORT_COLUMNS = {
    "dex": Pokemon.dex_number,
    "name": Pokemon.name,
    "total": Pokemon.base_stat_total,
    "hp": Pokemon.hp,
    "attack": Pokemon.attack,
    "defense": Pokemon.defense,
    "sp_attack": Pokemon.sp_attack,
    "sp_defense": Pokemon.sp_defense,
    "speed": Pokemon.speed,
}


def sprite_url(pokemon: Pokemon) -> str:
    return f"/sprites/{pokemon.sprite_path}" if pokemon.sprite_path else ""


def _type_names(pokemon: Pokemon) -> list[str]:
    return [pt.type.identifier for pt in pokemon.types]


def _apply_filters(
    stmt: Select,
    *,
    q: str | None,
    types: list[str] | None,
    generation: int | None,
    legendary: bool | None,
    mythical: bool | None,
) -> Select:
    if q:
        q = q.strip()
        if q.isdigit():
            stmt = stmt.where(Pokemon.dex_number == int(q))
        else:
            stmt = stmt.where(Pokemon.name.ilike(f"%{q}%"))
    if generation is not None:
        stmt = stmt.where(Pokemon.generation_id == generation)
    if legendary is not None:
        stmt = stmt.where(Pokemon.is_legendary.is_(legendary))
    if mythical is not None:
        stmt = stmt.where(Pokemon.is_mythical.is_(mythical))
    if types:
        # Require the Pokémon to have *all* requested types.
        for type_identifier in types:
            exists = (
                select(PokemonType.pokemon_id)
                .join(Type, Type.id == PokemonType.type_id)
                .where(
                    and_(
                        PokemonType.pokemon_id == Pokemon.id,
                        Type.identifier == type_identifier,
                    )
                )
                .exists()
            )
            stmt = stmt.where(exists)
    return stmt


async def list_pokemon(
    session: AsyncSession,
    *,
    q: str | None = None,
    types: list[str] | None = None,
    generation: int | None = None,
    legendary: bool | None = None,
    mythical: bool | None = None,
    sort: str = "dex",
    order: str = "asc",
    limit: int = 40,
    offset: int = 0,
) -> tuple[list[PokemonSummary], int]:
    filters = dict(
        q=q, types=types, generation=generation, legendary=legendary, mythical=mythical
    )

    count_stmt = _apply_filters(select(func.count(Pokemon.id)), **filters)
    total = (await session.execute(count_stmt)).scalar_one()

    sort_col = SORT_COLUMNS.get(sort, Pokemon.dex_number)
    sort_col = sort_col.desc() if order == "desc" else sort_col.asc()

    stmt = (
        _apply_filters(select(Pokemon), **filters)
        .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
        .order_by(sort_col, Pokemon.dex_number)
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).scalars().all()

    items = [
        PokemonSummary(
            id=p.id,
            dex_number=p.dex_number,
            name=p.name,
            genus=p.genus,
            types=_type_names(p),
            sprite_url=sprite_url(p),
            base_stat_total=p.base_stat_total,
            generation_id=p.generation_id,
            is_legendary=p.is_legendary,
            is_mythical=p.is_mythical,
        )
        for p in rows
    ]
    return items, total


async def get_pokemon(session: AsyncSession, id_or_name: str) -> PokemonDetail | None:
    stmt = select(Pokemon).options(
        selectinload(Pokemon.types).selectinload(PokemonType.type),
        selectinload(Pokemon.abilities),
        selectinload(Pokemon.flavor_texts),
        selectinload(Pokemon.generation),
    )
    if id_or_name.isdigit():
        stmt = stmt.where(Pokemon.dex_number == int(id_or_name))
    else:
        stmt = stmt.where(func.lower(Pokemon.name) == id_or_name.lower())

    pokemon = (await session.execute(stmt)).scalars().first()
    if pokemon is None:
        return None

    # abilities need their Ability objects (name/effect)
    ability_ids = [pa.ability_id for pa in pokemon.abilities]
    from app.models import Ability  # local import to avoid cycle noise

    ability_map = {}
    if ability_ids:
        arows = (
            await session.execute(select(Ability).where(Ability.id.in_(ability_ids)))
        ).scalars().all()
        ability_map = {a.id: a for a in arows}

    abilities = []
    for pa in pokemon.abilities:
        ability = ability_map.get(pa.ability_id)
        abilities.append(
            AbilityOut(
                id=pa.ability_id,
                identifier=ability.identifier if ability else "",
                name=ability.name if ability else "",
                effect=ability.effect if ability else None,
                is_hidden=pa.is_hidden,
            )
        )

    stages, members = await _evolution(session, pokemon)
    forms = await _forms(session, pokemon.id)

    type_ids = [pt.type_id for pt in pokemon.types]
    buckets = await matchups_service.defensive_for(session, type_ids)
    matchups = MatchupsOut(
        weak_4x=buckets.weak_4x,
        weak_2x=buckets.weak_2x,
        resist_half=buckets.resist_half,
        resist_quarter=buckets.resist_quarter,
        immune=buckets.immune,
    )

    gen = pokemon.generation
    return PokemonDetail(
        id=pokemon.id,
        dex_number=pokemon.dex_number,
        name=pokemon.name,
        genus=pokemon.genus,
        types=_type_names(pokemon),
        sprite_url=sprite_url(pokemon),
        height_m=pokemon.height_m,
        weight_kg=pokemon.weight_kg,
        base_experience=pokemon.base_experience,
        capture_rate=pokemon.capture_rate,
        base_happiness=pokemon.base_happiness,
        color=pokemon.color,
        shape=pokemon.shape,
        habitat=pokemon.habitat,
        gender_rate=pokemon.gender_rate,
        hatch_counter=pokemon.hatch_counter,
        growth_rate=pokemon.growth_rate,
        egg_groups=pokemon.egg_groups or [],
        ev_yield=pokemon.ev_yield or {},
        is_legendary=pokemon.is_legendary,
        is_mythical=pokemon.is_mythical,
        is_baby=pokemon.is_baby,
        generation=GenerationOut.model_validate(gen) if gen else None,
        stats=StatsOut(
            hp=pokemon.hp,
            attack=pokemon.attack,
            defense=pokemon.defense,
            sp_attack=pokemon.sp_attack,
            sp_defense=pokemon.sp_defense,
            speed=pokemon.speed,
            total=pokemon.base_stat_total,
        ),
        abilities=abilities,
        flavor_text=pokemon.flavor_text,
        flavor_texts=[ft.flavor_text for ft in pokemon.flavor_texts],
        evolution_chain_id=pokemon.evolution_chain_id,
        evolution_stages=stages,
        evolution_members=members,
        forms=forms,
        matchups=matchups,
    )


def _form_evolution(
    target: PokemonForm, forms_by_id: dict[int, PokemonForm]
) -> tuple[list[EvolutionMember], list[EvolutionStage]]:
    """The connected chain of forms (across the species' evolution chain) that
    `target` belongs to via `evolves_from_form_id`, as members + stages. Returns
    ([], []) when the form has no per-form evolution partners (chain of 1)."""
    # Build parent->children among forms via evolves_from_form_id.
    children: dict[int, list[PokemonForm]] = {}
    for f in forms_by_id.values():
        if f.evolves_from_form_id in forms_by_id:
            children.setdefault(f.evolves_from_form_id, []).append(f)
    # Walk up from target to the chain root, then collect the whole connected set.
    root = target
    seen: set[int] = set()
    while root.evolves_from_form_id in forms_by_id and root.id not in seen:
        seen.add(root.id)
        root = forms_by_id[root.evolves_from_form_id]
    members_out: list[EvolutionMember] = []
    stages_out: list[EvolutionStage] = []
    stack = [root]
    visited: set[int] = set()
    while stack:
        node = stack.pop()
        if node.id in visited:
            continue
        visited.add(node.id)
        members_out.append(
            EvolutionMember(
                id=node.id,
                name=node.name,
                types=node.types or [],
                sprite_url=f"/sprites/{node.sprite_path}" if node.sprite_path else "",
            )
        )
        for child in children.get(node.id, []):
            stages_out.append(
                EvolutionStage(
                    from_id=node.id,
                    from_name=node.name,
                    to_id=child.id,
                    to_name=child.name,
                    trigger=child.evo_trigger,
                    min_level=child.evo_min_level,
                    item=child.evo_item,
                    condition=child.evo_condition,
                )
            )
            stack.append(child)
    if len(members_out) <= 1:
        return [], []
    return members_out, stages_out


async def _forms(session: AsyncSession, base_pokemon_id: int) -> list[FormOut]:
    rows = (
        await session.execute(
            select(PokemonForm)
            .where(PokemonForm.base_pokemon_id == base_pokemon_id)
            .order_by(PokemonForm.sort_order, PokemonForm.id)
        )
    ).scalars().all()
    if not rows:
        return []

    # species set for this evolution chain (to gather sibling-stage forms)
    base = await session.get(Pokemon, base_pokemon_id)
    chain_species: list[int] = [base_pokemon_id]
    if base and base.evolution_chain_id:
        chain_species = [
            sid
            for (sid,) in (
                await session.execute(
                    select(Pokemon.id).where(
                        Pokemon.evolution_chain_id == base.evolution_chain_id
                    )
                )
            ).all()
        ]

    chain_forms = (
        await session.execute(
            select(PokemonForm).where(PokemonForm.base_pokemon_id.in_(chain_species))
        )
    ).scalars().all()
    chain_form_by_id = {f.id: f for f in chain_forms}

    # Resolve type identifiers -> ids so we can recompute each form's defensive
    # matchups (the switcher swaps types, so matchups must follow).
    type_id_by_ident = {
        t.identifier: t.id for t in (await session.execute(select(Type))).scalars().all()
    }
    # Effect text for the forms' abilities (JSONB stores name/identifier only).
    ability_idents = {a["identifier"] for f in rows for a in (f.abilities or [])}
    effect_by_ident: dict[str, str | None] = {}
    if ability_idents:
        from app.models import Ability

        arows = (
            await session.execute(
                select(Ability).where(Ability.identifier.in_(ability_idents))
            )
        ).scalars().all()
        effect_by_ident = {a.identifier: a.effect for a in arows}

    out: list[FormOut] = []
    for f in rows:
        type_ids = [type_id_by_ident[t] for t in (f.types or []) if t in type_id_by_ident]
        buckets = await matchups_service.defensive_for(session, type_ids)
        evo_members, evo_stages = _form_evolution(f, chain_form_by_id)
        out.append(
            FormOut(
                id=f.id,
                name=f.name,
                form_identifier=f.form_identifier,
                category=f.category,
                is_mega=f.is_mega,
                is_gigantamax=f.is_gigantamax,
                is_battle_only=f.is_battle_only,
                types=f.types or [],
                abilities=[
                    FormAbilityOut(
                        name=a["name"],
                        identifier=a["identifier"],
                        is_hidden=a.get("is_hidden", False),
                        effect=effect_by_ident.get(a["identifier"]),
                    )
                    for a in (f.abilities or [])
                ],
                stats=StatsOut(
                    hp=f.hp,
                    attack=f.attack,
                    defense=f.defense,
                    sp_attack=f.sp_attack,
                    sp_defense=f.sp_defense,
                    speed=f.speed,
                    total=f.base_stat_total,
                ),
                height_m=f.height_m,
                weight_kg=f.weight_kg,
                sprite_url=f"/sprites/{f.sprite_path}" if f.sprite_path else "",
                matchups=MatchupsOut(
                    weak_4x=buckets.weak_4x,
                    weak_2x=buckets.weak_2x,
                    resist_half=buckets.resist_half,
                    resist_quarter=buckets.resist_quarter,
                    immune=buckets.immune,
                ),
                flavor_texts=f.flavor_texts or [],
                evolution_members=evo_members,
                evolution_stages=evo_stages,
            )
        )
    return out


async def _evolution(
    session: AsyncSession, pokemon: Pokemon
) -> tuple[list[EvolutionStage], list[EvolutionMember]]:
    if not pokemon.evolution_chain_id:
        return [], []

    edges = (
        await session.execute(
            select(PokemonEvolution).where(
                PokemonEvolution.evolution_chain_id == pokemon.evolution_chain_id
            )
        )
    ).scalars().all()

    # all members of the chain
    members_rows = (
        await session.execute(
            select(Pokemon)
            .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
            .where(Pokemon.evolution_chain_id == pokemon.evolution_chain_id)
            .order_by(Pokemon.dex_number)
        )
    ).scalars().all()

    name_by_id = {m.id: m.name for m in members_rows}

    stages = [
        EvolutionStage(
            from_id=e.from_pokemon_id,
            from_name=name_by_id.get(e.from_pokemon_id) if e.from_pokemon_id else None,
            to_id=e.to_pokemon_id,
            to_name=name_by_id.get(e.to_pokemon_id, ""),
            trigger=e.trigger,
            min_level=e.min_level,
            item=e.item,
            condition=e.condition,
        )
        for e in edges
    ]
    members = [
        EvolutionMember(
            id=m.id,
            name=m.name,
            types=_type_names(m),
            sprite_url=sprite_url(m),
        )
        for m in members_rows
    ]
    return stages, members
