# Proposal

## Why

`stats.as_built` turns a member's real level-50 stats into base-stat equivalents. Its
last step, `(raw - 31) / 2`, always lands on .5 at level 50. The analysis engine,
strategy and summary round that half to even (Python's `round`). The team profile the
pages show rounds half up (it keeps the website's original maths). So the same member
can be one point apart on the cards and in the engine. Summed stats (bulk = HP + Def +
SpD) can then land on opposite sides of the 280 wall threshold.

## What Changes

- `as_built` rounds half up everywhere, matching what the team pages have always shown.
  The optional rounding parameter added for the profile is removed.
- Callers that change behaviour: `team_analysis` (roles, effective speed, opponent
  members), `team_strategy` (axes), `team_summary` (the speeds it phrases). A stat that
  was exactly .5 now reads one point higher where it used to round down.

## Out of scope

- No threshold, weight or wording changes. The rating and profile golden cases are
  unchanged.
- The damage calc and duels use real stats, not `as_built`, so they don't change.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
<!-- None: no spec states a rounding rule; this makes the engine agree with the
     team-rating capability's existing parity requirement. skip_specs is set. -->

## Impact

- `backend/app/services/stats.py` and its callers. Tests: a failing test first
  (bulk crossing 280), then `make test`, then `make eval` keyless for coach plans.
- Docs: `docs/architecture/team-coach.md` names the rounding once.
