"""Read queries for the Pokédex API (list / detail / evolutions)."""

from __future__ import annotations

import re

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Pokemon,
    PokemonEvolution,
    PokemonFlavorText,
    PokemonForm,
    PokemonType,
    Type,
)
from app.schemas.pokemon import (
    AbilityOut,
    CosmeticVariantOut,
    EvolutionMember,
    EvolutionStage,
    FlavorEntry,
    FormAbilityOut,
    FormOut,
    GenerationOut,
    MatchupsOut,
    PokemonDetail,
    PokemonSummary,
    StatsOut,
)
from app.services import alcremie
from app.services import matchups as matchups_service
from app.services.evolution_display import evolution_display
from app.services.versions import gen_label, generation_for_version

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


def _variants(pokemon: Pokemon) -> list[CosmeticVariantOut]:
    """Cosmetic variants with their artwork URL (tolerates pre-sprite name-only rows)."""
    out = []
    for v in pokemon.cosmetic_variants or []:
        if isinstance(v, str):
            out.append(CosmeticVariantOut(name=v))
        else:
            path = v.get("sprite_path")
            url = f"/sprites/{path}" if path else ""
            out.append(CosmeticVariantOut(name=v["name"], sprite_url=url))
    return out


def _type_names(pokemon: Pokemon) -> list[str]:
    return [pt.type.identifier for pt in pokemon.types]


def _flavor_entry(text: str, version: str | None) -> FlavorEntry:
    gen = generation_for_version(version)
    return FlavorEntry(
        text=text,
        version=version,
        generation=gen,
        generation_label=gen_label(gen),
    )


def _flavor_key(text: str) -> str:
    # Same entry across games, ignoring case/punctuation ("VENUSAUR's" vs "Venusaur’s").
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _flavor_entries(rows: list[PokemonFlavorText]) -> list[FlavorEntry]:
    """One entry per distinct text, listing every game that uses it, oldest first.

    Rows are stored one per game in release order; the newest game's wording is
    shown (later games fixed the old all-caps names).
    """
    groups: dict[str, FlavorEntry] = {}
    for ft in sorted(rows, key=lambda r: r.id):
        key = _flavor_key(ft.flavor_text)
        gen = generation_for_version(ft.version)
        e = groups.get(key)
        if e is None:
            e = groups[key] = _flavor_entry(ft.flavor_text, ft.version)
        else:
            e.text = ft.flavor_text
        if ft.version and ft.version not in e.versions:
            e.versions.append(ft.version)
            e.version_generations.append(gen)
        if gen is not None and gen not in e.generations:
            e.generations.append(gen)
    return list(groups.values())


def _apply_filters(
    stmt: Select,
    *,
    q: str | None,
    types: list[str] | None,
    generation: list[int] | None,
    legendary: bool | None,
    mythical: bool | None,
) -> Select:
    if q:
        q = q.strip()
        if q.isdigit():
            stmt = stmt.where(Pokemon.dex_number == int(q))
        else:
            stmt = stmt.where(Pokemon.name.ilike(f"%{q}%"))
    if generation:
        stmt = stmt.where(Pokemon.generation_id.in_(generation))
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
    generation: list[int] | None = None,
    legendary: bool | None = None,
    mythical: bool | None = None,
    sort: str = "dex",
    order: str = "asc",
    limit: int = 40,
    offset: int = 0,
) -> tuple[list[PokemonSummary], int]:
    filters = dict(q=q, types=types, generation=generation, legendary=legendary, mythical=mythical)

    sort_col = SORT_COLUMNS.get(sort, Pokemon.dex_number)
    sort_col = sort_col.desc() if order == "desc" else sort_col.asc()

    # A by-name search also surfaces alternate forms (e.g. "Hisuian Growlithe"),
    # which live in `pokemon_forms`, not the default-species `pokemon` table. The
    # default browse grid (and dex-number search) stays default-species only, so
    # counts/teams/RAG keep their default-form invariant. Because a name search
    # returns a small set, we gather species + forms and paginate in memory.
    q_name = q.strip() if q else None
    if q_name and not q_name.isdigit():
        species_rows = (
            (
                await session.execute(
                    _apply_filters(select(Pokemon), **filters)
                    .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
                    .order_by(sort_col, Pokemon.dex_number)
                )
            )
            .scalars()
            .all()
        )
        combined = [_species_summary(p) for p in species_rows]
        combined += await _form_search_summaries(
            session, q_name, types, generation, legendary, mythical
        )
        total = len(combined)
        return combined[offset : offset + limit], total

    count_stmt = _apply_filters(select(func.count(Pokemon.id)), **filters)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        _apply_filters(select(Pokemon), **filters)
        .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
        .order_by(sort_col, Pokemon.dex_number)
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).scalars().all()
    items = [_species_summary(p) for p in rows]
    return items, total


