# Proposal

## Why

Team grades, the team profile, the type chart and the Alcremie spin rules live only in
`frontend/lib/`. Every other client would have to copy them: the planned Flutter app
would mean a third language. The backend also can't compute anything from them: the
summary, the eval and any future server-side report can't calculate the grade the user
sees. Moving these rules to the backend makes it the single source of truth before a
second client exists.

## What Changes

- **Team rating moves to the backend.** A Python port of `frontend/lib/teamEval.ts`
  (`rateTeam`) produces the same overall score, grade, cap, ceiling, six area grades
  with headline and fix text, and the per-type cover and threat detail. It is returned
  with the opponent-free team analysis.
- **Team profile moves to the backend.** A Python port of `frontend/lib/teamProfile.ts`
  (`profileTeam`) produces the style, lean, averages, speeds, core types, weak/strong/
  resist lists, set counts and the one-line gist. It is returned alongside the rating.
- **Parity with today.** For the same team, the backend returns exactly what the
  TypeScript returns today: every number, grade and string. This is proven by golden
  fixtures generated from the current TypeScript before it is deleted.
- **Type chart is served by the backend.** A new read-only endpoint returns the
  attacking-type order and the effectiveness chart from the ingested
  `type_effectiveness` table. The frontend fetches it once and keeps only small lookup
  helpers. The hand-typed `CHART` leaves `frontend/lib/typeChart.ts`. It moves into
  `frontend/lib/damageCalc.ts`, which needs it synchronously and stays self-contained,
  like its Python port (ADR-006). A test pins every copy to the served chart.
- **Alcremie spin rules are served as data.** The Sweet→topping map, the cream→spin rules
  and the spin steps come with the evolution data for chains that evolve by spinning.
  `frontend/lib/alcremie.ts` is removed.
- **Frontend switches over.** The `/teams` cards, the team workbench and report, the home
  Type Calculator, the detail page's Type Matchups card and the evolution chain read
  the backend values. `frontend/lib/teamEval.ts`'s rating code and
  `frontend/lib/teamProfile.ts` are removed.
- **ADR-007 is amended:** grades stay deterministic but are computed in Python, not in
  `frontend/lib/teamEval.ts`.

No API change breaks existing callers: every new field is additive and optional.

## Out of scope

- `catchRate.ts`, `damageCalc.ts`, `evolution.ts` stay client-side. They recalculate
  instantly as the user edits inputs, and ADR-006 deliberately keeps the damage formula
  in TypeScript with a fixture-checked Python port. Revisit only if the Flutter app goes
  ahead.
- `pokeTypes.ts` (type colours are design tokens), `draftTeams.ts` (React-lifecycle draft
  handling), `api.ts`, `types.ts`, `answerFormat.tsx`, `askEvidence.ts`.
- `matchupFactors`, `isProvisional` and `gradeTone` in `teamEval.ts`. These only change
  how the existing vs-opponent payload and grades are displayed (labels, tone). They
  stay in the frontend for now.
- The team coach and the AI summary don't change. The coach still receives the page
  report the client sends. Having the coach or summary read the backend rating directly
  is a later change.
- No grade, threshold, weight or wording changes. This is a move, not a re-tune.
- The Flutter app itself.

## Capabilities

### New Capabilities
- `team-coach/team-rating`: the deterministic team rating (overall, grade, cap, area
  grades, cover/threat detail) and team profile, computed by the backend and returned
  with the team analysis.
- `pokedex/reference-data`: static game-reference data the clients read from the
  backend instead of hard-coding: the type-effectiveness chart and the Alcremie spin
  rules.

### Modified Capabilities
<!-- None: the team coach's requirements (coach-planning, coach-actions) are unchanged. -->

## Impact

- **Backend:** new `services/team_rating.py` and `services/team_profile.py`, new schemas
  in `schemas/analysis.py`, `team_analysis.analyze()` attaches rating and profile when
  there is no opponent. `services/matchups.py` gains the display order and a chart
  accessor. A new `GET /api/types/chart`. An Alcremie spin guide in
  `schemas/pokemon.py` / `services/pokemon_query.py`.
- **Frontend:** `lib/api.ts` / `lib/types.ts` types. `TeamCardParts.tsx`,
  `TeamWorkbench.tsx`, `TeamReport.tsx`, `TeamMatchupText.tsx`, `app/page.tsx`,
  `PokemonDetailView.tsx`, `EvolutionChain.tsx`. `lib/typeChart.ts` shrinks to helpers
  over fetched data. `lib/teamProfile.ts` and `lib/alcremie.ts` are deleted.
  `lib/teamEval.ts` keeps only display helpers.
- **Tests:** new golden fixtures under `backend/tests/fixtures/` and parity tests.
- **Docs:** ADR-007, `docs/architecture/team-coach.md`, `docs/architecture/overview.md`,
  `docs/components/team-coach.yaml`, `docs/components/pokedex.yaml`.
- **LLM:** none. No LLM calls are added or removed.
