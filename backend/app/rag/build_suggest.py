"""Coach-suggested competitive set for one Pokémon, as an *applicable* build.

The LLM picks from the species' (or form's) real options — its legal learnset,
its abilities, the natures and held items in the DB — and every field it returns
is validated against those lists before it reaches the UI, so the damage calc can
apply it as-is. Anything the model invents is dropped (or the EVs clamped), never
passed through.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Item
from app.rag import answer as answer_service
from app.services import builder
from app.services.pokemon_query import get_pokemon

STATS = ("hp", "atk", "def", "spa", "spd", "spe")
EV_CAP, EV_TOTAL = 252, 510


class BuildSuggestion(BaseModel):
    pokemon: str
    moves: list[str]  # up to 4, all legal; moves[0] is the main attack
    ability: str | None = None
    nature: str | None = None
    item: str | None = None
    evs: dict[str, int]
    why: str = ""


class CoachTurn(BaseModel):
    """One earlier exchange: what the user asked and what the coach replied."""

    ask: str
    reply: str = ""


SYSTEM = """You are a competitive Pokémon coach. Suggest ONE strong singles set \
for the given Pokémon, choosing ONLY from the options listed.
Reply with ONLY a JSON object:
{"moves": [4 move names, the main damaging attack FIRST],
 "ability": <one listed ability>,
 "nature": <one listed nature>,
 "item": <a held item name, e.g. "Life Orb", "Choice Scarf", "Leftovers">,
 "evs": {"hp":0,"atk":0,"def":0,"spa":0,"spd":0,"spe":0},
 "why": <one or two short sentences on the plan>}
EVs: each 0-252, total at most 510, in multiples of 4. Use exact names as listed.
When a current set and a follow-up are given, revise that set to satisfy the \
follow-up and keep everything it doesn't ask to change. If the follow-up is only a \
question, return the current set unchanged and answer it in "why"."""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "moves": {"type": "array", "items": {"type": "string"}},
        "ability": {"type": "string"},
        "nature": {"type": "string"},
        "item": {"type": "string"},
        "evs": {
            "type": "object",
            "additionalProperties": False,
            "properties": {k: {"type": "integer"} for k in STATS},
            "required": list(STATS),
        },
        "why": {"type": "string"},
    },
    "required": ["moves", "ability", "nature", "item", "evs", "why"],
}


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if not raw.startswith("{"):
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        raw = m.group(0) if m else raw
    return json.loads(raw)


