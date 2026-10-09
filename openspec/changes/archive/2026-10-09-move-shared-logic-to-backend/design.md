# Design

## Context

What the website computes in the browser today:

- `frontend/lib/teamEval.ts` → `rateTeam(size, analysis)`. A pure function of the
  opponent-free `TeamAnalysis` plus the hard-coded type chart. Three places call it:
  - `TeamWorkbench.tsx` rates both teams for the matchup text.
  - `TeamReport.tsx` reaches it through `profileTeam`.
  - `TeamCardParts.tsx` reaches it through `profileTeam`. It loads `getTeam` +
    `getTeamAnalysis` for each card.
- `frontend/lib/teamProfile.ts` → `profileTeam(team, analysis)`. Needs the full `Team`
  (final stats, moves, items, sprites), the analysis, and the rating. Its `asBuilt`
  already mirrors `services/stats.as_built`.
- `frontend/lib/typeChart.ts`: a hand-typed `CHART` plus `ATTACK_ORDER`. Used by
  `teamEval`, the home Type Calculator (`app/page.tsx`, a client component) and
  `PokemonDetailView.tsx` (`superEffectiveHits`). The backend already loads the same
  chart from `type_effectiveness` (`services/matchups.py`), but in DB id order and
  including any non-battle types.
- `frontend/lib/alcremie.ts`: three constants used only by `EvolutionChain.tsx`.

The workbench rates the **opponent-free** analysis on purpose. With an opponent,
`team_analysis.analyze()` fills empty move slots against that opponent, which would
change the grade. The design keeps that rule.

## Goals / Non-Goals

**Goals:**
- Port the rating and profile literally: same arithmetic, ordering and strings. No
  re-tuning.
- Prove parity with frozen golden fixtures made from the current TypeScript.
- Change only the website's data source. Keep its look and behaviour.

**Non-Goals:**
- Making the coach or summary consume the rating. The coach still receives the
  client-sent page report.
- Batching card loads into the `/api/teams` list response. Each card still makes its
  existing two calls. A list-level rating is a later optimisation.
- Moving the display helpers (`gradeTone`, `matchupFactors`, `isProvisional`).

## Decisions

### 1. Rating and profile ride on the opponent-free `TeamAnalysis`

`TeamAnalysis` gains `rating: TeamRating | None` and `profile: TeamProfile | None`.
`analyze()` fills them only when `opponent is None` and the team has members.

- *Why:* every caller already fetches this analysis, and the rating is a pure function
  of it, so this adds no new requests and keeps the opponent-free rule in one place.
- *Alternative:* a separate `GET /teams/{id}/rating`. Rejected: it adds a round-trip
  per card and repeats the analysis work.
- *Alternative:* always rate, even with an opponent. Rejected: the grade would change
  when the user picks an opponent (see Context).

`profile` does not embed the rating, unlike the TypeScript `Profile`. The client
combines them, so the payload doesn't carry the rating twice.

### 2. New modules, reusing what's there

- `services/team_rating.py`: `rate_team(size, analysis, chart) -> TeamRating`. Pure,
  no DB. The chart is passed in so the tests run without the DB.
- `services/team_profile.py`: `profile_team(team, analysis, rating) -> TeamProfile`.
  Pure. Reuses `services/stats.as_built` (the TypeScript `asBuilt` already mirrors it).
- `services/matchups.py` gains:
  - `ATTACK_ORDER`: the 18 battle types in display order. It moves here from
    `typeChart.ts` and becomes the one copy.
  - `async def type_chart(session) -> dict[str, dict[str, float]]`, limited to
    `ATTACK_ORDER`.
