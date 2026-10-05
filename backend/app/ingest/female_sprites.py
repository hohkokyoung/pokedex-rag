"""Download female artwork for species with visual gender differences and record it.

``pokemon_species.has_gender_differences`` flags ~100 species whose female looks
different (Pyroar's mane, Unfezant's plumage, Pikachu's heart-shaped tail). Species
whose female is its own ``pokemon`` record (Meowstic, Indeedee, Basculegion,
Oinkologne) already appear in the form switcher and are skipped.

Only official artwork ``<id>-female.png`` is used (upstream: Frillish, Jellicent,
Pyroar). Other art styles (e.g. Pokémon HOME renders) clash with the official male
art beside them, so species without an official female simply get no toggle.

Each is saved to ``data/sprites/female/<pokemon_id>.png``, then
``pokemon.female_sprite_path`` is set for every file on disk (and cleared for the
rest). Idempotent: existing files are skipped (delete ``data/sprites/female`` to
refetch). Run on the host: ``uv run python -m app.ingest.female_sprites``.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ingest.csv_source import read_csv, to_int
from app.ingest.run import _sync_engine
from app.models import Pokemon

_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other"


def female_sprite_path(pokemon_id: int) -> str:
    return f"female/{pokemon_id}.png"


def _gendered_pokemon_ids() -> list[int]:
    """Default pokemon ids of species with a cosmetic (same-record) female look."""
    gendered = {
        int(r["id"]) for r in read_csv("pokemon_species") if r.get("has_gender_differences") == "1"
    }
    rows = list(read_csv("pokemon"))
    separate_female = {to_int(r["species_id"]) for r in rows if r["identifier"].endswith("-female")}
    return sorted(
        int(r["id"])
        for r in rows
        if r.get("is_default") == "1"
        and to_int(r["species_id"]) in gendered - separate_female
    )


def _fetch(pid: int, sprites_dir: Path) -> str:
    dest = sprites_dir / female_sprite_path(pid)
    if dest.exists():
        return "skip"
    try:
        with urllib.request.urlopen(
            f"{_BASE}/official-artwork/{pid}-female.png", timeout=30
        ) as resp:
            dest.write_bytes(resp.read())
        return "ok"
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    return "miss"


def main() -> None:
    sprites_dir = Path(get_settings().sprites_dir)
    (sprites_dir / "female").mkdir(parents=True, exist_ok=True)
    ids = _gendered_pokemon_ids()
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda pid: _fetch(pid, sprites_dir), ids))

    on_disk = [pid for pid in ids if (sprites_dir / female_sprite_path(pid)).exists()]
    with Session(_sync_engine()) as session:
        session.execute(update(Pokemon).values(female_sprite_path=None))
        for pid in on_disk:
            session.execute(
                update(Pokemon)
                .where(Pokemon.id == pid)
                .values(female_sprite_path=female_sprite_path(pid))
            )
        session.commit()

    counts = {k: results.count(k) for k in ("ok", "skip", "miss")}
    print(
        f"Female artwork: {counts['ok']} downloaded, {counts['skip']} already present, "
        f"{counts['miss']} without official art; {len(on_disk)} species recorded."
    )


if __name__ == "__main__":
    main()
