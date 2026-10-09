# Tasks

## 1. Fix

- [x] 1.1 Add a failing test in `backend/tests/test_stats.py`. A member whose as-built HP, Def and SpD are each x.5 must read as a Wall: bulk 281 with half-up rounding, 278 with half-to-even. Verify it fails on the current code.
- [x] 1.2 Make `as_built` round half up (reuse `team_rating.js_round` via a shared helper in `stats.py`) and drop the `rnd` parameter and the profile's override. Verify: the new test, `tests/test_team_rating.py` (golden cases unchanged) and `make test` pass.
- [x] 1.3 Report which saved teams' roles or strategy axes shift: compare `GET /api/teams/{id}/analysis` and `/strategy` before and after for every saved team. Verify by listing the differences, or confirming there are none.

## 2. Docs

- [x] 2.1 In `docs/architecture/team-coach.md`, state once that as-built stats round half up (the website's rule), and drop the half-to-even caveat from `stats.as_built`'s docstring. Verify: `make test` (docs tests) and `make lint` pass.
