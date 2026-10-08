# Convenience targets for the Pokédex RAG project.
# The data pipeline (migrate/ingest) runs on the host against the Compose DB,
# which is published on host port 5433 (see .env).

DB_URL ?= postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex
BACKEND = cd backend && DATABASE_URL=$(DB_URL)

.PHONY: traces damage-fixtures up down logs migrate ingest items forms learnsets encounters ability-effects move-targets evolutions sprites variant-sprites female-sprites thumbs data test lint

up:            ## Build and start the full stack
	docker compose up --build -d

down:          ## Stop the stack
	docker compose down

logs:          ## Tail all service logs
	docker compose logs -f

migrate:       ## Apply database migrations
	$(BACKEND) uv run alembic upgrade head

ingest:        ## Ingest PokéAPI CSVs into the database
	$(BACKEND) uv run python -m app.ingest.run

items:         ## Ingest items (standalone; safe to run on its own)
	$(BACKEND) uv run python -m app.ingest.items

forms:         ## Ingest alternate forms (standalone; safe to run on its own)
	$(BACKEND) uv run python -m app.ingest.forms

learnsets:     ## Ingest per-game learnsets (standalone; needs pokemon, forms, moves)
	$(BACKEND) uv run python -m app.ingest.learnsets

encounters:    ## Ingest where to find each Pokémon, per game (standalone; needs pokemon, forms)
	$(BACKEND) uv run python -m app.ingest.encounters

ability-effects: ## Backfill abilities.short_effect (standalone; safe to run on its own)
	$(BACKEND) uv run python -m app.ingest.backfill_ability_effects

move-targets:  ## Backfill moves.target (doubles targeting; standalone; safe to run on its own)
	$(BACKEND) uv run python -m app.ingest.backfill_move_targets

flavor:        ## Rebuild dex entries, one per game (standalone; safe to run on its own)
	$(BACKEND) uv run python -m app.ingest.backfill_flavor_texts

evolutions:    ## Rebuild evolution edges (standalone; safe to run on its own)
	$(BACKEND) uv run python -m app.ingest.evolutions

chunks:        ## Build + embed knowledge chunks into pgvector (RAG layer)
	$(BACKEND) uv run python -m app.ingest.build_chunks

sprites:       ## Download official-artwork sprites (default forms + alternate forms)
	mkdir -p data/sprites/official-artwork
	cd data/sprites/official-artwork && seq 1 1025 | xargs -P 24 -I {} \
		curl -sfL -o {}.png \
		"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{}.png"
	@# Alternate-form artwork (regional/Mega/Gmax/battle): ids from the CSV. Some
	@# forms lack official artwork upstream; -f skips those (404) without failing.
	awk -F, 'NR>1 && $$8=="0" && $$3>=1 && $$3<=1025 && $$1>10000 {print $$1}' \
		data/raw/pokeapi/pokemon.csv | \
		xargs -P 24 -I {} curl -sfL -o data/sprites/official-artwork/{}.png \
		"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{}.png" || true

variant-sprites: ## Download HOME artwork for cosmetic variants (Alcremie, Vivillon, …)
	$(BACKEND) uv run python -m app.ingest.variant_sprites

female-sprites: ## Download + record female artwork (visual gender differences: Pyroar, …)
	$(BACKEND) uv run python -m app.ingest.female_sprites

thumbs:        ## Small WebP copies of all artwork for list views (96px, 320px); idempotent
	$(BACKEND) uv run python -m app.ingest.thumbs

chart:         ## Ingest the type-effectiveness chart (matchups)
	$(BACKEND) uv run python -m app.ingest.type_chart

enrich:        ## Add training & breeding info (gender, eggs, growth, EVs)
	$(BACKEND) uv run python -m app.ingest.enrich

data: migrate ingest items learnsets encounters enrich chart sprites variant-sprites female-sprites thumbs chunks  ## Full data pipeline
	@echo "Data pipeline complete."

test:          ## Run backend tests
	cd backend && DATABASE_URL=$(DB_URL) uv run pytest -q

damage-fixtures: ## Regenerate the damage reference cases (after changing frontend/lib/damageCalc.ts)
	cd frontend && node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --import ./scripts/ts-resolve.mjs scripts/damage-fixtures.ts

traces:        ## Recent plan traces (ARGS="--fallback", "--scope team", "--id 612" …)
	$(BACKEND) uv run python -m app.agent.trace_cli $(ARGS)

eval:          ## Run the RAG evaluation report
	$(BACKEND) uv run python -m eval.run

lint:          ## Lint backend + frontend
	cd backend && uv run ruff check .
	cd frontend && npm run lint
