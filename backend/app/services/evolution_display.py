"""Evolution labels: turns a stage's raw fields (trigger / min_level / item / condition)
into what a client shows: chips (one primary "solid" chip plus any "soft" qualifier
chips joined by "+") and an optional plain-English description behind a "?".

The rule: say each mechanic ONCE. The exact number (happiness ≥ 160, affection ≥ 2, a
set level) lives in the description, never doubled on a chip. A pure level-up shows
just the number.

Ported from the website's ``lib/evolution.ts`` and pinned to its output for every
stage in the data by golden cases (``tests/test_evolution_display.py``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.pokemon import EvolutionChip, EvolutionDisplay, EvolutionStage

_I = re.IGNORECASE


@dataclass
class _Parsed:
    happiness: int | None = None
    affection: int | None = None
    beauty: int | None = None
    time: str | None = None
    held: str | None = None
    location: str | None = None
    move: str | None = None
    party: str | None = None
    gender: str | None = None
    rain: bool = False
    other: list[str] = field(default_factory=list)


def _parse(cond: str | None) -> _Parsed:
    p = _Parsed()
    for raw in (cond or "").split(","):
        t = raw.strip()
        if not t:
            continue
        if m := re.search(r"happiness\s*≥\s*(\d+)", t, _I):
            p.happiness = int(m[1])
        elif m := re.search(r"affection\s*≥\s*(\d+)", t, _I):
            p.affection = int(m[1])
        elif m := re.search(r"beauty\s*≥\s*(\d+)", t, _I):
            p.beauty = int(m[1])
        elif m := re.search(r"^(day|night|dusk)\s*time$", t, _I):
            p.time = m[1].lower()
        elif m := re.search(r"^holding\s+(.+)$", t, _I):
            p.held = m[1]
        elif m := re.search(r"^near\s+(.+)$", t, _I):
            p.location = m[1]
        elif m := re.search(r"^knowing\s+(?:a\s+)?(.+?)(?:-type)?(?:\s+move)?$", t, _I):
            p.move = m[1]
        elif m := re.search(r"^with\s+(.+?)\s+in party$", t, _I):
            p.party = m[1]
        elif m := re.search(r"^\((male|female)\)$", t, _I):
            p.gender = m[1].lower()
        elif re.search(r"rain", t, _I):
            p.rain = True
        else:
            p.other.append(t)
    return p


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _a_or_an(s: str) -> str:
    return "an" if re.match(r"[aeiou]", s, _I) else "a"


def _humanize(s: str) -> str:
    return _cap(s.replace("-", " "))


def evolution_display(stage: EvolutionStage) -> EvolutionDisplay:
    p = _parse(stage.condition)
    trigger = (stage.trigger or "").lower()
    chips: list[EvolutionChip] = []
    desc: list[str] = []

    def chip(label: str, tone: str) -> None:
        chips.append(EvolutionChip(label=label, tone=tone))

    # ---- primary chip ----
    if stage.item:
        item = _cap(stage.item)
        chip(item, "solid")
        desc.append(f"Use {_a_or_an(item)} {item}.")
    elif trigger == "trade":
        chip("Trade", "solid")
        desc.append(
            "Trade this Pokémon. Since Gen VIII (Pokémon Legends: Arceus), a Linking Cord "
            "also evolves it without trading."
        )
    elif p.happiness is not None:
        chip("Friendship", "solid")
        desc.append(
            f"Level up with high friendship (happiness ≥ {p.happiness}) — a bond raised by "
            "travelling and battling together."
        )
    elif p.affection is not None:
        chip("Affection", "solid")
        hearts = "s" if p.affection > 1 else ""
        desc.append(
            f"Level up with high affection (≥ {p.affection} heart{hearts}) from Pokémon Camp care."
        )
    elif p.beauty is not None:
        chip("Beauty", "solid")
        desc.append(f"Level up with high beauty (≥ {p.beauty}).")
    elif trigger == "level-up" and stage.min_level is not None:
        chip(f"Lv. {stage.min_level}", "solid")
        desc.append(f"Reaches level {stage.min_level}.")
    elif trigger == "level-up" or not trigger:
        chip("Level up", "solid")
        desc.append("Level up.")
    else:
        h = _humanize(trigger)
        chip(h, "solid")
        desc.append(f"{h}.")

    # ---- qualifier chips (soft, joined by +) ----
    if p.time:
        chip(_cap(p.time), "soft")
        desc.append(f"During the {p.time}.")
    if p.held:
        chip(p.held, "soft")
        desc.append(f"While holding {_a_or_an(p.held)} {p.held}.")
    if p.move:
        chip(f"{_cap(p.move)} move", "soft")
        desc.append(f"While knowing a {_cap(p.move)}-type move.")
    if p.location:
        chip(p.location, "soft")
        desc.append(f"Near {p.location}.")
    if p.party:
        chip(p.party, "soft")
        desc.append(f"While {p.party} is in your party.")
    if p.gender:
        chip(_cap(p.gender), "soft")
    if p.rain:
        chip("Raining", "soft")
        desc.append("While it's raining.")
    # a set level on top of another condition (rare) — show as a soft chip
    jargon = p.happiness is not None or p.affection is not None or p.beauty is not None
    if stage.min_level is not None and trigger == "level-up" and jargon:
        chip(f"Lv. {stage.min_level}", "soft")
    for o in p.other:
        chip(_cap(o), "soft")

    has_info = len(chips) > 1 or jargon or trigger == "trade"
    return EvolutionDisplay(chips=chips, description=" ".join(desc) if has_info else None)
