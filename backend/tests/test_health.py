"""Tests for the health endpoints.

The liveness endpoint needs no database. The readiness endpoint depends on the
DB session; here we override that dependency so the test runs without Postgres.
"""

from __future__ import annotations

import httpx
import pytest

from app.core.database import get_session
from app.main import app


@pytest.fixture
def client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_liveness(client: httpx.AsyncClient) -> None:
    async with client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_root(client: httpx.AsyncClient) -> None:
    async with client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["name"] == "pokérag API"


async def test_readiness_reports_db_down_on_failure(client: httpx.AsyncClient) -> None:
    """With a session that raises on use, readiness should report degraded."""

    class _BrokenSession:
        async def execute(self, *_args, **_kwargs):
            raise RuntimeError("no database")

    async def _override():
        yield _BrokenSession()

    app.dependency_overrides[get_session] = _override
    try:
        async with client:
            resp = await client.get("/health/ready")
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert resp.status_code == 200
    assert resp.json() == {"status": "degraded", "database": "down"}


def test_slot_routes_registered() -> None:
    """Every slot verb is routed (a regression once dropped DELETE)."""
    from app.api.teams import router

    verbs = {(r.path, m) for r in router.routes for m in getattr(r, "methods", set())}
    slot = next(p for p, _ in verbs if p.endswith("/slots/{slot}"))
    assert (slot, "PUT") in verbs
    assert (slot, "DELETE") in verbs
    assert (slot + "/build", "POST") in verbs
