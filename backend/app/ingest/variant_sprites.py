"""Download artwork for every cosmetic variant (Alcremie creams, Vivillon patterns…).

Cosmetic forms share their species' ``pokemon`` record, so the per-id official
artwork only shows the default look. PokéAPI also keeps official artwork keyed by
form identifier. Each variant is saved at the path ``forms._cosmetic_variants``
records (``data/sprites/variants/<pokemon_id>-<form>.png``), trying in order:

1. official artwork ``<id>-<form>.png`` (the unnamed default form: ``<id>.png``)
2. official artwork ``<id>.png`` — forms upstream has no separate art for look the
   same in-game (Scatterbug/Spewpa patterns, Mothim cloaks)

Idempotent: files already on disk are skipped (delete ``data/sprites/variants`` to
refetch). Run on the host: ``uv run python -m app.ingest.variant_sprites``.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.core.config import get_settings
from app.ingest.csv_source import read_csv, to_int
from app.ingest.forms import variant_sprite_path

_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other"


def _variant_forms() -> list[tuple[int, str]]:
    """(pokemon_id, form_identifier) for species with >1 cosmetic form."""
    defaults = {
        int(r["id"]) for r in read_csv("pokemon") if r.get("is_default") == "1"
    }
    by_pokemon: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for row in read_csv("pokemon_forms"):
        pid = to_int(row["pokemon_id"])
        if pid not in defaults or row.get("is_battle_only") == "1":
            continue
        by_pokemon[pid].append((pid, row.get("form_identifier") or ""))
    return [f for forms in by_pokemon.values() if len(forms) > 1 for f in forms]


def _candidates(pid: int, ident: str) -> list[str]:
    base = f"{_BASE}/official-artwork"
    return ([f"{base}/{pid}-{ident}.png"] if ident else []) + [f"{base}/{pid}.png"]


def _fetch(form: tuple[int, str], out_dir: Path) -> str:
    pid, ident = form
    dest = out_dir.parent / variant_sprite_path(pid, ident)
    if dest.exists():
        return "skip"
    for url in _candidates(pid, ident):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                dest.write_bytes(resp.read())
            return "ok"
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
    return "miss"


def main() -> None:
    out_dir = Path(get_settings().sprites_dir) / "variants"
    out_dir.mkdir(parents=True, exist_ok=True)
    forms = _variant_forms()
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda f: _fetch(f, out_dir), forms))
    counts = {k: results.count(k) for k in ("ok", "skip", "miss")}
    print(
        f"Variant artwork: {counts['ok']} downloaded, {counts['skip']} already present, "
        f"{counts['miss']} unavailable ({len(forms)} variants)."
    )


if __name__ == "__main__":
    main()
