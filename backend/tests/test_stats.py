"""Unit tests for the competitive stat formula (pure, no DB)."""

from __future__ import annotations

from app.services.stats import final_stats

# Pikachu base stats.
PIKACHU = {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90}


def test_neutral_defaults_max_ivs() -> None:
    # No EVs, IV 31, neutral nature, level 50.
    s = final_stats(PIKACHU)
    # HP = floor((2*35+31+0)*50/100)+50+10 = floor(50.5)+60 = 50+60 = 110
    assert s["hp"] == 110
    # Speed = floor((2*90+31)*50/100)+5 = floor(105.5)+5 = 105+5 = 110
    assert s["speed"] == 110


def test_ev_and_nature_boost_speed() -> None:
    s = final_stats(
        PIKACHU,
        evs={"speed": 252, "sp_attack": 252},
        increased_stat="speed",
        decreased_stat="attack",
    )
    # Speed common = floor((2*90+31+63)*50/100) = floor(137) = 137; +5 = 142; *1.1 = 156.2 -> 156
    assert s["speed"] == 156
    # Attack is lowered by nature (0.9); still computed, must be < neutral.
    assert s["attack"] == int((((2 * 55 + 31 + 0) * 50) // 100 + 5) * 0.9)


def test_hp_ignores_nature() -> None:
    boosted = final_stats(PIKACHU, increased_stat="hp", decreased_stat="attack")
    plain = final_stats(PIKACHU)
    assert boosted["hp"] == plain["hp"]  # HP is never nature-modified


def test_as_built_matches_base_when_uninvested_and_rises_with_evs() -> None:
    from app.services.stats import as_built, final_stats

    base = {
        "hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102,
    }
    plain = as_built(final_stats(base))
    assert all(abs(plain[k] - base[k]) <= 1 for k in base)
    evs = {"speed": 252, "attack": 252}
    jolly = as_built(final_stats(base, evs=evs, increased_stat="speed", decreased_stat="sp_attack"))
    assert jolly["speed"] > 140 and jolly["attack"] > 150
    assert jolly["sp_attack"] < base["sp_attack"]
