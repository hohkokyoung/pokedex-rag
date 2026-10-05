"""Signature Z-Moves: which Pokémon can use each, with which crystal and base move.

Z-Moves are never learned — a Pokémon holding the right Z-Crystal turns a move it
knows into one for a turn — so they have no learnset rows. The PokéAPI CSVs don't
link a signature Z-Move to its user (only the crystals' prose mentions it), so this
small table is maintained by hand. Users are PokéAPI pokemon ids: a default species
(id == dex number) or an alternate form (> 10000).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignatureZ:
    users: tuple[int, ...]
    crystal: str
    base_move: str  # move identifier


# The cap Pikachus: Original, Hoenn, Sinnoh, Unova, Kalos, Alola, Partner, World.
_CAP_PIKACHU = (10094, 10095, 10096, 10097, 10098, 10099, 10148, 10160)

SIGNATURE_Z: dict[str, SignatureZ] = {
    "catastropika": SignatureZ((25,), "Pikanium Z", "volt-tackle"),
    "sinister-arrow-raid": SignatureZ((724,), "Decidium Z", "spirit-shackle"),
    "malicious-moonsault": SignatureZ((727,), "Incinium Z", "darkest-lariat"),
    "oceanic-operetta": SignatureZ((730,), "Primarium Z", "sparkling-aria"),
    "guardian-of-alola": SignatureZ((785, 786, 787, 788), "Tapunium Z", "natures-madness"),
    "soul-stealing-7-star-strike": SignatureZ((802,), "Marshadium Z", "spectral-thief"),
    "stoked-sparksurfer": SignatureZ((10100,), "Aloraichium Z", "thunderbolt"),
    "pulverizing-pancake": SignatureZ((143,), "Snorlium Z", "giga-impact"),
    "extreme-evoboost": SignatureZ((133,), "Eevium Z", "last-resort"),
    "genesis-supernova": SignatureZ((151,), "Mewnium Z", "psychic"),
    "10-000-000-volt-thunderbolt": SignatureZ(_CAP_PIKACHU, "Pikashunium Z", "thunderbolt"),
    # Dusk Mane / Dawn Wings Necrozma Ultra Burst into Ultra Necrozma with this crystal.
    "light-that-burns-the-sky": SignatureZ((10157,), "Ultranecrozium Z", "photon-geyser"),
    "searing-sunraze-smash": SignatureZ((791, 10155), "Solganium Z", "sunsteel-strike"),
    "menacing-moonraze-maelstrom": SignatureZ((792, 10156), "Lunalium Z", "moongeist-beam"),
    "lets-snuggle-forever": SignatureZ((778,), "Mimikium Z", "play-rough"),
    "splintered-stormshards": SignatureZ((745, 10126, 10152), "Lycanium Z", "stone-edge"),
    "clangorous-soulblaze": SignatureZ((784,), "Kommonium Z", "clanging-scales"),
}
