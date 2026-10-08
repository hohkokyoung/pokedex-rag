"""Sprites are large, never-changing files: the static mount must let browsers cache them."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.static import CachedStaticFiles


def _client(tmp_path) -> TestClient:
    (tmp_path / "official-artwork").mkdir()
    (tmp_path / "official-artwork" / "6.png").write_bytes(b"\x89PNG fake")
    app = FastAPI()
    app.mount("/sprites", CachedStaticFiles(directory=tmp_path), name="sprites")
    return TestClient(app)


def test_sprite_responses_are_cacheable(tmp_path):
    res = _client(tmp_path).get("/sprites/official-artwork/6.png")
    assert res.status_code == 200
    cache = res.headers.get("cache-control", "")
    assert "public" in cache
    assert "max-age=" in cache and int(cache.split("max-age=")[1].split(",")[0]) >= 86400


def test_missing_sprite_is_not_cached(tmp_path):
    res = _client(tmp_path).get("/sprites/official-artwork/99999.png")
    assert res.status_code == 404
    assert "max-age" not in res.headers.get("cache-control", "")
