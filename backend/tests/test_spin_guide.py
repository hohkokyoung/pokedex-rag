"""Spin evolutions carry their spin guide on the detail response (DB-backed)."""

from __future__ import annotations

import pytest

from app.services import pokemon_query


@pytest.mark.parametrize("ident", ["868", "869"])  # Milcery, Alcremie
async def test_spin_chain_has_guide(session, ident: str) -> None:
    detail = await pokemon_query.get_pokemon(session, ident)
    guide = detail.spin_guide
    assert guide is not None
    assert len(guide.steps) == 3
    assert len(guide.toppings) == 7
    assert [c.cream for c in guide.creams][0] == "Vanilla Cream"
    assert [c.cream for c in guide.creams][-1] == "Rainbow Swirl"
    assert len(guide.creams) == 9
    # Every cream and Sweet in Alcremie's 63 variant names has a rule.
    variants = next(m for m in detail.evolution_members if m.name.lower() == "alcremie").variants
    creams = {c.cream for c in guide.creams}
    sweets = {t.sweet for t in guide.toppings}
    for v in variants:
        assert any(v.name.startswith(c) for c in creams), v.name
        assert any(v.name.endswith(s) for s in sweets), v.name


async def test_other_chains_have_no_guide(session) -> None:
    detail = await pokemon_query.get_pokemon(session, "1")  # Bulbasaur
    assert detail.spin_guide is None
    assert all(f.spin_guide is None for f in detail.forms)
