# Component manifests

One YAML file per component: metadata that connects code to its docs, specs, decisions
and neighbours, so a tool (or Claude Code) can jump from a file path to the right page
without reading everything. They are an index, not documentation — behaviour lives in
the linked pages.

| Field | Holds |
|---|---|
| `name`, `description` | id (matches the file name) and one line |
| `code` | directories or files the component owns (repo-relative) |
| `documentation` | the `docs/` pages that explain it |
| `specs` | the `openspec/specs/` capability that states its rules |
| `decisions` | ADRs in `docs/decisions/` that constrain it |
| `depends_on` | other manifests by `name`, or an external system (`postgres`, `llm`, `pokeapi-csv`) |
| `interfaces` | HTTP endpoints it serves |
| `events` | SSE events it emits (`publishes`) |

Shared code (`app/models/`, `frontend/lib/api.ts`) belongs to no single component.
When a file moves or a component gains a route, update its manifest in the same commit.
`backend/tests/test_docs.py` fails on a path that no longer exists, an unknown
dependency, or a broken link between docs pages.
