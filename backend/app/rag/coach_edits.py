"""Turn a coach answer's set advice into concrete, validated edits.

After the coach answers, a small structured-output call reads the answer and lists
the per-Pokémon changes it recommends (ability / nature / item / EVs / moves). Every
field is then checked against real data — the member's legal abilities and
learnset, known natures and items — and dropped if it doesn't hold, so the UI only
ever offers edits the slot editor would accept. Nothing is saved here: the page
shows each as a was → now proposal with Apply / Revert.
"""

from __future__ import annotations

import json
import logging
import re

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.rag import answer as answer_service
from app.schemas.team import TeamOut
from app.services import teams as teams_service

log = logging.getLogger(__name__)

_SET_WORDS = re.compile(
    r"\b(nature|ability|item|evs?|moves?|moveset|hold|run|switch|change|replace)\b", re.I
)
_EV = ("hp", "atk", "def", "spa", "spd", "spe")

SYSTEM = """You read a Pokémon coach's answer and list the concrete set changes it \
recommends for specific team members. Use ONLY changes the answer actually states — \
never invent any. Use exact Pokémon names from the roster given. For each member with \
recommended changes give: ability, nature, item (null when the answer doesn't change it), \
evs (all six numbers when the answer gives a spread, else null; "Spd" written next to Atk/HP \
in a spread usually means Speed — use your judgement), moves (the full list only when the \
answer names moves to run, else null). Reply with JSON only."""

_NULLABLE_STR = {"type": ["string", "null"]}
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "edits": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "side": {"type": "string", "enum": ["ours", "theirs"]},
                    "name": {"type": "string"},
                    "ability": _NULLABLE_STR,
                    "nature": _NULLABLE_STR,
                    "item": _NULLABLE_STR,
                    "evs": {
                        "type": ["object", "null"],
                        "additionalProperties": False,
                        "properties": {k: {"type": "integer"} for k in _EV},
                        "required": list(_EV),
                    },
                    "moves": {"type": ["array", "null"], "items": {"type": "string"}},
                },
                "required": ["side", "name", "ability", "nature", "item", "evs", "moves"],
            },
        }
    },
    "required": ["edits"],
}


def worth_extracting(answer: str, team: TeamOut, opponent: TeamOut | None) -> bool:
    """Only when the answer talks about a member's set (saves a call on general answers)."""
    names = [m.name.lower() for m in team.members] + [
        m.name.lower() for m in (opponent.members if opponent else [])
    ]
    low = answer.lower()
    return bool(_SET_WORDS.search(answer)) and any(n in low for n in names)


async def extract_edits(
    session: AsyncSession, answer: str, team: TeamOut, opponent: TeamOut | None
) -> list[dict]:
    if not get_settings().llm_enabled or not worth_extracting(answer, team, opponent):
        return []
    roster = {"ours": [m.name for m in team.members]}
    if opponent:
        roster["theirs"] = [m.name for m in opponent.members]
    user = f"Roster: {json.dumps(roster)}\n\nCoach answer:\n{answer[:4000]}"
    try:
        raw = await answer_service.quick_complete(SYSTEM, user, max_tokens=1500, json_schema=SCHEMA)
        data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
    except Exception:  # noqa: BLE001 — no proposals is a safe fallback
        log.info("coach edit extraction failed", exc_info=True)
        return []

    out: list[dict] = []
    for e in data.get("edits", [])[:8]:
        side = "theirs" if e.get("side") == "theirs" and opponent else "ours"
        tm = opponent if side == "theirs" else team
        m = next((x for x in tm.members if x.name.lower() == str(e.get("name", "")).lower()), None)
        if m is None:
            continue
        row = await teams_service.member_row(session, tm.id, m.slot)
        if row is None:
            continue
        fields: dict = {}
        evs = e.get("evs")
        vals = [int(v) for v in (evs or {}).values()]
        if vals and 0 < sum(vals) <= 510 and all(0 <= v <= 252 for v in vals):
            fields["evs"] = {k: int(v) for k, v in evs.items() if int(v)}
        for k in ("ability", "nature", "item"):
            if e.get(k):
                fields[k] = e[k]
        if e.get("moves"):
            fields["moves"] = list(e["moves"])[:4]
        # Keep only the fields that validate on their own (legal ability, learnable moves…).
        ok: dict = {}
        for k, v in fields.items():
            try:
                await teams_service.resolve_build(session, row, **{k: v})
                ok[k] = v
            except HTTPException:
                continue
        # Drop fields that wouldn't change anything.
        cur = {
            "ability": m.ability.name if m.ability else None,
            "nature": m.nature.name if m.nature else None,
            "item": m.item.name if m.item else None,
        }
        ok = {
            k: v for k, v in ok.items()
            if k not in cur or (cur[k] or "").lower() != str(v).lower()
        }
        if ok:
            out.append({"side": side, "slot": m.slot, "name": m.name, **ok})
    return out
