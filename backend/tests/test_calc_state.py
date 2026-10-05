"""Calculator state → damage-maths inputs, resolved from the DB (needs the Compose DB)."""

from __future__ import annotations

from app.schemas.calc import CalcAskRequest
from app.services.calc_state import resolve_state


def _req(**kw) -> CalcAskRequest:
    base = {
        "question": "q",
        "slots": [
            {"slot": 0, "pokemon_id": 445, "name": "Fake", "nature": "Jolly",
             "evs": {"atk": 252, "spe": 252}, "item": "Life Orb", "move": "earthquake"},
            {"slot": 2, "pokemon_id": 373, "move": "Dragon Claw", "hp": 80},
        ],
    }
    return CalcAskRequest(**{**base, **kw})


async def test_resolves_species_stats_and_moves(session) -> None:
    st = await resolve_state(session, _req())
    g, s = st.by_slot(0), st.by_slot(2)
    assert g.name == "Garchomp" and g.mon.types == ["dragon", "ground"]  # client name ignored
    assert g.mon.stats["attack"] == 130 and g.set.ev["atk"] == 252 and g.set.ev["hp"] == 0
    assert g.move.name == "Earthquake" and g.move.type == "ground" and g.move.power == 100
    assert s.side == 1 and s.set.hp == 80 and st.foes_of(g) == [s]


async def test_resolves_forms(session) -> None:
    st = await resolve_state(session, _req(slots=[
        {"slot": 0, "pokemon_id": 445, "form_id": 10058, "move": "Dragon Claw"}]))
    m = st.by_slot(0)
    assert m.name == "Mega Garchomp" and m.form_id == 10058 and m.mon.stats["attack"] == 170