def _norm(s: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def clamp_evs(raw: object) -> dict[str, int]:
    """Each stat 0–252 in steps of 4; trims the largest spends until the total fits 510."""
    src = raw if isinstance(raw, dict) else {}
    evs: dict[str, int] = {}
    for k in STATS:
        try:
            v = int(src.get(k, 0))
        except (TypeError, ValueError):
            v = 0
        evs[k] = max(0, min(EV_CAP, v)) // 4 * 4
    while sum(evs.values()) > EV_TOTAL:
        top = max(STATS, key=lambda k: evs[k])
        evs[top] -= min(4 * ((sum(evs.values()) - EV_TOTAL + 3) // 4), evs[top])
    return evs


def validate(
    data: dict,
    *,
    pokemon: str,
    moves: list[str],
    abilities: list[str],
    natures: list[str],
    items: list[str],
) -> BuildSuggestion:
    """Keep only names that exist in the given option lists (loose match, canonical name)."""

    def pick(value: object, options: list[str]) -> str | None:
        by = {_norm(o): o for o in options}
        return by.get(_norm(value)) if value else None

    picked: list[str] = []
    for m in data.get("moves") or []:
        name = pick(m, moves)
        if name and name not in picked:
            picked.append(name)
    return BuildSuggestion(
        pokemon=pokemon,
        moves=picked[:4],
        ability=pick(data.get("ability"), abilities),
        nature=pick(data.get("nature"), natures),
        item=pick(data.get("item"), items),
        evs=clamp_evs(data.get("evs")),
        why=str(data.get("why") or "").strip()[:600],
    )


class SuggestError(Exception):
    """No LLM configured, unknown Pokémon, or the model's reply was unusable."""


def _follow_up_block(current: BuildSuggestion, request: str, history: list[CoachTurn]) -> str:
    evs = ", ".join(f"{v} {k}" for k, v in current.evs.items() if v) or "none"
    lines = [
        "\nCurrent set:",
        f"- Moves: {', '.join(current.moves)}",
        f"- Ability: {current.ability or '-'}; Nature: {current.nature or '-'}; "
        f"Item: {current.item or '-'}; EVs: {evs}",
    ]
    if history:
        lines.append("Earlier in this conversation:")
        lines += [f"- User: {t.ask}\n  Coach: {t.reply}" for t in history[-6:]]
    lines.append(f"Follow-up: {request.strip()[:300]}")
    return "\n".join(lines)


async def suggest_build(
    session: AsyncSession,
    pokemon_id: int,
    form_id: int | None = None,
    *,
    request: str | None = None,
    current: BuildSuggestion | None = None,
    history: list[CoachTurn] | None = None,
) -> BuildSuggestion:
    """A fresh set, or — given ``current`` and a ``request`` — that set revised."""
    if not get_settings().llm_enabled:
        raise SuggestError("The coach needs an LLM key to suggest builds.")
    detail = await get_pokemon(session, str(pokemon_id))
    if detail is None:
        raise SuggestError("Pokémon not found.")
    form = next((f for f in (detail.forms or []) if f.id == form_id), None) if form_id else None
    name = form.name if form else detail.name
    types = form.types if form else detail.types
    st = form.stats if form else detail.stats

    learnset = (
        await builder.legal_moves_for_form(session, form_id)
        if form
        else await builder.legal_moves(session, pokemon_id)
    )
    if form and not learnset:  # forms without their own learnset share the species'
        learnset = await builder.legal_moves(session, pokemon_id)
    abilities = (
        [a.name for a in form.abilities]
        if form and form.abilities
        else [a.name for a in await builder.species_abilities(session, pokemon_id)]
    )
    natures = [n.name for n in await builder.all_natures(session)]
    items = list(
        (
            await session.execute(
                select(Item.name).where(Item.category.in_(builder.HELD_CATEGORIES))
            )
        ).scalars()
    )

    move_lines = "\n".join(
        f"- {m.name} ({m.type}, {m.damage_class}"
        + (f", {m.power} BP" if m.power else "")
        + (f", priority {m.priority:+d}" if m.priority else "")
        + ")"
        for m in learnset
    )
    user = (
        f"Pokémon: {name} — {'/'.join(types)}\n"
        f"Base stats: HP {st.hp} / Atk {st.attack} / Def {st.defense} / "
        f"SpA {st.sp_attack} / SpD {st.sp_defense} / Spe {st.speed}\n"
        f"Abilities: {', '.join(abilities)}\n"
        f"Natures: {', '.join(natures)}\n"
        f"Legal moves:\n{move_lines}"
    )
    if current and request and request.strip():
        user += _follow_up_block(current, request, history or [])
    elif request and request.strip():  # a first ask that carries preferences
        user += f"\nThe user wants: {request.strip()[:300]}"
    # A reasoning model can spend its budget thinking over a long learnset and fail the
    # strict-schema check (Groq 400), so retry once with more room.
    data: dict | None = None
    for budget in (1200, 2400):
        try:
            raw = await answer_service.quick_complete(
                SYSTEM, user, max_tokens=budget, json_schema=SCHEMA
            )
            data = _extract_json(raw)
            break
        except Exception:  # rate limit, provider error, bad JSON
            continue
    if data is None:
        raise SuggestError("The coach couldn't produce a build right now.")

    out = validate(
        data,
        pokemon=name,
        moves=[m.name for m in learnset],
        abilities=abilities,
        natures=natures,
        items=items,
    )
    if not out.moves:
        raise SuggestError("The coach's suggestion didn't match this Pokémon's learnset.")
    return out
