"""LLM extraction of team-drafting preferences.

Understands open-ended phrasing the keyword parser can't — "fuck legendaries",
"skip the ubers", "nothing too broken" all mean *exclude legendaries*. Returns
``None`` when no LLM is configured or the call/parse fails, so the caller falls
back to the keyword parsers in ``recommend.py``.

The LLM only extracts intent; the deterministic recommender still selects the
actual Pokémon.
"""

from __future__ import annotations

import json
import re

from app.core.config import get_settings
from app.rag import answer as answer_service
from app.services.recommend import DraftPrefs

_ROLES = {"sweeper", "wall", "wallbreaker", "support"}
_TYPES = {
    "normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison",
    "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark",
    "steel", "fairy",
}

SYSTEM = """You extract team-building preferences from a Pokémon drafting request.
Reply with ONLY a JSON object:
{"role": "sweeper"|"wall"|"wallbreaker"|"support"|null,
 "legendaries": "include"|"exclude"|"any",
 "mythicals": "include"|"exclude"|"any",
 "types": [<type names the user wants the Pokémon to BE, lowercase>, ...]}

Read sentiment and negation, not just keywords:
- "no legendaries", "non-legendary", "fuck legendaries", "skip the ubers", \
"nothing broken/restricted" -> legendaries "exclude".
- "only legendaries", "legendaries welcome", "ubers are fine" -> "include".
- unmentioned -> "any". Treat mythicals the same way; if the user rejects \
legendaries without mentioning mythicals, set mythicals "exclude" too.
- role: pick the closest archetype or null. types: usually empty unless they ask \
for a specific typing (e.g. "a steel type").

Return only the JSON, nothing else."""

# Strict JSON Schema for Groq structured output (all fields required,
# additionalProperties disallowed — required by strict mode).
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "role": {
            "type": ["string", "null"],
            "enum": ["sweeper", "wall", "wallbreaker", "support", None],
        },
        "legendaries": {"type": "string", "enum": ["include", "exclude", "any"]},
        "mythicals": {"type": "string", "enum": ["include", "exclude", "any"]},
        "types": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["role", "legendaries", "mythicals", "types"],
}


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if not raw.startswith("{"):
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        raw = m.group(0) if m else raw
    return json.loads(raw)


def _tri(value: object) -> bool | None:
    """'include'->True, 'exclude'->False, anything else ('any'/None)->None."""
    if value == "include":
        return True
    if value == "exclude":
        return False
    return None


def _prefs_from_json(data: dict) -> DraftPrefs:
    role = data.get("role")
    role = role if role in _ROLES else None
    types = [t for t in (data.get("types") or []) if isinstance(t, str) and t.lower() in _TYPES]
    return DraftPrefs(
        role=role,
        include_legendary=_tri(data.get("legendaries")),
        include_mythical=_tri(data.get("mythicals")),
        want_types=[t.lower() for t in types],
    )


async def extract_draft_prefs(question: str) -> DraftPrefs | None:
    if not get_settings().llm_enabled:
        return None
    try:
        # Strict schema-constrained structured output (Groq json_schema) — the
        # model's JSON is guaranteed to match SCHEMA. On any failure the caller
        # falls back to the deterministic keyword parser.
        raw = await answer_service.quick_complete(
            SYSTEM, question, max_tokens=200, json_schema=SCHEMA
        )
        return _prefs_from_json(_extract_json(raw))
    except Exception:
        return None
