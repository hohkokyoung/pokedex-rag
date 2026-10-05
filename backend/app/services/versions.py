"""Game version → generation mapping (dep-free leaf).

Pokédex flavor (dex entry) rows carry the English *game version* they came from
("Red", "Sword", "Scarlet: The Teal Mask", …) but not a generation. That mapping
is a fixed historical fact, so rather than widen the schema and force a re-ingest we
resolve it here at read time. The table is derived from the PokéAPI CSVs
(versions → version_groups.generation_id); regenerate it from those if PokéAPI ever
adds a game.
"""

from __future__ import annotations

# English version name -> generation number. Kept grouped by generation for legibility.
VERSION_TO_GEN: dict[str, int] = {
    # Gen I
    "Red": 1, "Green": 1, "Blue": 1, "Yellow": 1,
    # Gen II
    "Gold": 2, "Silver": 2, "Crystal": 2,
    # Gen III
    "Ruby": 3, "Sapphire": 3, "Emerald": 3, "FireRed": 3, "LeafGreen": 3,
    "Colosseum": 3, "XD": 3,
    # Gen IV
    "Diamond": 4, "Pearl": 4, "Platinum": 4, "HeartGold": 4, "SoulSilver": 4,
    # Gen V
    "Black": 5, "White": 5, "Black 2": 5, "White 2": 5,
    # Gen VI
    "X": 6, "Y": 6, "Omega Ruby": 6, "Alpha Sapphire": 6,
    # Gen VII
    "Sun": 7, "Moon": 7, "Ultra Sun": 7, "Ultra Moon": 7,
    "Let’s Go, Pikachu!": 7, "Let’s Go, Eevee!": 7,
    # Gen VIII
    "Sword": 8, "Shield": 8,
    "Sword: The Isle of Armor": 8, "Shield: The Isle of Armor": 8,
    "Sword: The Crown Tundra": 8, "Shield: The Crown Tundra": 8,
    "Brilliant Diamond": 8, "Shining Pearl": 8, "Legends: Arceus": 8,
    # Gen IX
    "Scarlet": 9, "Violet": 9,
    "Scarlet: The Teal Mask": 9, "Violet: The Teal Mask": 9,
    "Scarlet: The Indigo Disk": 9, "Violet: The Indigo Disk": 9,
    "Legends: Z-A": 9, "Mega Dimension": 9, "Champions": 9,
}

_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX"}


def generation_for_version(version: str | None) -> int | None:
    """Generation number for a stored game-version name, or None if unknown."""
    if not version:
        return None
    return VERSION_TO_GEN.get(version.strip())


def gen_label(generation: int | None) -> str | None:
    """Human label for a generation number, e.g. 5 -> 'Gen V'. None if unknown."""
    if generation is None:
        return None
    return f"Gen {_ROMAN.get(generation, str(generation))}"