def _summary_stats(p: Pokemon | PokemonForm) -> StatsOut:
    return StatsOut(
        hp=p.hp,
        attack=p.attack,
        defense=p.defense,
        sp_attack=p.sp_attack,
        sp_defense=p.sp_defense,
        speed=p.speed,
        total=p.base_stat_total,
    )


def _species_summary(p: Pokemon) -> PokemonSummary:
    return PokemonSummary(
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
        stats=_summary_stats(p),
    )


async def _form_search_summaries(
    session: AsyncSession,
    q_name: str,
    types: list[str] | None,
    generation: list[int] | None,
    legendary: bool | None,
    mythical: bool | None,
) -> list[PokemonSummary]:
    """Alternate forms whose name matches, as summaries that link back to the base
    species' page (``dex_number`` = base dex, ``form_id`` set). Type filters apply to
    the form's own types; generation/legendary/mythical apply to the base species."""
    form_rows = (
        (
            await session.execute(
                select(PokemonForm)
                .where(PokemonForm.name.ilike(f"%{q_name}%"))
                .order_by(PokemonForm.base_pokemon_id, PokemonForm.sort_order, PokemonForm.id)
            )
        )
        .scalars()
        .all()
    )
    if not form_rows:
        return []

    base_ids = {f.base_pokemon_id for f in form_rows}
    bases = {
        p.id: p
        for p in (await session.execute(select(Pokemon).where(Pokemon.id.in_(base_ids))))
        .scalars()
        .all()
    }
    wanted_types = set(types or [])
    out: list[PokemonSummary] = []
    for f in form_rows:
        base = bases.get(f.base_pokemon_id)
        if base is None:
            continue
        if wanted_types and not wanted_types.issubset(set(f.types or [])):
            continue
        if generation and base.generation_id not in generation:
            continue
        if legendary is not None and base.is_legendary is not legendary:
            continue
        if mythical is not None and base.is_mythical is not mythical:
            continue
        out.append(
            PokemonSummary(
                id=f.id,
                dex_number=base.dex_number,
                name=f.name,
                genus=base.genus,
                types=f.types or [],
                sprite_url=f"/sprites/{f.sprite_path}" if f.sprite_path else "",
                base_stat_total=f.base_stat_total,
                generation_id=base.generation_id,
                is_legendary=base.is_legendary,
                is_mythical=base.is_mythical,
                form_id=f.id,
                stats=_summary_stats(f),
            )
        )
    return out


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
            (await session.execute(select(Ability).where(Ability.id.in_(ability_ids))))
            .scalars()
            .all()
        )
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
    entries = _flavor_entries(pokemon.flavor_texts)
    return PokemonDetail(
        id=pokemon.id,
        dex_number=pokemon.dex_number,
        name=pokemon.name,
        genus=pokemon.genus,
        types=_type_names(pokemon),
        sprite_url=sprite_url(pokemon),
        female_sprite_url=(
            f"/sprites/{pokemon.female_sprite_path}" if pokemon.female_sprite_path else None
        ),
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
        flavor_texts=[e.text for e in entries],
        flavor_entries=entries,
        evolution_chain_id=pokemon.evolution_chain_id,
        evolution_stages=stages,
        evolution_members=members,
        spin_guide=alcremie.spin_guide_for(stages),
        forms=forms,
        matchups=matchups,
    )


def _labelled(stage: EvolutionStage) -> EvolutionStage:
    """The stage with the labels every client shows (chips + description)."""
    stage.display = evolution_display(stage)
    return stage


