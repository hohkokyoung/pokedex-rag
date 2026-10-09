"""The mobile app's committed API snapshot matches the live schema for every endpoint it
calls. When this fails, a backend change touched something the app uses: run
`make mobile-api` to regenerate the snapshot and the app's Dart client, then fix the app.

Runs on the host (the backend container only mounts ``backend/``), so it skips when the
repo's ``mobile/`` and ``tools/`` aren't there."""

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "mobile" / "openapi.json"
TOOL = REPO / "tools" / "mobile" / "openapi_snapshot.py"

pytestmark = pytest.mark.skipif(
    not (SNAPSHOT.is_file() and TOOL.is_file()), reason="mobile/ or tools/ not mounted"
)


def test_mobile_snapshot_is_current():
    from app.main import app

    spec = importlib.util.spec_from_file_location("openapi_snapshot", TOOL)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    live = json.loads(json.dumps(tool.snapshot(app.openapi())))
    committed = json.loads(SNAPSHOT.read_text())
    assert committed == live, "mobile/openapi.json is stale: run `make mobile-api`"
