"""Deterministic candidate recommender for coach-assisted drafting.

Given a team + its analysis and the user's question, rank real Pokémon from the DB
as additions. The ranking adapts to what was asked (a role like *sweeper*/*wall*, or
a specific coverage type) and, by default, favours candidates that patch the team's
analysis — resisting shared weaknesses and covering types the team can't hit. No LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Pokemon, PokemonType
from app.schemas.analysis import TeamAnalysis
from app.schemas.recommend import Candidate
from app.schemas.team import TeamOut
from app.services import matchups, nlfilters
from app.services.pokemon_query import sprite_url
from app.services.team_analysis import _classify

# Preference keywords → internal role. Order matters: more specific roles first, so
# "wallbreaker" isn't captured by the "wall" keyword.
_ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "wallbreaker": ("wallbreaker", "wall breaker", "breaker", "hard hitter", "hard-hitter"),
    "sweeper": ("sweeper", "sweep", "fast attacker", "speedy", "fast "),
    "wall": ("wall", "tank", "defensive", "bulky", "stall", "defense"),
    "support": ("support", "utility", "pivot"),
}

@dataclass
class DraftPrefs:
    """Explicit drafting preferences, typically extracted by the LLM. Any field left
    None falls back to the keyword parser inside ``recommend_additions``."""

    role: str | None = None
    include_legendary: bool | None = None
    include_mythical: bool | None = None
    want_types: list[str] = field(default_factory=list)


_DRAFT_KEYWORDS = (
    "draft", "recommend", "suggest", "who should", "what should", "which pokemon",
    "fill", "complete", "round out", "build", "add ", "additions", "rest of", "other",
    "best 5", "best five", "team of", "picks", "options",
)


def is_draft_request(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in _DRAFT_KEYWORDS)


def parse_role(question: str) -> str | None:
    q = question.lower()
    for role, kws in _ROLE_KEYWORDS.items():
        if any(kw in q for kw in kws):
            return role
    return None


def allow_legendary(question: str) -> bool:
    # Include legendaries only when the user positively asks for them; default excludes.
    return nlfilters.legendary_constraint(question) is True


def requested_types(question: str, known: set[str]) -> list[str]:
    q = question.lower()
    return [t for t in known if t in q]


def _offense(bs: dict[str, int]) -> int:
    return max(bs["attack"], bs["sp_attack"])


def _bulk(bs: dict[str, int]) -> int:
    return bs["hp"] + bs["defense"] + bs["sp_defense"]


def _role_value(role: str | None, bs: dict[str, int]) -> float:
    spe, off, blk, bst = bs["speed"], _offense(bs), _bulk(bs), sum(bs.values())
    if role == "sweeper":
        return spe * 1.5 + off  # reward speed heavily
    if role == "wall":
        return blk
    if role == "wallbreaker":
        return off * 1.5 + max(0, 100 - spe) * 0.5
    if role == "support":
        return blk * 0.7 + spe
    return bst  # no explicit role → overall quality


def _base_stats(p: Pokemon) -> dict[str, int]:
    return {
        "hp": p.hp, "attack": p.attack, "defense": p.defense,
        "sp_attack": p.sp_attack, "sp_defense": p.sp_defense, "speed": p.speed,
    }


async def recommend_additions(
    session: AsyncSession,
    team: TeamOut,
    analysis: TeamAnalysis,
    question: str,
    *,
    prefs: DraftPrefs | None = None,
    limit: int = 6,
) -> list[Candidate]:
    # Explicit prefs (from the LLM) win field-by-field; unset fields fall back to
    # the keyword parsers, so offline behaviour is unchanged.
    role = prefs.role if prefs and prefs.role is not None else parse_role(question)
    legendaries_ok = (
        prefs.include_legendary
        if prefs and prefs.include_legendary is not None
        else allow_legendary(question)
    )
    known_types = set(await matchups.all_type_idents(session))
    want_types = (
        prefs.want_types if prefs and prefs.want_types else requested_types(question, known_types)
    )
    on_team = {m.pokemon_id for m in team.members}

    # Prefilter the pool so scoring stays cheap.
    stmt = select(Pokemon).options(
        selectinload(Pokemon.types).selectinload(PokemonType.type)
    )
    mythical_ok = (
        prefs.include_mythical
        if prefs and prefs.include_mythical is not None
        else legendaries_ok  # by default mythicals share the legendary decision
    )
    if not legendaries_ok:
        stmt = stmt.where(Pokemon.is_legendary.is_(False))
    if not mythical_ok:
        stmt = stmt.where(Pokemon.is_mythical.is_(False))
    if on_team:
        stmt = stmt.where(Pokemon.id.notin_(on_team))
    if role == "sweeper":
        stmt = stmt.where(
            Pokemon.speed >= 90,
            func.greatest(Pokemon.attack, Pokemon.sp_attack) >= 95,
        )
    elif role == "wall":
        stmt = stmt.where((Pokemon.hp + Pokemon.defense + Pokemon.sp_defense) >= 280)
    elif role == "wallbreaker":
        stmt = stmt.where(func.greatest(Pokemon.attack, Pokemon.sp_attack) >= 110)
    else:
        stmt = stmt.where(Pokemon.base_stat_total >= 480)
    if want_types:
        stmt = stmt.where(
            or_(
                *[
                    Pokemon.types.any(PokemonType.type.has(identifier=t))
                    for t in want_types
                ]
            )
        )
    stmt = stmt.order_by(Pokemon.base_stat_total.desc()).limit(150)
    pool = (await session.execute(stmt)).scalars().all()

    shared_weak = [w.type for w in analysis.defensive.shared_weaknesses]
    uncovered = analysis.offensive.uncovered_types

    scored: list[tuple[float, Candidate]] = []
    for p in pool:
        bs = _base_stats(p)
        types = [pt.type.identifier for pt in p.types]
        type_ids = await matchups.ids_for(session, types)

        role_val = _role_value(role, bs)

        resisted: list[str] = []
        if shared_weak:
            dmult = await matchups.defense_multipliers(session, type_ids)
            resisted = [t for t in shared_weak if dmult.get(t, 1.0) < 1]
        covered: list[str] = []
        if uncovered:
            omult = await matchups.offense_multipliers(session, types)
            covered = [t for t in uncovered if omult.get(t, 1.0) >= 2]

        # When a role is explicitly requested it should dominate; otherwise the
        # patch score (weakness/coverage fit) leads and role is a light quality prior.
        patch = len(resisted) * 40 + len(covered) * 25
        role_weight = 0.4 if role else 0.03
        want_bonus = 40 if want_types and any(t in want_types for t in types) else 0
        total = role_weight * role_val + patch + want_bonus

        scored.append(
            (
                total,
                Candidate(
                    pokemon_id=p.id,
                    dex_number=p.dex_number,
                    name=p.name,
                    types=types,
                    sprite_url=sprite_url(p),
                    role=_classify(bs["speed"], _offense(bs), _bulk(bs)),
                    base_stats=bs,
                    reason=_reason(role, bs, resisted, covered),
                ),
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _score, c in scored[:limit]]


def _reason(
    role: str | None, bs: dict[str, int], resisted: list[str], covered: list[str]
) -> str:
    bits = [f"{_classify(bs['speed'], _offense(bs), _bulk(bs))} (Spe {bs['speed']}, "
            f"best offense {_offense(bs)}, BST {sum(bs.values())})"]
    if resisted:
        bits.append("resists your shared weakness to " + ", ".join(resisted))
    if covered:
        bits.append("adds super-effective coverage vs " + ", ".join(covered))
    return "; ".join(bits) + "."


def to_chunks(candidates: list[Candidate]):
    """Represent candidates as citable RetrievedChunk passages for the coach."""
    from app.rag.retrieval import RetrievedChunk

    chunks = []
    for c in candidates:
        stat = "/".join(
            f"{k.replace('sp_', 'Sp')}{c.base_stats[k]}"
            for k in ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")
        )
        content = (
            f"Candidate addition: {c.name} ({'/'.join(c.types)}), role {c.role}. "
            f"Base stats {stat}. {c.reason}"
        )
        chunks.append(
            RetrievedChunk(
                id=-1,
                pokemon_id=c.pokemon_id,
                pokemon_name=c.name,
                dex_number=c.dex_number,
                chunk_type="candidate",
                source_ref=f"candidate-{c.pokemon_id}",
                content=content,
                score=1.0,
            )
        )
    return chunks