def _form_evolution(
    target: PokemonForm,
    forms_by_id: dict[int, PokemonForm],
    species_by_id: dict[int, Pokemon],
    species_edges: list[PokemonEvolution],
    dex_by_pokemon_id: dict[int, int],
) -> tuple[list[EvolutionMember], list[EvolutionStage]]:
    """The evolution line `target` sits on: its ancestors plus everything it evolves
    into, as members + stages. Nodes are pokemon ids, so a line can mix forms and
    plain species (Koffing -> Galarian Weezing; Hisuian Qwilfish -> Overqwil).
    Returns ([], []) when the form has no evolution partners (chain of 1)."""

    def _stage(frm: int, to: int, e) -> EvolutionStage:
        # `e` is a PokemonForm (its evo_* fields), a PokemonEvolution, or an evolves_to dict.
        if isinstance(e, dict):
            trigger, level = e.get("trigger"), e.get("min_level")
            item, cond = e.get("item"), e.get("condition")
        elif isinstance(e, PokemonForm):
            trigger, level, item, cond = e.evo_trigger, e.evo_min_level, e.evo_item, e.evo_condition
        else:
            trigger, level, item, cond = e.trigger, e.min_level, e.item, e.condition
        return _labelled(EvolutionStage(
            from_id=frm,
            from_name=_name(frm),
            to_id=to,
            to_name=_name(to) or "",
            trigger=trigger,
            min_level=level,
            item=item,
            condition=cond,
        ))

    def _known(pid: int | None) -> bool:
        return pid in forms_by_id or pid in species_by_id

    def _name(pid: int) -> str | None:
        node = forms_by_id.get(pid) or species_by_id.get(pid)
        return node.name if node else None

    def _parent(pid: int):
        if pid in forms_by_id:
            f = forms_by_id[pid]
            return (f.evolves_from_form_id, f) if _known(f.evolves_from_form_id) else None
        edge = next(
            (e for e in species_edges if e.to_pokemon_id == pid and _known(e.from_pokemon_id)),
            None,
        )
        return (edge.from_pokemon_id, edge) if edge else None

    def _children(pid: int) -> list[tuple[int, object]]:
        if pid in forms_by_id:
            out: list[tuple[int, object]] = [
                (f.id, f) for f in forms_by_id.values() if f.evolves_from_form_id == pid
            ]
            out += [
                (e["to_pokemon_id"], e)
                for e in (forms_by_id[pid].evolves_to or [])
                if e.get("to_pokemon_id") in species_by_id
            ]
            return out
        return [(e.to_pokemon_id, e) for e in species_edges if e.from_pokemon_id == pid]

    order: list[int] = [target.id]
    stages_out: list[EvolutionStage] = []
    # Walk up to the root.
    node = target.id
    while (up := _parent(node)) and up[0] not in order:
        stages_out.append(_stage(up[0], node, up[1]))
        order.insert(0, up[0])
        node = up[0]
    # Then everything `target` evolves into.
    stack = [target.id]
    while stack:
        cur = stack.pop()
        for child, edge in _children(cur):
            if child in order:
                continue
            order.append(child)
            stages_out.append(_stage(cur, child, edge))
            stack.append(child)

    if len(order) <= 1:
        return [], []
    members_out: list[EvolutionMember] = []
    for pid in order:
        if pid in forms_by_id:
            f = forms_by_id[pid]
            members_out.append(
                EvolutionMember(
                    id=f.id,
                    name=f.name,
                    types=f.types or [],
                    sprite_url=f"/sprites/{f.sprite_path}" if f.sprite_path else "",
                    dex_number=dex_by_pokemon_id.get(f.base_pokemon_id, 0),
                    form_id=f.id,
                )
            )
        else:
            m = species_by_id[pid]
            members_out.append(
                EvolutionMember(
                    id=m.id,
                    name=m.name,
                    types=_type_names(m),
                    sprite_url=sprite_url(m),
                    dex_number=m.dex_number,
                    variants=_variants(m),
                )
            )
    return members_out, stages_out


