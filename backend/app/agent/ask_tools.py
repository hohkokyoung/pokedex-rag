"""Ask-scope tools: read-only adapters over the existing retrieval and services.

Each handler validates nothing about the question (it never sees it) — it takes
explicit arguments, resolves names against the data, calls the existing retriever,
and returns citable chunks plus typed views built from structured data.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent import names
from app.agent.results import ToolResult
from app.agent.tools import AgentContext, tool
from app.agent.views import (
    LearnCheckView,
    LearnersView,
    LearnGroup,
    LearnMove,
    LearnsetView,
    MoveListView,
    MoveRow,
    PokemonCard,
    PokemonListView,
    RankingRow,
    RankingView,
    TypeChartView,
)
from app.models import Ability, KnowledgeChunk, Pokemon, PokemonForm, PokemonType, Type
from app.models.item import Item
from app.models.pokemon import PokemonAbility
from app.rag import hybrid, learnset, matchup, personalize, similarity, sql_retrieval
from app.rag.retrieval import RetrievedChunk
from app.rag.sql_retrieval import StructuredQuery
from app.services import encounters as encounters_service
from app.services import matchups as matchups_service

# Dex lookups serve Ask and both coaches (team and calculator) alike.
ASK_AND_TEAM = ("ask", "team", "calc")

STAT_KEYS = ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")
_STAT_LABEL = {
    "hp": "HP", "attack": "Attack", "defense": "Defense", "sp_attack": "Sp. Atk",
    "sp_defense": "Sp. Def", "speed": "Speed", "base_stat_total": "BST",
    "height_m": "height", "weight_kg": "weight", "capture_rate": "capture rate",
}


def _types(values: list[str]) -> list[str]:
    """Lowercase and keep only real types ("Fire" → "fire")."""
    out = [v.strip().lower() for v in values]
    return [t for t in dict.fromkeys(out) if t in names.STANDARD_TYPES]


# ---- view helpers -----------------------------------------------------------------


def _card_from_row(c: RetrievedChunk, ref: int, **extra) -> PokemonCard:
    """A card from a structured Pokémon row chunk (values + meta)."""
    v = c.values or {}
    meta = c.meta or {}
    return PokemonCard(
        ref=ref, pokemon_id=c.pokemon_id, name=c.pokemon_name or "", dex_number=c.dex_number,
        types=meta.get("types", []),
        stats={k: int(v[k]) for k in STAT_KEYS if v.get(k) is not None},
        total=int(v["base_stat_total"]) if v.get("base_stat_total") is not None else None,
        coverage=meta.get("coverage", []),
        **extra,
    )


def _card_from_pokemon(p: Pokemon, ref: int | None, **extra) -> PokemonCard:
    return PokemonCard(
        ref=ref, pokemon_id=p.id, name=p.name, dex_number=p.dex_number,
        types=[pt.type.identifier for pt in p.types],
        stats={k: getattr(p, k) for k in STAT_KEYS}, total=p.base_stat_total, **extra,
    )


async def _pokemon_by_id(session: AsyncSession, ids: list[int]) -> dict[int, Pokemon]:
    if not ids:
        return {}
    rows = (
        await session.execute(
            select(Pokemon)
            .options(selectinload(Pokemon.types).selectinload(PokemonType.type))
            .where(Pokemon.id.in_(ids))
        )
    ).scalars().all()
    return {p.id: p for p in rows}


def _move_row(c: RetrievedChunk, ref: int) -> MoveRow:
    return MoveRow(ref=ref, **(c.meta or {})["move"])


def _unresolved(kind: str, name: str) -> ToolResult:
    return ToolResult.error(f'unresolved {kind} "{name}"')


def _resolved_note(asked: str, m: names.Match) -> str:
    return "" if m.exact else f' (closest match for "{asked}")'


# ---- query_pokemon ----------------------------------------------------------------


class QueryPokemonArgs(StructuredQuery):
    @field_validator("types_all")
    @classmethod
    def _norm_types(cls, v: list[str]) -> list[str]:
        return _types(v)


@tool(
    "query_pokemon",
    scopes=ASK_AND_TEAM,
    description="Filter/rank Pokémon by type, generation, legendary/mythical and stats "
    "(rankings, thresholds, counts).",
    args=QueryPokemonArgs,
    closed_form=True,
)
async def query_pokemon(
    session: AsyncSession, args: QueryPokemonArgs, ctx: AgentContext
) -> ToolResult:
    sq = StructuredQuery(**args.model_dump())
    rows = await sql_retrieval.execute(session, sq)
    total = await sql_retrieval.count(session, sq)
    data = {"query": sq, "total": total}
    if not rows:
        return ToolResult(summary="no Pokémon match", status="empty", data=data)

    refs = list(range(len(rows)))
    if sq.sort_by:
        stat = sq.sort_by
        view = RankingView(
            stat=stat, order=sq.order, total=total, chunk_refs=refs,
            rows=[
                RankingRow(**_card_from_row(c, i).model_dump(), value=(c.values or {}).get(stat))
                for i, c in enumerate(rows)
            ],
        )
        top = rows[0]
        summary = (
            f"{total} match · top {top.pokemon_name} "
            f"({_STAT_LABEL[stat]} {(top.values or {}).get(stat):g})"
        )
    else:
        view = PokemonListView(cards=[_card_from_row(c, i) for i, c in enumerate(rows)],
                               chunk_refs=refs)
        summary = f"{total} match"
    return ToolResult(chunks=rows, views=[view], summary=summary, data=data)


# ---- get_pokemon ------------------------------------------------------------------


class NameArgs(BaseModel):
    name: str


@tool(
    "get_pokemon",
    scopes=ASK_AND_TEAM,
    description="One Pokémon's (or form's) profile and Pokédex entries.",
    args=NameArgs,
)
async def get_pokemon(session: AsyncSession, args: NameArgs, ctx: AgentContext) -> ToolResult:
    matches = await names.resolve(session, args.name, ("pokemon", "form"))
    if not matches:
        return _unresolved("Pokémon", args.name)
    m = matches[0]
    if m.kind == "form":
        return await _form_profile(session, m, args.name)

    p = (await _pokemon_by_id(session, [m.id]))[m.id]
    chunks: list[RetrievedChunk] = []
    own = await similarity.target_profile_chunk(session, p)
    if own is not None:
        chunks.append(own)
    dex = (
        await session.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.pokemon_id == p.id, KnowledgeChunk.chunk_type == "dex_entry")
            .order_by(KnowledgeChunk.id)
            .limit(2)
        )
    ).scalars().all()
    for d in dex:
        chunks.append(RetrievedChunk(
            id=d.id, pokemon_id=p.id, pokemon_name=p.name, dex_number=p.dex_number,
            chunk_type="dex_entry", source_ref=d.source_ref, content=d.content, score=1.0,
        ))
    if not chunks:
        return ToolResult.empty(f"no profile for {p.name}")
    entry = next(
        (c.content.split("Pokédex entry: ", 1)[-1] for c in chunks if c.chunk_type == "dex_entry"),
        None,
    )
    card = _card_from_pokemon(p, 0, entry=entry)
    return ToolResult(
        chunks=chunks,
        views=[PokemonListView(cards=[card], chunk_refs=list(range(len(chunks))))],
        summary=f"{p.name}{_resolved_note(args.name, m)}",
    )


async def _form_profile(session: AsyncSession, m: names.Match, asked: str) -> ToolResult:
    f = await session.get(PokemonForm, m.id)
    base = (await _pokemon_by_id(session, [f.base_pokemon_id]))[f.base_pokemon_id]
    stats = ", ".join(f"{_STAT_LABEL[k]} {getattr(f, k)}" for k in STAT_KEYS)
    content = (
        f"{f.name} is an alternate form of {base.name} (#{base.dex_number}): "
        f"{'/'.join(t.title() for t in f.types)}-type. Base stats: {stats}, "
        f"base stat total {f.base_stat_total}."
        + (f" Pokédex entry: {f.flavor_text}" if f.flavor_text else "")
    )
    chunk = RetrievedChunk(
        id=-(9_000_000 + f.id), pokemon_id=base.id, pokemon_name=f.name,
        dex_number=base.dex_number, chunk_type="profile", source_ref="form",
        content=content, score=1.0,
    )
    card = PokemonCard(
        ref=0, pokemon_id=base.id, name=f.name, dex_number=base.dex_number, types=f.types,
        stats={k: getattr(f, k) for k in STAT_KEYS}, total=f.base_stat_total,
        entry=f.flavor_text,
    )
    return ToolResult(
        chunks=[chunk], views=[PokemonListView(cards=[card], chunk_refs=[0])],
        summary=f"{f.name}{_resolved_note(asked, m)}",
    )


# ---- semantic_search --------------------------------------------------------------


class SearchArgs(BaseModel):
    query: str
    k: int | None = None


@tool(
    "semantic_search",
    description="Free-text search of Pokédex descriptions, lore, habitats and appearance.",
    args=SearchArgs,
)
async def semantic_search(
    session: AsyncSession, args: SearchArgs, ctx: AgentContext
) -> ToolResult:
    k = max(1, min(args.k or 6, 10))
    chunks = await hybrid.hybrid_retrieve(session, args.query, k=k)
    if not chunks:
        return ToolResult.empty("no passages found")
    return ToolResult(chunks=chunks, summary=f"{len(chunks)} passages")


# ---- similar_to -------------------------------------------------------------------


class SimilarArgs(BaseModel):
    name: str
    include_target: bool = False


@tool(
    "similar_to",
    description="Other Pokémon that resemble one (type, stats, role); include_target adds its "
    "own profile.",
    args=SimilarArgs,
)
async def similar_to(session: AsyncSession, args: SimilarArgs, ctx: AgentContext) -> ToolResult:
    m = await names.resolve_one(session, args.name, "pokemon")
    if m is None:
        return _unresolved("Pokémon", args.name)
    target = (await _pokemon_by_id(session, [m.id]))[m.id]
    chunks = await similarity.similar_to(session, target, k=6)
    if args.include_target:
        own = await similarity.target_profile_chunk(session, target)
        if own is not None:
            chunks = [own, *chunks]
    if not chunks:
        return ToolResult.empty(f"nothing similar to {target.name}")
    byid = await _pokemon_by_id(session, [c.pokemon_id for c in chunks if c.pokemon_id])
    cards = [
        _card_from_pokemon(byid[c.pokemon_id], i,
                           match=None if c.source_ref == "target" else c.score)
        for i, c in enumerate(chunks)
        if c.pokemon_id in byid
    ]
    extra = f" {target.name}'s own profile is included first." if args.include_target else ""
    note = (
        f"NOTE: The CONTEXT lists the Pokémon most similar to {target.name} by type, stats and "
        f"characteristics (excluding its evolution line).{extra} Name the closest matches and "
        f"briefly say why they resemble {target.name}."
    )
    return ToolResult(
        chunks=chunks,
        views=[PokemonListView(title=f"Similar to {target.name}", cards=cards,
                               chunk_refs=list(range(len(chunks))))],
        summary=f"{len(cards)} like {target.name}{_resolved_note(args.name, m)}",
        note=note,
    )


# ---- user_profile -----------------------------------------------------------------


class NoArgs(BaseModel):
    pass


@tool(
    "user_profile",
    description="Recommendations from the user's own favourites and preferred types.",
    args=NoArgs,
)
async def user_profile(session: AsyncSession, args: NoArgs, ctx: AgentContext) -> ToolResult:
    preferred, favorites = await personalize.load_profile(session)
    candidates = await personalize.recommend_chunks(session, preferred, favorites, k=8)
    fav_chunks = await personalize.favorite_profile_chunks(session, favorites)
    recent = await personalize.recent_questions(session)
    block = personalize.preference_block(preferred, favorites, recent)
    chunks = [*fav_chunks, *candidates]
    offset = len(fav_chunks)
    view = PokemonListView(
        title="Picked for you",
        cards=[_card_from_row(c, offset + i) for i, c in enumerate(candidates)],
        chunk_refs=list(range(offset, len(chunks))),
    )
    return ToolResult(
        chunks=chunks, views=[view] if candidates else [],
        summary=f"{len(candidates)} picks from your profile",
        status="done" if chunks else "empty",
        note=block or None,
        data={"profile": True},
    )


# ---- type charts ------------------------------------------------------------------


def _join(words: list[str]) -> str:
    words = [w.title() for w in sorted(words)]
    return words[0] if len(words) == 1 else f"{', '.join(words[:-1])} and {words[-1]}"


async def _type_chart(
    session: AsyncSession, types: list[str]
) -> tuple[RetrievedChunk, TypeChartView] | None:
    ids = (
        await session.execute(select(Type.id).where(Type.identifier.in_(types)))
    ).scalars().all()
    if len(ids) != len(types):
        return None
    b = await matchups_service.defensive_for(session, list(ids))
    label = "/".join(t.title() for t in types)
    parts = []
    if b.weak_4x:
        parts.append(f"takes 4x damage from {_join(b.weak_4x)} moves")
    if b.weak_2x:
        parts.append(f"takes super-effective (2x) damage from {_join(b.weak_2x)} moves")
    if b.resist_quarter:
        parts.append(f"resists (0.25x) {_join(b.resist_quarter)} moves")
    if b.resist_half:
        parts.append(f"resists (0.5x) {_join(b.resist_half)} moves")
    if b.immune:
        parts.append(f"is immune to {_join(b.immune)} moves")
    content = f"Type chart: a {label}-type Pokémon {'; '.join(parts)}."
    strong: list[str] = []
    if len(types) == 1:
        offense = await matchups_service.offense_multipliers(session, types)
        strong = sorted(t for t, f in offense.items() if f > 1)
        if strong:
            content += f" {label} moves are super-effective against {_join(strong)}-types."
    key = sum(sorted(ids)[i] * (100 ** i) for i in range(len(ids)))
    chunk = RetrievedChunk(
        id=-(1_000_000 + key), pokemon_id=None, pokemon_name=None, dex_number=None,
        chunk_type="type_chart", source_ref=f"{'/'.join(types)} defence",
        content=content, score=1.0,
    )
    view = TypeChartView(
        types=types, weak_4x=b.weak_4x, weak_2x=b.weak_2x, resist_half=b.resist_half,
        resist_quarter=b.resist_quarter, immune=b.immune, strong_against=strong,
    )
    return chunk, view


class TypeMatchupArgs(BaseModel):
    types: list[str] = Field(description="1 or 2 types; 2 = a dual typing")


@tool(
    "type_matchup",
    scopes=ASK_AND_TEAM,
    description="Type chart for a type or dual typing: weaknesses, resistances, immunities, "
    "super-effective hits.",
    args=TypeMatchupArgs,
    closed_form=True,
)
async def type_matchup(
    session: AsyncSession, args: TypeMatchupArgs, ctx: AgentContext
) -> ToolResult:
    types = _types(args.types)[:2]
    if not types:
        return _unresolved("type", ", ".join(args.types))
    out = await _type_chart(session, types)
    if out is None:
        return _unresolved("type", ", ".join(args.types))
    chunk, view = out
    view.chunk_refs = [0]
    return ToolResult(chunks=[chunk], views=[view], summary=f"{'/'.join(types)} type chart",
                      data={"types": types, "view": view})


# ---- coverage_vs_types ------------------------------------------------------------


class CoverageArgs(BaseModel):
    targets: list[str] = Field(default_factory=list, description="defending types")
    against: str | None = Field(None, description="a defending Pokémon; its types are used")
    want: Literal["pokemon", "moves"] = "pokemon"
    attacker_class: Literal["physical", "special"] | None = None
    legendary: bool | None = None
    mythical: bool | None = None
    off_type: bool = False


@tool(
    "coverage_vs_types",
    scopes=ASK_AND_TEAM,
    description="Pokémon or moves hitting types (or a named Pokémon) super-effectively via "
    "learnable moves; off_type ranks by stats only.",
    args=CoverageArgs,
)
async def coverage_vs_types(
    session: AsyncSession, args: CoverageArgs, ctx: AgentContext
) -> ToolResult:
    targets = _types(args.targets)
    if args.against:
        m = await names.resolve_one(session, args.against, "pokemon")
        if m is None:
            return _unresolved("Pokémon", args.against)
        foe = (await _pokemon_by_id(session, [m.id]))[m.id]
        targets = [pt.type.identifier for pt in foe.types]
    if not targets:
        return _unresolved("type", ", ".join(args.targets))
    chunks, note = await matchup.coverage_typed(
        session, targets, attacker_class=args.attacker_class, want=args.want,
        legendary=args.legendary, mythical=args.mythical, off_type=args.off_type, k=8,
    )
    if not chunks:
        return ToolResult.empty("nothing covers those types")

    views = []
    for t in targets:
        out = await _type_chart(session, [t])
        if out is not None:
            idx = next((i for i, c in enumerate(chunks)
                        if c.chunk_type == "type_chart" and c.source_ref == f"{t} defence"), None)
            out[1].chunk_refs = [idx] if idx is not None else []
            views.append(out[1])
    if args.want == "moves":
        rows = [(i, c) for i, c in enumerate(chunks) if c.chunk_type == "move"]
        views.append(MoveListView(moves=[_move_row(c, i) for i, c in rows],
                                  chunk_refs=[i for i, _ in rows]))
        summary = f"{len(rows)} moves vs {'/'.join(targets)}"
    else:
        rows = [(i, c) for i, c in enumerate(chunks) if c.chunk_type == "sql_row"]
        views.append(PokemonListView(
            title=f"Covers {_join(targets)}",
            cards=[_card_from_row(c, i) for i, c in rows], chunk_refs=[i for i, _ in rows],
        ))
        summary = f"{len(rows)} attackers vs {'/'.join(targets)}"
    if not rows:
        return ToolResult(chunks=chunks, views=views[:-1], summary="no attackers found",
                          status="empty", note=note)
    return ToolResult(chunks=chunks, views=views, summary=summary, note=note)


# ---- learnset ---------------------------------------------------------------------


class LearnsetArgs(BaseModel):
    pokemon: str | None = None
    move: str | None = None
    game: str | None = None
    types: list[str] = Field(default_factory=list, description="restrict to these types")
    damage_class: Literal["physical", "special", "status"] | None = None
    legendary: bool | None = None
    mythical: bool | None = None
    method: Literal["level-up", "machine", "tutor", "egg"] | None = None


@tool(
    "learnset",
    scopes=ASK_AND_TEAM,
    description="Pokémon+move: can it learn it; move: who learns it; Pokémon: its moves. "
    "game/method narrow it (machine = TM).",
    args=LearnsetArgs,
)
async def learnset_tool(
    session: AsyncSession, args: LearnsetArgs, ctx: AgentContext
) -> ToolResult:
    pm = mm = None
    if args.pokemon:
        pm = await names.resolve_one(session, args.pokemon, "pokemon")
        if pm is None:
            return _unresolved("Pokémon", args.pokemon)
    if args.move:
        mm = await names.resolve_one(session, args.move, "move")
        if mm is None:
            return _unresolved("move", args.move)
    if pm is None and mm is None:
        return ToolResult.error("needs a Pokémon or a move")
    try:
        plan = await learnset.plan_typed(
            session, pokemon=pm.name if pm else None, move=mm.name if mm else None,
            game=args.game, types=args.types, damage_class=args.damage_class,
            legendary=args.legendary, mythical=args.mythical, method=args.method,
        )
    except learnset.UnresolvedName as e:
        return _unresolved(e.kind, e.name)
    out = await learnset.retrieve_typed(session, plan, k=8)
    d = out.data
    fixed = "".join(
        _resolved_note(asked, m) for asked, m in ((args.pokemon, pm), (args.move, mm)) if m
    )

    if out.kind == "pair":
        p = (await _pokemon_by_id(session, [d["pokemon"].id]))[d["pokemon"].id]
        view = LearnCheckView(
            pokemon=_card_from_pokemon(p, 0), move=_move_row(out.chunks[1], 1),
            ok=d["ok"], how=d["how"], game=d["game"], method=d["method"], chunk_refs=[0, 1],
        )
        verdict = f"yes, {d['how']}" if d["ok"] else "no"
        return ToolResult(
            chunks=out.chunks, views=[view], note=out.note, closed=True, data=d,
            summary=f"{p.name} × {d['move'].name}: {verdict}{fixed}",
        )

    if out.kind == "learners":
        users = list(enumerate(out.chunks[2:], start=2))
        how = d["hows"]
        view = LearnersView(
            move=_move_row(out.chunks[0], 0), total=d["total"], by_method=d["by_method"],
            scope=d["scope"], game=d["game"], method=d["method"],
            rows=[_card_from_row(c, i, via=how.get(c.pokemon_id)) for i, c in users],
            chunk_refs=list(range(len(out.chunks))),
        )
        status = "done" if d["total"] else "empty"
        return ToolResult(
            chunks=out.chunks, views=[view], note=out.note, closed=True, status=status, data=d,
            summary=f"{d['total']} learn {d['move'].name}{fixed}",
        )

    p = (await _pokemon_by_id(session, [d["pokemon"].id]))[d["pokemon"].id]
    groups = [
        LearnGroup(ref=ref, method=method, label=label, moves=[
            LearnMove(name=m.name, type=t, damage_class=m.damage_class, power=m.power,
                      level=lv if method == "level-up" else None)
            for m, t, lv in moves
        ])
        for ref, method, label, moves in d["groups"]
    ]
    total = sum(len(g.moves) for g in groups)
    view = LearnsetView(
        pokemon=_card_from_pokemon(p, 0 if d["has_profile"] else None), game=d["game"],
        groups=groups, chunk_refs=list(range(len(out.chunks))),
    )
    return ToolResult(
        chunks=out.chunks, views=[view], note=out.note, closed=False, data=d,
        status="done" if total else "empty",
        summary=f"{p.name} learns {total} moves{fixed}",
    )


# ---- move_info --------------------------------------------------------------------


@tool(
    "move_info",
    scopes=ASK_AND_TEAM,
    description="A move's type, category, power, accuracy, PP, effect and learner count.",
    args=NameArgs,
    closed_form=True,
)
async def move_info(session: AsyncSession, args: NameArgs, ctx: AgentContext) -> ToolResult:
    m = await names.resolve_one(session, args.name, "move")
    if m is None:
        return _unresolved("move", args.name)
    move, mtype, n = await learnset._move_with_type(session, m.id)
    chunk = learnset.move_chunk(move, mtype, n)
    return ToolResult(
        chunks=[chunk], views=[MoveListView(moves=[_move_row(chunk, 0)], chunk_refs=[0])],
        summary=f"{move.name}{_resolved_note(args.name, m)}",
    )


# ---- ability_info / item_info -----------------------------------------------------


@tool(
    "ability_info",
    scopes=ASK_AND_TEAM,
    description="An ability's effect and holder count.",
    args=NameArgs,
)
async def ability_info(session: AsyncSession, args: NameArgs, ctx: AgentContext) -> ToolResult:
    m = await names.resolve_one(session, args.name, "ability")
    if m is None:
        return ToolResult.empty(f'no ability "{args.name}"')
    a = await session.get(Ability, m.id)
    holders = await session.scalar(
        select(func.count()).select_from(PokemonAbility).where(PokemonAbility.ability_id == a.id)
    )
    effect = " ".join(filter(None, [a.short_effect, a.effect]))
    chunk = RetrievedChunk(
        id=-(6_000_000 + a.id), pokemon_id=None, pokemon_name=None, dex_number=None,
        chunk_type="ability", source_ref=a.name,
        content=f"{a.name} is an ability. {effect or 'No effect text in the data.'} "
        f"{holders or 0} Pokémon can have it.",
        score=1.0,
    )
    return ToolResult(chunks=[chunk], summary=f"{a.name}{_resolved_note(args.name, m)}")


@tool(
    "item_info",
    scopes=ASK_AND_TEAM,
    description="An item's category, effect and Fling power.",
    args=NameArgs,
)
async def item_info(session: AsyncSession, args: NameArgs, ctx: AgentContext) -> ToolResult:
    m = await names.resolve_one(session, args.name, "item")
    if m is None:
        return ToolResult.empty(f'no item "{args.name}"')
    it = await session.get(Item, m.id)
    bits = [f"{it.name} is an item" + (f" ({it.category})" if it.category else "") + "."]
    if it.short_effect:
        bits.append(f"Effect: {it.short_effect}")
    if it.flavor_text:
        bits.append(f"In-game description: {it.flavor_text}")
    if it.fling_power:
        bits.append(f"Fling power {it.fling_power}.")
    chunk = RetrievedChunk(
        id=-(7_000_000 + it.id), pokemon_id=None, pokemon_name=None, dex_number=None,
        chunk_type="item", source_ref=it.name, content=" ".join(bits), score=1.0,
    )
    return ToolResult(chunks=[chunk], summary=f"{it.name}{_resolved_note(args.name, m)}")


# ---- encounters -------------------------------------------------------------------


class EncounterArgs(BaseModel):
    pokemon: str
    game: str | None = None


@tool(
    "encounters",
    description="Where to find a Pokémon in the wild, per game (data ends at Sword/Shield).",
    args=EncounterArgs,
)
async def encounters(
    session: AsyncSession, args: EncounterArgs, ctx: AgentContext
) -> ToolResult:
    matches = await names.resolve(session, args.pokemon, ("pokemon", "form"))
    if not matches:
        return _unresolved("Pokémon", args.pokemon)
    m = matches[0]
    out = await encounters_service.encounters_by_game(session, m.id)
    if not out.games:
        return ToolResult.empty(f"{m.name} isn't found in the wild in the data")
    if args.game:
        key = args.game.strip().lower()
        g = next((g for g in out.games if key in g.version.lower()), None)
        if g is not None and g.version_id != out.version_id:
            out = await encounters_service.encounters_by_game(session, m.id, g.version_id)
    game = next(g for g in out.games if g.version_id == out.version_id)
    places = []
    for e in out.encounters[:15]:
        where = e.location + (f" ({e.area})" if e.area else "")
        lv = f"Lv {e.min_level}" + (f"–{e.max_level}" if e.max_level != e.min_level else "")
        chance = f", {e.chance}%" if e.chance else ""
        places.append(f"{where}: {e.method_name}, {lv}{chance}")
    others = [g.version for g in out.games if g.version_id != game.version_id]
    content = f"Where to find {m.name} in Pokémon {game.version}: " + "; ".join(places) + "."
    if others:
        content += f" Also found in: {', '.join(others)}."
    chunk = RetrievedChunk(
        id=-(8_000_000 + m.id * 100 + game.version_id % 100), pokemon_id=None,
        pokemon_name=m.name, dex_number=None, chunk_type="encounters",
        source_ref=game.version, content=content, score=1.0,
    )
    return ToolResult(chunks=[chunk], summary=f"{m.name} in {game.version}: {game.places} places")
