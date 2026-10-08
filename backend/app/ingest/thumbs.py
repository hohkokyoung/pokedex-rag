"""Write small WebP copies of the downloaded artwork for list views.

The official artwork is 475×475 PNG (~150 KB each), but lists show it at 26–150px:
a catalog page of 36 cards moved ~5 MB of images. This writes
``data/sprites/thumbs/<size>/<same path>.webp`` for every PNG under ``data/sprites``
(96px for icons and rows, 320px for cards, both 2× their largest display size).
The frontend asks for ``/sprites/thumbs/<size>/…webp``; the backend falls back to
the PNG when a thumb doesn't exist yet (``app/core/static.py``), so this step is
optional and safe to re-run.

Idempotent: a thumb newer than its PNG is skipped. Run on the host after the sprite
targets: ``uv run python -m app.ingest.thumbs`` (``make thumbs``).
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from app.core.config import get_settings

SIZES = (96, 320)
THUMBS_DIR = "thumbs"
QUALITY = 82


def _jobs(root: Path) -> list[tuple[Path, Path, int]]:
    jobs = []
    for png in sorted(root.rglob("*.png")):
        rel = png.relative_to(root)
        if rel.parts[0] == THUMBS_DIR:
            continue
        for size in SIZES:
            out = root / THUMBS_DIR / str(size) / rel.with_suffix(".webp")
            if out.exists() and out.stat().st_mtime >= png.stat().st_mtime:
                continue
            jobs.append((png, out, size))
    return jobs


def _write(job: tuple[Path, Path, int]) -> None:
    png, out, size = job
    out.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(png) as im:
        im = im.convert("RGBA")
        im.thumbnail((size, size), Image.Resampling.LANCZOS)
        im.save(out, "WEBP", quality=QUALITY, method=6)


def build_thumbs(root: Path) -> int:
    """Write any missing or stale thumbs under ``root``; returns how many were written."""
    jobs = _jobs(root)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(_write, jobs))
    return len(jobs)


def main() -> None:
    root = Path(get_settings().sprites_dir)
    if not root.is_dir():
        sys.exit(f"No sprites at {root}; run `make sprites` first.")
    print(f"thumbs: wrote {build_thumbs(root)} file(s) under {root / THUMBS_DIR}")


if __name__ == "__main__":
    main()
