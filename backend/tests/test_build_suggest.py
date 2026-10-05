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
