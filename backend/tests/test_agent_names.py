"""Name resolution for the agent's tools and the keyword planner (needs the DB)."""

from __future__ import annotations

from app.agent import names


async def test_close_match_spelling(session) -> None:
    [m] = await names.resolve(session, "charizrd", ("pokemon",))
    assert (m.kind, m.name, m.exact) == ("pokemon", "Charizard", False)


async def test_exact_is_case_and_punctuation_insensitive(session) -> None:
    [m] = await names.resolve(session, "will o wisp", ("move",))
    assert m.name == "Will-O-Wisp" and m.exact


async def test_psychic_is_a_type_and_a_move(session) -> None:
    kinds = {m.kind for m in await names.resolve(session, "Psychic")}
    assert {"type", "move"} <= kinds


async def test_unknown_name(session) -> None:
    assert await names.resolve(session, "Zorbulax the Unseen", ("pokemon",)) == []


async def test_form_name_resolves(session) -> None:
    [m] = await names.resolve(session, "mega latios", ("form",))
    assert m.kind == "form" and m.id > 10000


async def test_find_in_text_longest_and_multi_kind(session) -> None:
    found = await names.find_in_text(session, "Can Garchomp learn Earthquake?")
    assert [(m.kind, m.name) for m in found] == [("pokemon", "Garchomp"), ("move", "Earthquake")]

    # "Fire Punch" claims its span, so "Fire" (type) isn't also reported.
    found = await names.find_in_text(session, "what does fire punch do", ("move", "type"))
    assert [(m.kind, m.name) for m in found] == [("move", "Fire Punch")]

    kinds = {m.kind for m in await names.find_in_text(session, "Tell me about Psychic")}
    assert {"type", "move"} <= kinds
