"""Where to find a Pokémon (the Pokédex detail page's encounter section)."""

from __future__ import annotations

from app.ingest.encounters import _area_label
from app.services.encounters import encounters_by_game


def test_area_label() -> None:
    prose = "Road 204 (south, towards Jubilife City)"
    assert _area_label("south-towards-jubilife-city", prose) == "South, towards Jubilife City"
    assert _area_label("b1f", None) == "B1F"
    assert _area_label("", "Canalave City") is None


async def test_defaults_to_newest_game(session) -> None:
    out = await encounters_by_game(session, 163)  # Hoothoot
    gens = [g.generation for g in out.games]
    assert gens == sorted(gens)
    assert out.version_id == out.games[-1].version_id
    assert out.encounters


async def test_one_game_folds_slots_and_conditions(session) -> None:
    out = await encounters_by_game(session, 163)
    hg = next(g.version_id for g in out.games if g.version == "HeartGold")
    rows = (await encounters_by_game(session, 163, hg)).encounters
    route29 = [r for r in rows if r.location == "Route 29" and r.method == "walk"]
    assert route29 and all(r.conditions == "At night" for r in route29)
    assert all(r.chance is None or 0 < r.chance <= 100 for r in rows)


async def test_regional_form_has_its_own_places(session) -> None:
    alolan = await encounters_by_game(session, 10091)  # Alolan Rattata
    assert {g.generation for g in alolan.games} == {7}
    assert (await encounters_by_game(session, 10033)).games == []  # Mega Venusaur


async def test_unknown_game_falls_back(session) -> None:
    out = await encounters_by_game(session, 163, 99999)
    assert out.version_id == out.games[-1].version_id


def test_condition_text() -> None:
    from app.ingest.encounters import _condition_text

    weather = {i: f"weather-{w}" for i, w in enumerate(
        ["normal", "overcast", "raining", "thunderstorm", "snowing", "snowstorm",
         "sandstorm", "intense-sun", "fog"])}
    values = {i: (28, "") for i in weather}
    every = set(weather)
    assert _condition_text({3}, every, weather, values) == "Thunderstorm"
    four = "Clear, overcast, rain or thunderstorm"
    assert _condition_text({0, 1, 2, 3}, every, weather, values) == four
    no_snow = "Any weather but snow or snowstorm"
    assert _condition_text(every - {4, 5}, every, weather, values) == no_snow
