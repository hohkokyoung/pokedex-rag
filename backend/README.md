# Pokédex RAG — Backend

FastAPI + SQLAlchemy (async) + Pydantic backend.

Phase 0 scope: project foundation, config, database connection, and a health endpoint. No RAG or Pokémon data yet.

## Local development (uv)

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

The backend reads configuration from the repository-root `.env` file.
