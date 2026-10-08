"""Static file serving with browser caching for downloaded sprites."""

from __future__ import annotations

import mimetypes
import re

from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

# Artwork only changes when `make sprites` / `make thumbs` is re-run, so a day of
# caching (plus the ETag the base class already sends) stops browsers re-checking
# images on every page. Not `immutable`: file names are stable, so a re-download
# must still win.
SPRITE_CACHE = "public, max-age=86400, stale-while-revalidate=604800"

# Slim container images ship without a .webp entry (served as octet-stream otherwise).
mimetypes.add_type("image/webp", ".webp")

# thumbs/<size>/<path>.webp → <path>.png (see app/ingest/thumbs.py)
_THUMB = re.compile(r"^thumbs/\d+/(?P<rest>.+)\.webp$")


class CachedStaticFiles(StaticFiles):
    """StaticFiles that marks responses cacheable and falls back from a missing
    thumbnail to the full PNG, so thumb URLs work before `make thumbs` has run."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except HTTPException as exc:  # StaticFiles raises (not returns) its 404
            m = _THUMB.match(path.replace("\\", "/"))
            if exc.status_code != 404 or not m:
                raise
            response = await super().get_response(f"{m['rest']}.png", scope)
        if response.status_code in (200, 304):
            response.headers["Cache-Control"] = SPRITE_CACHE
        return response
