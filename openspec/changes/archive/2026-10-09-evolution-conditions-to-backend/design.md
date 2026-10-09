# Design

## Context

`buildCondition(stage)` in `frontend/lib/evolution.ts` is a pure function of one
`EvolutionStage` (`trigger`, `min_level`, `item`, `condition`). Its only caller is
`EvolutionChain.tsx` (`EvoCard`). The backend builds stages in
`services/pokemon_query.py`: `_evolution` for species and `_form_evolution` for forms.
That's the same pattern as the team-rating move (ADR-009), on a smaller scale.

## Goals / Non-Goals

**Goals:** a literal port pinned by golden cases over every ingested stage; the website
switches over; the TypeScript is deleted.

**Non-Goals:** rewording; changing the raw fields; the mobile app.

## Decisions

1. **`display` on `EvolutionStage`.** The schema is
   `{chips: [{label, tone: "solid"|"soft"}], description: str | None}`. It is filled
   where the stages are built, so species and form chains both get it, and any
   future client reads it from the detail response.
   - *Alternative:* a separate endpoint. Rejected, because the chain already ships
     with the detail response.
2. **New `services/evolution_display.py`.** A literal port of `parseCondition` and
   `buildCondition`. The regexes keep the same semantics, including case-insensitive
   matching and the `≥` character. `titleCase` uppercases only the first character,
   as on the website. `aOrAn` keeps its vowel rule.
3. **Golden cases cover every stage in the data, not a sample.**
   - A one-off script collects the distinct `(trigger, min_level, item, condition)`
     tuples from the database into `backend/tests/fixtures/evolution_inputs.json`.
     The test is pure, so this is a frozen input; collect with SQL over the
     `pokemon_evolution` source the query service reads.
   - `frontend/scripts/evolution-fixtures.ts` runs `buildCondition` on each tuple and
     writes `evolution_cases.json`.
   - `tests/test_evolution_display.py` is pure (no DB) and checks every case. The TS
     script is deleted with `lib/evolution.ts`, and the JSON stays as the record.
4. **The reused helpers are pure functions.** Reused: `pokemon_query`'s stage
   builders and `ts-resolve.mjs` (with the `@/` alias already added). Removed:
   `frontend/lib/evolution.ts`. Nothing becomes fallback-only.

LLM budget: none. Deterministic, 0 calls.

## Risks / Trade-offs

- [Regex semantics differ between JS and Python, e.g. `\s` and Unicode] → Run golden
  cases over every real stage. Any stage that differs fails CI before the TypeScript
  is deleted.
- [Payload grows slightly] → A few short strings per stage.

## Docs affected

- `docs/decisions/ADR-009.md`: drop "the evolution condition text" from the
  client-side list, with a dated note.
- `docs/components/pokedex.yaml`: add the service.
- `docs/product/pokedex.md`: only if it names `lib/evolution.ts` (check).
