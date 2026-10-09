# Tasks

## 1. Backend: server-built report

- [x] 1.1 Freeze golden cases: from real saved teams (read-only GETs), save inputs (teams, ratings, vs) and the website's `reportFacts` output to `backend/tests/fixtures/coach_report_{inputs,cases}.json` (no opponent, opponent, empty opponent, capped roster). Verify: the cases file has ≥ 4 labelled cases.
- [x] 1.2 Port to `services/coach_report.py`; golden test passes byte-for-byte. Verify: pytest.
- [x] 1.3 The coach endpoint builds `ctx.report` itself; remove `report` from `CoachAskRequest`. Endpoint test: keyless coach question → the team-context source starts with the server-built report; an opponent adds the matchup lines; an empty opponent adds none. Verify: pytest.
- [x] 1.4 Website: drop `reportFacts` and the `report` argument. Verify: `tsc`, eslint, and the team page's coach answers in the browser.

## 2. App: stream and state

- [x] 2.1 Add `/api/teams/{team_id}/ask` to the OpenAPI slice and run `make mobile-api`; add coach view kinds to `decodeView`. Verify: drift test, `flutter analyze`, decode tests on recorded coach views.
- [x] 2.2 Extract the shared stream reducer; add the coach runner (opponent, `team_updated` → invalidate). Verify: unit tests on a recorded coach stream (steps terminal, views decoded, `team_updated` invalidates).

## 3. App: coach UI

- [x] 3.1 Coach section: quick questions (with/without opponent, first member), disabled on an empty team, the thread with answers, How line, error line. Verify: widget tests.
- [x] 3.2 Cards: set edit (Apply/Dismiss/Revert), candidates (Add/Replace…/Confirm/Revert), member added (Undo), duel. Verify widget tests against a stateful fake: each click sends the right request, Revert restores the full set, nothing is sent without a click, a 422 shows on the card.

## 4. Check and docs

- [x] 4.1 Simulator against the real server on a scratch team (deleted afterwards): a plain team question, "add <Pokémon>" then Undo, a candidate Add then Revert, and with an opponent a duel or matchup question. Run `make test`, `make lint`, `make mobile-test`.
- [x] 4.2 Update docs: `docs/architecture/team-coach.md`, `docs/product/mobile.md`, `docs/components/mobile.yaml`, `docs/components/team-coach.yaml`. Verify: `make test`.
