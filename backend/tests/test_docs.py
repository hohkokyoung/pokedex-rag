"""Docs stay wired to the code: every path a component manifest names exists, and every
relative link between docs pages resolves. Runs on the host (the backend container
only mounts ``backend/``), so it skips when the repo's ``docs/`` isn't there."""

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"

pytestmark = pytest.mark.skipif(not DOCS.is_dir(), reason="docs/ not mounted")

REQUIRED = ("name", "description", "code", "documentation")
PATH_FIELDS = ("code", "documentation", "specs", "decisions")
# Systems outside the repo a component may depend on (first word of the entry).
EXTERNAL = {"postgres", "llm", "pokeapi-csv"}
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def _manifests():
    return sorted((DOCS / "components").glob("*.yaml"))


@pytest.mark.parametrize("path", _manifests(), ids=lambda p: p.stem)
def test_manifest_paths_exist(path: Path):
    m = yaml.safe_load(path.read_text())
    missing_keys = [k for k in REQUIRED if not m.get(k)]
    assert not missing_keys, f"{path.name} lacks {missing_keys}"
    assert m["name"] == path.stem, f"{path.name}: name must match the file name"
    missing = [p for f in PATH_FIELDS for p in m.get(f) or [] if not (REPO / p).exists()]
    assert not missing, f"{path.name} names paths that don't exist: {missing}"


def test_manifest_dependencies_are_known():
    known = {p.stem for p in _manifests()} | EXTERNAL
    for path in _manifests():
        for dep in yaml.safe_load(path.read_text()).get("depends_on") or []:
            assert dep.split(" ")[0] in known, f"{path.name}: unknown dependency {dep!r}"


def test_doc_links_resolve():
    broken = []
    for md in [*DOCS.rglob("*.md"), REPO / "CLAUDE.md", REPO / "README.md"]:
        for target in LINK.findall(md.read_text()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (md.parent / target).exists():
                broken.append(f"{md.relative_to(REPO)} → {target}")
    assert not broken, "broken doc links:\n" + "\n".join(broken)
