"""Small WebP copies of the artwork for list views, and the PNG fallback when one is missing."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.core.static import CachedStaticFiles
from app.ingest.thumbs import SIZES, build_thumbs


def _art(root, rel="official-artwork/6.png", px=475):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))  # artwork sits on a transparent ground
    im.paste((227, 53, 13, 255), (px // 4, px // 4, px * 3 // 4, px * 3 // 4))
    im.save(path)
    return path


def test_builds_each_size_as_webp(tmp_path):
    _art(tmp_path)
    made = build_thumbs(tmp_path)
    assert made == len(SIZES)
    for size in SIZES:
        out = tmp_path / "thumbs" / str(size) / "official-artwork" / "6.webp"
        with Image.open(out) as im:
            assert im.format == "WEBP"
            assert max(im.size) == size
            assert im.mode == "RGBA"  # transparency kept for the card backgrounds


def test_is_idempotent_and_skips_its_own_output(tmp_path):
    _art(tmp_path)
    build_thumbs(tmp_path)
    assert build_thumbs(tmp_path) == 0  # up to date: nothing rewritten, thumbs/ not re-thumbed


def test_thumb_url_falls_back_to_the_png(tmp_path):
    _art(tmp_path, "official-artwork/25.png")
    app = FastAPI()
    app.mount("/sprites", CachedStaticFiles(directory=tmp_path), name="sprites")
    res = TestClient(app).get("/sprites/thumbs/320/official-artwork/25.webp")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert "max-age=" in res.headers.get("cache-control", "")


def test_thumb_url_serves_the_thumb_once_built(tmp_path):
    _art(tmp_path, "official-artwork/25.png")
    build_thumbs(tmp_path)
    app = FastAPI()
    app.mount("/sprites", CachedStaticFiles(directory=tmp_path), name="sprites")
    res = TestClient(app).get("/sprites/thumbs/96/official-artwork/25.webp")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/webp"
