"""How Milcery's spin evolution decides Alcremie's look (Pokémon Sword & Shield).

PokéAPI only records the trigger ("spin") and the 63 form names, so these rules are
hand-written game knowledge, keyed by the form-name parts the API returns. Served with
the evolution data of any chain that evolves by spinning.
"""

from __future__ import annotations

from app.schemas.pokemon import CreamRule, EvolutionStage, SpinGuide, SweetTopping

SPIN_STEPS = [
    "Give Milcery a Sweet to hold.",
    "In the overworld, rotate the control stick so your character spins in place.",
    "Stop spinning. Milcery evolves on the spot.",
]

# Sweet held -> the decoration it puts on Alcremie.
SWEET_TOPPING = [
    ("Strawberry Sweet", "Strawberry"),
    ("Berry Sweet", "Berry"),
    ("Love Sweet", "Heart"),
    ("Star Sweet", "Star"),
    ("Clover Sweet", "Clover"),
    ("Flower Sweet", "Flower"),
    ("Ribbon Sweet", "Ribbon"),
]

# Cream -> how to spin for it, in display order. Day/night follows the in-game clock.
CREAM_RULES = [
    ("Vanilla Cream", "Clockwise", "Under 5 s", "Day"),
    ("Ruby Cream", "Counter-clockwise", "Under 5 s", "Day"),
    ("Caramel Swirl", "Clockwise", "Over 5 s", "Day"),
    ("Ruby Swirl", "Counter-clockwise", "Over 5 s", "Day"),
    ("Lemon Cream", "Clockwise", "Under 5 s", "Night"),
    ("Matcha Cream", "Counter-clockwise", "Under 5 s", "Night"),
    ("Mint Cream", "Clockwise", "Over 5 s", "Night"),
    ("Salted Cream", "Counter-clockwise", "Over 5 s", "Night"),
    ("Rainbow Swirl", "Counter-clockwise", "Over 10 s", "7:00–7:59 PM"),
]


def spin_guide_for(stages: list[EvolutionStage]) -> SpinGuide | None:
    """The spin guide when any stage evolves by spinning; None otherwise."""
    if not any(s.trigger == "spin" for s in stages):
        return None
    return SpinGuide(
        steps=SPIN_STEPS,
        toppings=[SweetTopping(sweet=s, topping=t) for s, t in SWEET_TOPPING],
        creams=[
            CreamRule(cream=c, direction=d, duration=dur, time=t) for c, d, dur, t in CREAM_RULES
        ],
    )
