"""Pure tests for validating a coach-suggested build (no LLM, no DB)."""

from __future__ import annotations

from app.rag.build_suggest import clamp_evs, validate


def test_clamp_evs_caps_and_fits_total() -> None:
    evs = clamp_evs({"hp": 300, "atk": 252, "def": 7, "spa": 0, "spd": 0, "spe": 252})
    assert all(0 <= v <= 252 and v % 4 == 0 for v in evs.values())
    assert sum(evs.values()) <= 510


def test_clamp_evs_bad_input() -> None:
    assert clamp_evs({"hp": "x"}) == {k: 0 for k in ("hp", "atk", "def", "spa", "spd", "spe")}
    assert sum(clamp_evs(None).values()) == 0


def test_validate_drops_invented_options() -> None:
    out = validate(
        {
            "moves": ["earthquake", "Outrage", "Hyper Beam Ultra", "Earthquake", "Swords Dance"],
            "ability": "rough skin",
            "nature": "Jolly",
            "item": "Mystery Orb",
            "evs": {"atk": 252, "spe": 252, "hp": 4},
            "why": "Fast physical sweeper.",
        },
        pokemon="Garchomp",
        moves=["Earthquake", "Outrage", "Swords Dance", "Stone Edge"],
        abilities=["Sand Veil", "Rough Skin"],
        natures=["Jolly", "Adamant"],
        items=["Life Orb", "Choice Scarf"],
    )
    assert out.moves == ["Earthquake", "Outrage", "Swords Dance"]  # invented + dupe dropped
    assert out.ability == "Rough Skin"
    assert out.nature == "Jolly"
    assert out.item is None
    assert out.evs["atk"] == 252 and out.evs["spe"] == 252 and out.evs["hp"] == 4


def test_follow_up_block_carries_set_history_and_request() -> None:
    from app.rag.build_suggest import BuildSuggestion, CoachTurn, _follow_up_block

    cur = BuildSuggestion(
        pokemon="Garchomp",
        moves=["Earthquake", "Outrage"],
        ability="Rough Skin",
        nature="Jolly",
        item="Choice Scarf",
        evs={"hp": 4, "atk": 252, "def": 0, "spa": 0, "spd": 0, "spe": 252},
    )
    block = _follow_up_block(cur, "make it bulkier", [CoachTurn(ask="why scarf?", reply="Speed.")])
    assert "Earthquake, Outrage" in block and "Choice Scarf" in block
    assert "User: why scarf?" in block and "Coach: Speed." in block
    assert block.rstrip().endswith("Follow-up: make it bulkier")


async def test_single_attempt_counts_usage(session, monkeypatch) -> None:
    """The agent's set-edit tool calls the build coach once and counts the tokens."""
    import json

    import pytest

    from app.core.config import Settings
    from app.rag import answer as answer_service
    from app.rag import build_suggest

    monkeypatch.setattr(build_suggest, "get_settings",
                        lambda: Settings(anthropic_api_key="", groq_api_key="g"))
    calls: list[dict] = []

    async def fake(system, user, *, usage=None, **kw):
        calls.append(kw)
        if usage is not None:
            usage.add(900, 120)
        raise RuntimeError("provider down")

    monkeypatch.setattr(answer_service, "quick_complete", fake)
    usage = answer_service.Usage()
    with pytest.raises(build_suggest.SuggestError):
        await build_suggest.suggest_build(session, 445, attempts=1, usage=usage)
    assert len(calls) == 1 and calls[0]["max_tokens"] == 2400 and calls[0]["retry"] is False
    assert usage.as_dict() == {"llm_calls": 1, "input_tokens": 900, "output_tokens": 120}

    good = {"moves": ["Earthquake", "Dragon Claw", "Swords Dance", "Fire Fang"],
            "ability": "Rough Skin", "nature": "Jolly", "item": "Life Orb",
            "evs": {"hp": 4, "atk": 252, "def": 0, "spa": 0, "spd": 0, "spe": 252},
            "why": "Fast physical sweeper."}

    async def ok(system, user, *, usage=None, **kw):
        return json.dumps(good)

    monkeypatch.setattr(answer_service, "quick_complete", ok)
    out = await build_suggest.suggest_build(session, 445, attempts=1)
    assert out.moves[0] == "Earthquake" and out.nature == "Jolly"
