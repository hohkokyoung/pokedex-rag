"""The team analysis carries the rating and profile only when it describes the team on
its own (DB-backed; skipped without the Compose DB)."""

from __future__ import annotations

import pytest

from app.rag import answer as answer_service
from app.schemas.team import SlotUpdate, TeamCreate
from app.services import team_analysis
from app.services import teams as teams_service


@pytest.fixture
async def teams(session):
    """A three-member team, a one-member opponent and an empty team; deleted afterwards."""
    made = []
    for name, ids in (
        ("__rate_ours__", (445, 6, 9)),
        ("__rate_theirs__", (25,)),
        ("__rate_empty__", ()),
    ):
        t = await teams_service.create_team(session, TeamCreate(name=name, kind="player"))
        made.append(t.id)
        for slot, pid in enumerate(ids, start=1):
            await teams_service.set_slot(session, t.id, slot, SlotUpdate(pokemon_id=pid))
    try:
        yield [await teams_service.get_team(session, i) for i in made]
    finally:
        for i in made:
            await teams_service.delete_team(session, i)


@pytest.fixture
def no_llm(monkeypatch):
    """Any LLM client use fails like a rate-limited provider would, and is recorded."""
    calls: list[str] = []

    def refuse(name):
        def _f(*a, **k):
            calls.append(name)
            raise RuntimeError("429 Too Many Requests")

        return _f

    monkeypatch.setattr(answer_service, "_anthropic", refuse("anthropic"))
    monkeypatch.setattr(answer_service, "_groq", refuse("groq"))
    return calls


async def test_opponent_free_analysis_has_rating_and_profile(session, teams, no_llm) -> None:
    ours, _, _ = teams
    a = await team_analysis.analyze(session, ours)
    assert a.rating is not None and a.profile is not None
    assert a.rating.capped and a.rating.ceiling == 50
    assert [x.key for x in a.rating.areas] == [
        "coverage",
        "defence",
        "speed",
        "roles",
        "sets",
        "roster",
    ]
    assert a.profile.gist and a.profile.style
    assert no_llm == []  # no LLM call, even with the provider refusing


async def test_analysis_with_opponent_has_no_rating(session, teams, no_llm) -> None:
    ours, theirs, _ = teams
    a = await team_analysis.analyze(session, ours, theirs)
    assert a.vs_opponent is not None
    assert a.rating is None and a.profile is None


async def test_empty_team_has_no_rating(session, teams) -> None:
    _, _, empty = teams
    a = await team_analysis.analyze(session, empty)
    assert a.rating is None and a.profile is None


async def test_rating_is_the_same_on_every_opponent_free_read(session, teams) -> None:
    ours, theirs, _ = teams
    first = await team_analysis.analyze(session, ours)
    await team_analysis.analyze(session, ours, theirs)  # an opponent in between changes nothing
    again = await team_analysis.analyze(session, ours)
    assert first.rating == again.rating and first.profile == again.profile
