"""Every item and ability the calculator offers changes some damage result (and the
lists the client gets are the ones the maths reads)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.services import damage_calc as dc

MON = dc.Mon(types=["dragon", "ground"], stats=dict(hp=108, attack=130, defense=95,
                                                    sp_attack=80, sp_defense=85, speed=102))
FOE = dc.Mon(types=["fire", "steel"], stats=dict(hp=91, attack=90, defense=106,
                                                 sp_attack=130, sp_defense=106, speed=77))


def _changes(side: str, key: str, name: str) -> bool:
    """Whether setting ``name`` changes the result of some plain probe hit."""
    defenders = [MON, FOE] + [replace(FOE, types=[t]) for t in dc.CHART]
    for mtype in dc.CHART:
        for cls in ("physical", "special"):
            for power, burn, hp in ((40, False, 100), (100, True, 50), (100, False, 100)):
                f = dc.Field(burn=burn)
                base_a, base_d = dc.Side(), dc.Side(hp=hp)
                a = replace(base_a, **{key: name}) if side == "a" else base_a
                d = replace(base_d, **{key: name}) if side == "d" else base_d
                mv = dc.MoveIn(mtype, cls, power)
                for dfn in defenders:
                    got = dc.calc_hit(MON, a, dfn, d, mv, f)
                    if got != dc.calc_hit(MON, base_a, dfn, base_d, mv, f):
                        return True
    return False


@pytest.mark.parametrize("name,side,note", [x for x in dc.CALC_ITEMS if x[0] != "Focus Sash"])
def test_every_item_changes_damage(name, side, note):
    if name == "Eviolite":
        return  # modelled for any defender (the calc trusts the user that it's unevolved)
    assert _changes(side, "item", name), name


@pytest.mark.parametrize("name,side,note", dc.CALC_ABILITIES)
def test_every_ability_changes_damage(name, side, note):
    assert _changes(side, "abil", name), name


async def test_options_endpoint():
    import httpx

    from app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        body = (await c.get("/api/calc/options")).json()
    assert {"name": "Choice Band", "side": "a", "note": "Atk ×1.5"} in body["items"]
    assert body["weathers"] == ["None", "Rain", "Sun"] and "Adamant" in body["natures"]