- `team_analysis.analyze()` loads the chart once (it's cached per process) and calls
  both new functions.
- `TeamRating` exposes `fast_speed` (100). `TeamReport.tsx` then reads the threshold
  from the payload, and the TypeScript `FAST_SPEED` constant is deleted.

Nothing becomes fallback-only. The removed pieces:
- `rateTeam` and its private helpers, plus `WEIGHTS`, `gradeOf` and `FAST_SPEED`, from
  `teamEval.ts`. `gradeTone`, `matchupFactors`, `isProvisional` and the
  `Grade`/`Area`/`Rating` types stay; the types are re-pointed at the API shapes.
- All of `teamProfile.ts` and `alcremie.ts`.
- `CHART` and `ATTACK_ORDER` from `typeChart.ts`.

### 3. Port literally; mirror JavaScript numerics

The port must reproduce the TypeScript exactly, so:

- **Rounding:** `Math.round` rounds half up, but Python's `round()` rounds half to
  even. Use a local `js_round(x) = math.floor(x + 0.5)` everywhere the TypeScript uses
  `Math.round`.
- **Grade from the unrounded score:** an area's `grade` comes from the clamped,
  *unrounded* score, while `score` is rounded. Keep that quirk.
- **Sort stability:** JavaScript's `Array.sort` is stable, and so is `sorted()`. Port
  each comparator as a key or `cmp_to_key` that keeps the same tie order. Affected:
  `problems`, `resistersOf`, `fastest`, `speeds`, `coreTypes`, `weakTo`, `resists`.
- **Map order:** `coreTypes` relies on `Map` insertion order. Python's `dict` keeps
  insertion order too.
- **Strings:** port `cap`, `orList`, `andList`, `titleCase` and the `names(...)`
  " or "→" and " replace character for character. The replace hits only the first
  match, so use `str.replace(" or ", " and ", 1)`.

### 4. Parity via frozen golden fixtures, generated before the TypeScript is deleted

This follows the `damage-fixtures` pattern (ADR-006), with one difference: the
TypeScript is deleted afterwards, so the fixtures are frozen rather than regenerated.

1. `frontend/scripts/team-rating-fixtures.ts` reads
   `backend/tests/fixtures/team_rating_inputs.json`. Each input is a `{team, analysis}`
   pair. It runs the current `rateTeam` + `profileTeam` on each, then writes
   `team_rating_cases.json`. It also writes `type_chart_previous.json` (the
   hard-coded chart and order).
2. Inputs combine two sources:
   - the user's saved teams, captured from the running app's `/api/teams/{id}` and
     `/analysis`;
   - hand-built edge cases: 1 member, a duplicate species, empty move slots, no items,
     a 4× weakness, a slow team with priority users, and a score landing exactly on
     .5.
3. `backend/tests/test_team_rating.py` loads each pair, validates it into the Pydantic
   models, rates it with the frozen chart, and compares field by field. It is pure and
   needs no DB. It fails first, because the module doesn't exist yet.
4. `test_type_chart.py` compares the DB chart with `type_chart_previous.json`. It
   needs the DB and skips when the DB is down, like the other DB tests.

Once the frontend has switched over and `rateTeam` is deleted, the generator script
goes too. The JSON stays as the record of the old behaviour.

- *Alternative:* keep `teamEval.ts` and fixture-check both forever, as with the damage
  calc. Rejected: the point is one copy. The damage calc keeps two only because it
  needs instant client-side recalculation, which grades don't.

### 5. Type chart endpoint and client cache

`GET /api/types/chart` → `{order: string[], chart: {[atk]: {[def]: number}}}`. It
includes every pair, 1× entries too, so clients need no default. It lives in
`api/pokemon.py` next to `GET /api/types`.

Client side, `lib/typeChart.ts` keeps `typeEff`, `typingEff`, `defensiveMatchups` and
`superEffectiveHits`. They now take a `TypeChart` argument. A module-level cached
promise, `loadTypeChart()`, plus a `useTypeChart()` hook makes sure the chart is
fetched at most once per page load. The home Type Calculator and the detail page's
super-effective list show their existing skeleton until the chart arrives.

The damage calc (`lib/damageCalc.ts`) also read the chart from `typeChart.ts`. This was
found during apply. The hard-coded chart moves into `damageCalc.ts` itself: the calc must
stay a pure module that Node can run for `make damage-fixtures`, and its Python port
already carries its own copy (ADR-006). `test_type_chart.py` checks the served chart and
the Python copy against the previous client chart. The regenerated damage fixtures are
byte-identical, which pins the TypeScript copy.

- *Alternative (rejected, user decision):* pass the fetched chart into `calcHit`. That
  would change the calc's signature and its Node fixture runner, which is outside this
  change.
- *Alternative:* have the backend compute the calculator's result per selection.
  Rejected: the calculator updates on every click and the chart is about 2 KB.
  Fetching it once and computing locally is instant and still has one source.

### 6. Alcremie spin guide on the detail response

There's a new `services/alcremie.py` holding the steps, toppings and cream rules, with
creams as an ordered list. `PokemonDetail` (and the form detail with the same evolution
fields) gains `spin_guide: SpinGuide | None`. `pokemon_query` sets it when any
`evolution_stages[].trigger == "spin"`.

`EvolutionChain.tsx` receives it as a prop. It keeps its current ordering: known creams
in guide order, then any unknown ones.

- *Alternative:* a generic `/api/reference/alcremie` endpoint. Rejected: there is
  exactly one consumer and it already has the detail payload.

### LLM budget

None. This change adds and removes no LLM calls. Rating, profile, chart and spin guide
are all deterministic. Opening a team page stays at 0 LLM calls (ADR-007).

## Risks / Trade-offs

- [A port mismatch in an edge case the fixtures don't cover] → Inputs include
  captured real teams plus targeted edge cases, and the numeric rules above are the
  known traps. Any mismatch fails CI before the TypeScript is deleted.
- [DB chart differs from the hard-coded chart, e.g. ingest of a newer generation] →
  `test_type_chart.py` fails loudly. Deciding which is right is a data question, not
  part of this move.
- [Team pages break if the backend is older than the frontend] → Both ship together in
  Compose. The new fields are optional, and the frontend treats a missing rating as
  loading or empty, never as a crash.
- [Captured saved teams in fixtures] → They're the user's own local teams (single-user
  app). If any shouldn't be committed, replace them with hand-built ones before
  committing.
- [Slightly larger analysis payload] → The rating plus profile is a few KB, and only
  on opponent-free requests.

## Migration Plan

Additive first, then the switch, then the deletion:

1. Add the fixtures (generated from the current TypeScript) and the failing tests.
2. Add the backend modules, the fields and the endpoint, and get the tests passing.
3. Switch the frontend.
4. Delete the TypeScript.

Rollback means reverting the frontend commit. The backend fields are optional and
harmless to older clients.

## Docs affected

- `docs/decisions/ADR-007.md`: grades are computed by `services/team_rating.py`, not
  `frontend/lib/teamEval.ts`. Amend the decision and add a dated note.
- `docs/architecture/team-coach.md`: in the deterministic engines table, replace the
  `frontend/lib/teamEval.ts` row with `services/team_rating.py` and
  `services/team_profile.py`.
- `docs/architecture/overview.md`: the `lib/teamEval.ts` row.
- `docs/architecture/retrieval.md` or `data.md`: wherever the type chart's home is
  described, if it is (check during apply).
- `docs/components/team-coach.yaml`: code list (drop `teamProfile.ts`, add the new
  services) and interfaces (no new team route).
- `docs/components/pokedex.yaml`: code list (drop `alcremie.ts` if listed; `typeChart.ts`
  stays as helpers) and interfaces (+ `GET /api/types/chart`).
- `docs/product/teams.md` and `README.md`: no user-visible change, so no edit beyond
  any file paths they name.
