"""What a member's *set* adds on top of species + typing: held item, ability and
set moves (setup, priority, recovery…). A dependency-free leaf shared by the
one-on-one engine (`battle`) and the team analysis' build profile.

Only effects that can be read deterministically are modelled — no weather,
terrain, switching or prediction. Each table entry carries the short note the UI
shows next to the item/ability so every number stays explainable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def key(name: str | None) -> str | None:
    return name.lower().replace(" ", "-").replace("'", "").replace("’", "") if name else None


# ── items ────────────────────────────────────────────────────────────────────
# Stat multipliers (applied to the final stat).
ITEM_STAT: dict[str, dict[str, float]] = {
    "choice-band": {"attack": 1.5},
    "choice-specs": {"sp_attack": 1.5},
    "choice-scarf": {"speed": 1.5},
    "assault-vest": {"sp_defense": 1.5},
    "iron-ball": {"speed": 0.5},
}
# Damage multipliers on every damaging move.
ITEM_DAMAGE = {"life-orb": 1.3}
ITEM_CLASS_DAMAGE = {"muscle-band": ("physical", 1.1), "wise-glasses": ("special", 1.1)}
EXPERT_BELT = 1.2  # super-effective hits only
# Type-boosting held items (incl. plates): ×1.2 to that type's moves.
TYPE_BOOST_ITEMS: dict[str, str] = {
    "silk-scarf": "normal", "charcoal": "fire", "flame-plate": "fire",
    "mystic-water": "water", "splash-plate": "water", "magnet": "electric",
    "zap-plate": "electric", "miracle-seed": "grass", "meadow-plate": "grass",
    "never-melt-ice": "ice", "icicle-plate": "ice", "black-belt": "fighting",
    "fist-plate": "fighting", "poison-barb": "poison", "toxic-plate": "poison",
    "soft-sand": "ground", "earth-plate": "ground", "sharp-beak": "flying",
    "sky-plate": "flying", "twisted-spoon": "psychic", "mind-plate": "psychic",
    "silver-powder": "bug", "insect-plate": "bug", "hard-stone": "rock",
    "stone-plate": "rock", "spell-tag": "ghost", "spooky-plate": "ghost",
    "dragon-fang": "dragon", "draco-plate": "dragon", "black-glasses": "dark",
    "dread-plate": "dark", "metal-coat": "steel", "iron-plate": "steel",
    "fairy-feather": "fairy", "pixie-plate": "fairy",
}
LEFTOVERS_HEAL = 6.25  # % max HP per turn
LIFE_ORB_RECOIL = 10.0  # % max HP per damaging hit
SITRUS_HEAL = 25.0  # once, at ≤ 50%

ITEM_NOTES: dict[str, str] = {
    "choice-band": "×1.5 Attack (locked into one move)",
    "choice-specs": "×1.5 Sp. Atk (locked into one move)",
    "choice-scarf": "×1.5 Speed (locked into one move)",
    "life-orb": "×1.3 damage, 10% recoil per hit",
    "expert-belt": "×1.2 on super-effective hits",
    "muscle-band": "×1.1 physical damage",
    "wise-glasses": "×1.1 special damage",
    "assault-vest": "×1.5 Sp. Def (attacks only)",
    "focus-sash": "survives one KO hit from full HP",
    "leftovers": "heals 6.25% every turn",
    "black-sludge": "heals 6.25% every turn (Poison types)",
    "sitrus-berry": "heals 25% once at half HP",
    "iron-ball": "halves Speed",
}


def item_note(item: str | None) -> str | None:
    if not item:
        return None
    if item in ITEM_NOTES:
        return ITEM_NOTES[item]
    if item in TYPE_BOOST_ITEMS:
        return f"×1.2 {TYPE_BOOST_ITEMS[item].title()} moves"
    return None


# ── abilities ────────────────────────────────────────────────────────────────
# Modelled in the one-on-one (battle.duel / damage maths). Immunity abilities are
# in battle.ABILITY_DEFENSE and noted here for the UI.
ABILITY_NOTES: dict[str, str] = {
    "speed-boost": "+1 Speed at the end of every turn",
    "intimidate": "lowers the foe's Attack by 1 on entry",
    "huge-power": "doubles Attack",
    "pure-power": "doubles Attack",
    "adaptability": "STAB ×2 instead of ×1.5",
    "technician": "×1.5 on moves of 60 power or less",
    "sturdy": "survives one KO hit from full HP",
    "multiscale": "halves damage taken at full HP",
    "shadow-shield": "halves damage taken at full HP",
    "filter": "super-effective hits ×0.75",
    "solid-rock": "super-effective hits ×0.75",
    "prism-armor": "super-effective hits ×0.75",
    "wonder-guard": "only super-effective hits land",
    "levitate": "immune to Ground",
    "earth-eater": "immune to Ground",
    "flash-fire": "immune to Fire",
    "well-baked-body": "immune to Fire",
    "water-absorb": "immune to Water",
    "storm-drain": "immune to Water",
    "dry-skin": "immune to Water, weaker to Fire",
    "volt-absorb": "immune to Electric",
    "lightning-rod": "immune to Electric",
    "motor-drive": "immune to Electric",
    "sap-sipper": "immune to Grass",
    "thick-fat": "halves Fire and Ice damage",
    "heatproof": "halves Fire damage",
    "water-bubble": "halves Fire damage",
    "purifying-salt": "halves Ghost damage",
    "fluffy": "halves contact damage, weaker to Fire",
    "regenerator": "heals on switching out",
    "moxie": "+1 Attack after each KO",
    "beast-boost": "+1 best stat after each KO",
}

# ── set moves ────────────────────────────────────────────────────────────────
# Stat stages a setup move grants (used once in a one-on-one before attacking).
SETUP_BOOSTS: dict[str, dict[str, int]] = {
    "swords-dance": {"attack": 2},
    "dragon-dance": {"attack": 1, "speed": 1},
    "nasty-plot": {"sp_attack": 2},
    "calm-mind": {"sp_attack": 1, "sp_defense": 1},
    "quiver-dance": {"sp_attack": 1, "sp_defense": 1, "speed": 1},
    "bulk-up": {"attack": 1, "defense": 1},
    "shell-smash": {"attack": 2, "sp_attack": 2, "speed": 2, "defense": -1, "sp_defense": -1},
    "shift-gear": {"attack": 1, "speed": 2},
    "coil": {"attack": 1, "defense": 1},
    "hone-claws": {"attack": 1},
    "work-up": {"attack": 1, "sp_attack": 1},
    "growth": {"attack": 1, "sp_attack": 1},
    "howl": {"attack": 1},
    "tail-glow": {"sp_attack": 3},
    "agility": {"speed": 2},
    "rock-polish": {"speed": 2},
    "autotomize": {"speed": 2},
    "victory-dance": {"attack": 1, "defense": 1, "speed": 1},
    "tidy-up": {"attack": 1, "speed": 1},
    "no-retreat": {"attack": 1, "defense": 1, "sp_attack": 1, "sp_defense": 1, "speed": 1},
    "clangorous-soul": {"attack": 1, "defense": 1, "sp_attack": 1, "sp_defense": 1, "speed": 1},
    "curse": {"attack": 1, "defense": 1, "speed": -1},
    "belly-drum": {"attack": 6},
    "iron-defense": {"defense": 2},
    "acid-armor": {"defense": 2},
    "amnesia": {"sp_defense": 2},
    "cosmic-power": {"defense": 1, "sp_defense": 1},
}
RECOVERY_MOVES = {
    "recover", "roost", "soft-boiled", "milk-drink", "slack-off", "moonlight",
    "morning-sun", "synthesis", "shore-up", "strength-sap", "heal-order", "wish",
}
SUPPORT_MOVES = {
    "stealth-rock", "spikes", "toxic-spikes", "sticky-web", "reflect", "light-screen",
    "aurora-veil", "u-turn", "volt-switch", "flip-turn", "parting-shot", "teleport",
    "thunder-wave", "will-o-wisp", "toxic", "spore", "sleep-powder", "yawn", "taunt",
    "encore", "trick", "knock-off", "rapid-spin", "defog", "tailwind", "trick-room",
    "protect", "substitute", "haze", "whirlwind", "roar", "leech-seed",
}


@dataclass(frozen=True)
class Setup:
    name: str
    boosts: dict[str, int] = field(default_factory=dict)


def best_setup(moves: list[tuple[str, str]], physical: bool) -> Setup | None:
    """The set setup move that helps this attacker most: (display name, key) pairs in."""
    best: tuple[float, Setup] | None = None
    for name, k in moves:
        b = SETUP_BOOSTS.get(k)
        if not b:
            continue
        atk = b.get("attack" if physical else "sp_attack", 0)
        value = 2 * atk + b.get("speed", 0) + 0.5 * (b.get("defense", 0) + b.get("sp_defense", 0))
        if value > 0 and (best is None or value > best[0]):
            best = (value, Setup(name=name, boosts=b))
    return best[1] if best else None


def stage_mult(stage: int) -> float:
    s = max(-6, min(6, stage))
    return (2 + s) / 2 if s >= 0 else 2 / (2 - s)