async def _forms(session: AsyncSession, base_pokemon_id: int) -> list[FormOut]:
    rows = (
        (
            await session.execute(
                select(PokemonForm)
                .where(PokemonForm.base_pokemon_id == base_pokemon_id)
                .order_by(PokemonForm.sort_order, PokemonForm.id)
            )
        )
        .scalars()
        .all()
    )
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
                    select(Pokemon.id).where(Pokemon.evolution_chain_id == base.evolution_chain_id)
                )
            ).all()
        ]

    chain_forms = (
        (
            await session.execute(
                select(PokemonForm).where(PokemonForm.base_pokemon_id.in_(chain_species))
            )
        )
        .scalars()
        .all()
    )
    chain_form_by_id = {f.id: f for f in chain_forms}
    # Chain species (with types, for evolution members) and their species edges; a
    # form's evolution line can pass through plain species (Koffing -> Galarian Weezing).
    species_by_id = {
        m.id: m
        for m in (
            await session.execute(
                select(Pokemon)
                .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
                .where(Pokemon.id.in_(chain_species))
            )
        )
        .scalars()
        .all()
    }
    species_edges = (
        list(
            (
                await session.execute(
                    select(PokemonEvolution).where(
                        PokemonEvolution.evolution_chain_id == base.evolution_chain_id
                    )
                )
            )
            .scalars()
            .all()
        )
        if base and base.evolution_chain_id
        else []
    )
    # A form links under its base species' dex number (with ?form=<id>), so map each
    # base_pokemon_id in the chain to its dex number for the evolution member links.
    dex_by_pokemon_id = {pid: m.dex_number for pid, m in species_by_id.items()}

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
            (await session.execute(select(Ability).where(Ability.identifier.in_(ability_idents))))
            .scalars()
            .all()
        )
        effect_by_ident = {a.identifier: a.effect for a in arows}
        id_by_ident = {a.identifier: a.id for a in arows}
    else:
        id_by_ident = {}

    out: list[FormOut] = []
    for f in rows:
        type_ids = [type_id_by_ident[t] for t in (f.types or []) if t in type_id_by_ident]
        buckets = await matchups_service.defensive_for(session, type_ids)
        evo_members, evo_stages = _form_evolution(
            f, chain_form_by_id, species_by_id, species_edges, dex_by_pokemon_id
        )
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
                        id=id_by_ident.get(a["identifier"]),
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
                flavor_entries=[_flavor_entry(t, None) for t in (f.flavor_texts or [])],
                evolution_members=evo_members,
                evolution_stages=evo_stages,
                spin_guide=alcremie.spin_guide_for(evo_stages),
            )
        )
    return out


async def _evolution(
    session: AsyncSession, pokemon: Pokemon
) -> tuple[list[EvolutionStage], list[EvolutionMember]]:
    if not pokemon.evolution_chain_id:
        return [], []

    edges = (
        (
            await session.execute(
                select(PokemonEvolution).where(
                    PokemonEvolution.evolution_chain_id == pokemon.evolution_chain_id
                )
            )
        )
        .scalars()
        .all()
    )

    # all members of the chain
    members_rows = (
        (
            await session.execute(
                select(Pokemon)
                .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
                .where(Pokemon.evolution_chain_id == pokemon.evolution_chain_id)
                .order_by(Pokemon.dex_number)
            )
        )
        .scalars()
        .all()
    )

    name_by_id = {m.id: m.name for m in members_rows}

    stages = [
        _labelled(EvolutionStage(
            from_id=e.from_pokemon_id,
            from_name=name_by_id.get(e.from_pokemon_id) if e.from_pokemon_id else None,
            to_id=e.to_pokemon_id,
            to_name=name_by_id.get(e.to_pokemon_id, ""),
            trigger=e.trigger,
            min_level=e.min_level,
            item=e.item,
            condition=e.condition,
        ))
        for e in edges
    ]
    members = [
        EvolutionMember(
            id=m.id,
            name=m.name,
            types=_type_names(m),
            sprite_url=sprite_url(m),
            dex_number=m.dex_number,
            variants=_variants(m),
        )
        for m in members_rows
    ]
    return stages, members
