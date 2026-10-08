"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import ask, builder, calc, health, pokemon, profile, teams, traces
from app.core.config import get_settings
from app.core.static import CachedStaticFiles

settings = get_settings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pokedex")

app = FastAPI(
    title="pokérag API",
    version="0.1.0",
    description="Backend for the premium Pokédex + personalized RAG project.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Lightweight observability: log method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    if not request.url.path.startswith("/sprites"):
        logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path,
                    response.status_code, elapsed_ms)
    return response

app.include_router(health.router)
app.include_router(pokemon.router)
app.include_router(ask.router)
app.include_router(profile.router)
app.include_router(builder.router)
app.include_router(teams.router)
app.include_router(calc.router)
app.include_router(traces.router)


@app.get("/api/ask/status", tags=["ask"])
async def ask_status() -> dict[str, object]:
    """Whether the RAG assistant is configured, and which provider is active."""
    return {"enabled": settings.llm_enabled, "provider": settings.llm_provider}

# Serve downloaded Pokémon sprites as static files (e.g. /sprites/official-artwork/1.png),
# browser-cacheable: they only change when `make sprites` is re-run.
if os.path.isdir(settings.sprites_dir):
    app.mount("/sprites", CachedStaticFiles(directory=settings.sprites_dir), name="sprites")


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"name": "pokérag API", "version": "0.1.0", "docs": "/docs"}
