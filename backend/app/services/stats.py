"""Competitive stat maths shared by team hydration and the analysis engine.

Uses the standard Gen-3+ stat formula. Level defaults to 50 (the VGC standard),
IVs default to 31 and EVs to 0 when a slot leaves them unset.
"""

from __future__ import annotations

STAT_KEYS: tuple[str, ...] = ("hp", "attack", "defense", "sp_attack", "sp_defense", "speed")
DEFAULT_LEVEL = 50


def _iv(ivs: dict[str, int] | None, key: str) -> int:
    return (ivs or {}).get(key, 31)


def _ev(evs: dict[str, int] | None, key: str) -> int:
    return (evs or {}).get(key, 0)


def _nature_mod(key: str, increased: str | None, decreased: str | None) -> float:
    if increased == key and decreased != key:
        return 1.1
    if decreased == key and increased != key:
        return 0.9
    return 1.0


def final_stats(
    base: dict[str, int],
    ivs: dict[str, int] | None = None,
    evs: dict[str, int] | None = None,
    increased_stat: str | None = None,
    decreased_stat: str | None = None,
    level: int = DEFAULT_LEVEL,
) -> dict[str, int]:
    """Return computed battle stats for each of the six stats at ``level``."""
    out: dict[str, int] = {}
    for key in STAT_KEYS:
        b = base.get(key, 0)
        iv = _iv(ivs, key)
        ev = _ev(evs, key)
        common = ((2 * b + iv + ev // 4) * level) // 100
        if key == "hp":
            # Shedinja (base HP 1) is always 1 HP, but we don't special-case it here.
            out[key] = common + level + 10
        else:
            mod = _nature_mod(key, increased_stat, decreased_stat)
            out[key] = int((common + 5) * mod)
    return out


def as_built(final: dict[str, int], level: int = DEFAULT_LEVEL) -> dict[str, int]:
    """Base-stat equivalents of a member's real stats (EVs, IVs and nature included).

    Inverts the stat formula for an uninvested, neutral, 31-IV Pokémon, so thresholds
    written in base-stat terms ("base Speed 100+") still mean the same thing while a
    252-EV, +nature spread counts as faster/stronger than the species alone."""
    out: dict[str, int] = {}
    for key in STAT_KEYS:
        v = final.get(key, 0)
        if key == "hp":
            raw = (v - level - 10) * 100 / level  # = 2B + 31 (+EV/4)
        else:
            raw = (v - 5) * 100 / level
        out[key] = max(1, round((raw - 31) / 2))
    return out
