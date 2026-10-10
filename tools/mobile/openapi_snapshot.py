"""The slice of the backend's OpenAPI schema the mobile app is generated from.

Keeps only the paths the app calls (PATHS) and the component schemas they reference,
transitively, so the snapshot (``mobile/openapi.json``) and the generated Dart client
change only when something the app uses changes. ``backend/tests/test_mobile_openapi.py``
compares the committed snapshot with the live schema through ``snapshot()``.

    cd backend && uv run python ../tools/mobile/openapi_snapshot.py ../mobile/openapi.json
    (or: make mobile-api)
"""

from __future__ import annotations

import json
import sys

# Every endpoint the app calls. Add one here, then run `make mobile-api`.
PATHS = [
    "/health",
    "/api/pokemon",
    "/api/pokemon/{id_or_name}",
    "/api/types",
    "/api/types/chart",
    "/api/generations",
    "/api/pokemon/{pokemon_id}/moves/by-game",
    "/api/moves/{move_id}/learners/by-game",
    "/api/pokemon/{pokemon_id}/encounters",
    "/api/profile",
    "/api/profile/favorites/{pokemon_id}",
    # Teams (phase 3)
    "/api/teams",
    "/api/teams/{team_id}",
    "/api/teams/{team_id}/slots/{slot}",
    "/api/teams/{team_id}/slots/{slot}/build",
    "/api/teams/{team_id}/analysis",
    "/api/teams/{team_id}/strategy",
    "/api/teams/{team_id}/summary",
    "/api/teams/{team_id}/summary/refresh",
    "/api/teams/{team_id}/ask",
    "/api/pokemon/{pokemon_id}/moves",
    "/api/pokemon/forms/{form_id}/moves",
    "/api/pokemon/{pokemon_id}/abilities",
    "/api/items",
    "/api/natures",
    # Tools tab
    "/api/pokemon/{pokemon_id}/catch",
    "/api/moves",
    "/api/abilities",
    "/api/abilities/{ability_id}/pokemon",
    # Ask (phase 4): the answer's typed views and sources; the app reads the SSE twin.
    "/api/ask",
    "/api/ask/status",
]


def _refs(node) -> set[str]:
    if isinstance(node, dict):
        out = {node["$ref"].rsplit("/", 1)[-1]} if isinstance(node.get("$ref"), str) else set()
        for v in node.values():
            out |= _refs(v)
        return out
    if isinstance(node, list):
        return set().union(*(_refs(v) for v in node)) if node else set()
    return set()


def snapshot(schema: dict) -> dict:
    """The app's slice of a full OpenAPI schema: PATHS plus every schema they reach."""
    paths = {p: schema["paths"][p] for p in PATHS}
    all_schemas = schema.get("components", {}).get("schemas", {})
    keep: set[str] = set()
    todo = _refs(paths)
    while todo:
        name = todo.pop()
        if name in keep:
            continue
        keep.add(name)
        todo |= _refs(all_schemas[name]) - keep
    return {
        "openapi": schema["openapi"],
        "info": schema["info"],
        "paths": paths,
        "components": {"schemas": {k: all_schemas[k] for k in sorted(keep)}},
    }


if __name__ == "__main__":
    import os

    sys.path.insert(0, os.getcwd())  # run from backend/ so the app package imports
    from app.main import app

    out = sys.argv[1] if len(sys.argv) > 1 else "../mobile/openapi.json"
    with open(out, "w") as f:
        json.dump(snapshot(app.openapi()), f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print(f"wrote {out}")
