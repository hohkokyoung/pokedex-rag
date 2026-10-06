# Local development

## Run the whole stack

```bash
cp .env.example .env      # then add an LLM key if you want one (optional)
make up                   # docker compose up --build -d
make data                 # first time only: migrate + ingest + sprites + chunks
```

| Service | Default host port | Env var |
|---|---|---|
| Frontend | 3000 | `FRONTEND_HOST_PORT` |
| Backend | 8000 | `BACKEND_HOST_PORT` (also set `NEXT_PUBLIC_API_BASE_URL`) |
| Postgres | 5433 | `POSTGRES_HOST_PORT` |

If a port is taken, change the `*_HOST_PORT` value in `.env`. On the main dev machine
the backend is on **8001** because 8000 is in use. Containers talk to each other on
the internal network (db on 5432) whatever the host ports are.

## LLM keys

Set **one** in `.env`, then restart the backend:

| Provider | Key | Default model (override) |
|---|---|---|
| Anthropic (preferred) | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` |
| Groq (free tier) | `GROQ_API_KEY` | `openai/gpt-oss-120b` (`GROQ_MODEL`) |

Anthropic wins if both are set. `ASK_AGENT_ENABLED=false` turns off LLM planning only
(keyword plans for everything) — the quick switch if planning misbehaves. Keep LLM
work Groq-friendly: the free tier has a tokens-per-minute limit, and a 429 means fall
back, never retry in a loop.

## Iterating

- **Backend:** the container bind-mounts `./backend` and reloads on save.
- **Frontend:** for visual work, stop the Compose `frontend` service and run
  `cd frontend && npm run dev` on the host (port 3000), with
  `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` pointing at the backend.
- **Data scripts** run on the host against the Compose DB (`make` targets set
  `DATABASE_URL` to `localhost:5433`).

## After adding dependencies

Container `node_modules` and `.venv` are anonymous volumes, so a host install doesn't
reach the container.

```bash
docker compose build frontend
```

```bash
docker compose up -d --build --force-recreate --renew-anon-volumes backend
```

The backend needs `--renew-anon-volumes`, or the old `.venv` volume hides the new one.

## Tests and lint

```bash
make test             # backend pytest (needs the Compose DB)
make lint             # ruff + eslint
make damage-fixtures  # after changing frontend/lib/damageCalc.ts (Node ≥ 22.18)
```

Claude Code runs lint and tests itself at the end of any turn that changed code (a Stop
hook — see "Making a change" in `CLAUDE.md`).

Evaluation: [eval.md](eval.md).
