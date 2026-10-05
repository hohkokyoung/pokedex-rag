"""Tests for LLM draft-preference extraction + prefs override in the recommender."""

from __future__ import annotations

from app.rag.draft_intent import _prefs_from_json
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import recommend, team_analysis
from app.services import teams as teams_service
from app.services.recommend import DraftPrefs

# ---- pure: JSON → DraftPrefs mapping (no LLM) ----


def test_prefs_from_json_exclude() -> None:
    p = _prefs_from_json(
        {"role": "sweeper", "legendaries": "exclude", "mythicals": "exclude", "types": ["steel"]}
    )
    assert p.role == "sweeper"
    assert p.include_legendary is False
    assert p.include_mythical is False
    assert p.want_types == ["steel"]


def test_prefs_from_json_include_and_any() -> None:
    p = _prefs_from_json({"role": "bogus", "legendaries": "include", "mythicals": "any"})
    assert p.role is None  # unknown role dropped
    assert p.include_legendary is True
    assert p.include_mythical is None  # "any" → no constraint


def test_prefs_from_json_filters_unknown_types() -> None:
    p = _prefs_from_json({"types": ["steel", "banana", "FIRE"]})
    assert p.want_types == ["steel", "fire"]  # unknowns removed, lowercased


# ---- integration: explicit prefs beat the question text ----


async def test_prefs_override_excludes_legendaries(session) -> None:
    # Question text would (via keywords) INCLUDE legendaries, but explicit prefs exclude.
    team = await teams_service.create_team(
        session, TeamCreate(name="__t_pref__", kind="player")
    )
    try:
        await teams_service.set_slot(session, team.id, 1, SlotUpdate(pokemon_id=1))
        full = await teams_service.get_team(session, team.id)
        analysis = await team_analysis.analyze(session, full)
        prefs = DraftPrefs(include_legendary=False, include_mythical=False)
        cands = await recommend.recommend_additions(
            session, full, analysis, "legendaries are welcome, give me sweepers", prefs=prefs
        )
        assert cands
        from app.models import Pokemon

        for c in cands:
            p = await session.get(Pokemon, c.pokemon_id)
            assert not p.is_legendary and not p.is_mythical
    finally:
        await teams_service.delete_team(session, team.id)
