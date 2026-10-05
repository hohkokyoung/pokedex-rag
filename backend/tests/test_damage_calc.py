"""The backend port equals the browser calculator on its own reference cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import damage_calc as dc

CASES = json.loads((Path(__file__).parent / "fixtures" / "damage_cases.json").read_text())


def _side(s: dict) -> dc.Side:
    return dc.Side(nat=s["nat"], ev=s["ev"], iv=s["iv"], item=s["item"], abil=s["abil"],
                   hp=s["hp"])


def _field(f: dict) -> dc.Field:
    return dc.Field(level=f["level"], doubles=f["doubles"], spread=f["spread"],
                    weather=f["weather"], terrain=f["terrain"], reflect=f["reflect"],
                    lightscreen=f["lightscreen"], crit=f["crit"], burn=f["burn"],
                    helping_hand=f["helpingHand"], friend_guard=f["friendGuard"])


def test_fixture_is_substantial():
    assert CASES["version"] == 1 and len(CASES["cases"]) >= 250


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda c: c["id"])
def test_matches_the_calculator(case):
    r = dc.calc_hit(
        dc.Mon(**case["atk_mon"]), _side(case["a"]), dc.Mon(**case["def_mon"]), _side(case["d"]),
        dc.MoveIn(**case["move_in"]), _field(case["f"]),
    )
    want = case["result"]
    assert r.min_pct == pytest.approx(want["minPct"], abs=0.01)
    assert r.max_pct == pytest.approx(want["maxPct"], abs=0.01)
    assert (r.ko, r.te, r.stab, r.A, r.D, r.base) == (
        want["ko"], want["te"], want["stab"], want["A"], want["D"], want["base"])


async def test_static_chart_equals_db_chart(session):
    from app.services import matchups

    await matchups._ensure_loaded(session)
    for (atk_id, def_id), factor in matchups._chart.items():
        atk, dfn = matchups._id2ident[atk_id], matchups._id2ident[def_id]
        if atk in dc.CHART and dfn in dc.CHART:
            assert dc.type_eff(atk, dfn) == factor, (atk, dfn)


def test_apply_changes():
    a, d, f = dc.apply_changes(dc.Side(), dc.Side(), dc.Field(), [
        {"who": "attacker", "key": "item", "value": "Choice Band"},
        {"who": "defender", "key": "evs", "value": "252 HP / 4 Def"},
        {"who": "field", "key": "weather", "value": "rain"},
    ])
    assert a.item == "Choice Band" and d.ev["hp"] == 252 and d.ev["def"] == 4
    assert f.weather == "Rain"
    with pytest.raises(dc.ChangeError):
        dc.apply_changes(dc.Side(), dc.Side(), dc.Field(), [{"who": "attacker", "key": "x",
                                                           "value": "1"}])
    with pytest.raises(dc.ChangeError):
        dc.parse_evs("300 Atk")


# ---- survival threshold ----------------------------------------------------------------

GARCHOMP = dc.Mon(["dragon", "ground"], {"hp": 108, "attack": 130, "defense": 95,
                                         "sp_attack": 80, "sp_defense": 85, "speed": 102})
SALAMENCE = dc.Mon(["dragon", "flying"], {"hp": 95, "attack": 135, "defense": 80,
                                          "sp_attack": 110, "sp_defense": 80, "speed": 100})
TYRANITAR = dc.Mon(["rock", "dark"], {"hp": 100, "attack": 134, "defense": 110,
                                      "sp_attack": 95, "sp_defense": 100, "speed": 61})
BRELOOM = dc.Mon(["grass", "fighting"], {"hp": 60, "attack": 130, "defense": 80,
                                         "sp_attack": 60, "sp_defense": 60, "speed": 70})
DRAGON_CLAW = dc.MoveIn("dragon", "physical", 80)
CLOSE_COMBAT = dc.MoveIn("fighting", "physical", 120)
JOLLY_252 = dc.Side(nat="Jolly", ev={**dc.Side().ev, "atk": 252})


def test_survive_minimal_spread():
    import time
    from dataclasses import replace

    t = time.monotonic()
    s = dc.survive(GARCHOMP, JOLLY_252, SALAMENCE, dc.Side(), DRAGON_CLAW, dc.Field())
    assert time.monotonic() - t < 0.1
    assert s.survives and s.current_max_pct >= 100 and s.max_pct < 100
    total = s.hp_ev + s.stat_ev
    # Nothing cheaper survives.
    for hp_ev in range(0, total + 1, 4):
        side = replace(dc.Side(), ev={**dc.Side().ev, "hp": hp_ev, "def": total - 4 - hp_ev})
        if side.ev["def"] < 0:
            continue
        r = dc.calc_hit(GARCHOMP, JOLLY_252, SALAMENCE, side, DRAGON_CLAW, dc.Field())
        assert r.max_pct >= 100


def test_survive_impossible():
    adamant = dc.Side(nat="Adamant", ev={**dc.Side().ev, "atk": 252})
    s = dc.survive(BRELOOM, adamant, TYRANITAR, dc.Side(), CLOSE_COMBAT, dc.Field())
    assert not s.survives and s.max_pct >= 100
    assert s.nature_changed and s.nature == "Impish"  # Tyranitar's SpA is its lower attack
