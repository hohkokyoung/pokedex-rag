# Design

## Context

The coach endpoint (`POST /api/teams/{id}/ask`, `api/teams.py`) already plans and
answers on the server through `run_question(scope="team")`. The browser's only
contribution beyond the question is the optional `report` text. The website builds it
with `reportFacts` from `TeamMatchupText.tsx`, using two inputs. One is the
opponent-free ratings, which the backend already computes (`team_rating.py`, exposed
on `GET /analysis`). The other is `computeMatchup` over the engine's `vs_opponent`
cells. `team_tools.team_context` puts the report first as "authoritative" evidence.

The app already has, from phases 3 and 4:
- `TeamsRepository.setSlot / clearSlot / applyBuild`;
- the team providers with `invalidateTeam`;
- the Ask SSE reader (`parseSse`, `AskRun._apply`);
- the Ask cards (`ViewCard`, `globalRefs`) and per-kind view decoding (`views.dart`).

## Goals / Non-Goals

**Goals:** one report built in one place; coach parity with the website (same
questions, same cards, same click-only writes); no new LLM spend.

**Non-Goals:** new coach tools or prompts; the website's written matchup card in the
app; persisting threads.

## Decisions

1. **Server-built report: `services/coach_report.py`.**
   - It ports `reportFacts` plus the slice of `computeMatchup` it reads: threats sorted
     by how many of ours they beat, the best answer by lowest damage taken, the lead
     by most wins, and the members that win nothing.
   - Inputs are `TeamOut`s, the `TeamRating`s and `VsOpponent`.
   - The endpoint computes the opponent-free analysis for each side (rating only
     exists without an opponent) plus the analysis with the opponent it already makes,
     then sets `ctx.report`.
   - *Alternative:* keep `report` optional so clients can override. Rejected: two
     sources of truth is the drift ADR-009 removes.
   - The field is dropped from `CoachAskRequest`. Pydantic ignores an unknown field, so
     an old page that still sends it doesn't break.
2. **Parity is pinned by golden cases**, as for the ratings
   (`tests/fixtures/coach_report_{inputs,cases}.json`). The cases are frozen once from
   the website's TypeScript on real saved teams (with and without an opponent, an
   empty opponent, a capped roster), and then `reportFacts` is deleted. Display-only
   speed fields (`speedOf`, `boostedSpeed`) aren't in the report and aren't ported.
3. **The website stops sending the report.** `TeamWorkbench` drops the `reportFacts(...)`
   prop; `coachAskStream` drops the argument. `computeMatchup`, `matchupHeadline` and
   `tally` stay in the website for its Matchup card.
4. **App stream reader is shared.**
   - `AskRun`'s event handling moves into a reusable `AskStreamState` reducer.
   - `AskRun` (Ask tab) and a new `CoachTurn` runner both feed it. The coach adds one
     event, `team_updated`, which only invalidates the team's providers (the
     payload's team is ignored; the providers refetch).
   - Coach view kinds (`set_edit`, `candidates`, `member_added`, `duel`) join
     `decodeView`.
5. **Coach state lives with the team page:**
   - a `coachProvider` family keyed by team id;
   - a list of turns, with only one streaming at a time; a new question cancels
     nothing (as on the website, busy disables asking);
   - leaving the page disposes it (autoDispose), matching the website's
     per-visit thread.
6. **Card actions call the existing repository**, and each card keeps its own state:
   - Apply → `applyBuild(slot, fields)`;
   - Revert / Replace-Revert → `setSlot` with the member's full saved set (the Dart
     twin of the website's `restoreMember`);
   - Add → `setSlot(firstEmpty, {pokemon_id})`;
   - Undo / Add-Revert → `clearSlot`.
   - Every success calls `invalidateTeam` (ours or the opponent's, per `side`).
7. **Placement:** a "Coach" section on the team page below the slots and above the
   report. It holds the quick-question chips, the box, then the turns (newest last).
   An "Ask the coach" button in the app bar scrolls to it.

## LLM budget

Unchanged from the website's coach: plan ≤ 1, build ≤ 1, answer ≤ 1 per question;
plain team questions take the fast path (0 planning calls). Building the report adds no
LLM calls (pure code), and token use for it matches today's, since the website already
sent the same text. Tests and fixtures are recorded keyless (0 calls); the Simulator
check uses plain team questions (fast path), an explicit add (code-answered), and, with
the key, at most one drafting question.

## Reused / removed

- Reused: `team_analysis.analyze`, `team_rating`, `team_tools.team_context`,
  `run_question`; app `TeamsRepository`, `invalidateTeam`, `parseSse`, `ViewCard`.
- Removed: `reportFacts` (website), `CoachAskRequest.report`.

## Docs affected

- `docs/architecture/team-coach.md` (the report is server-built)
- `docs/product/mobile.md` (Coach)
- `docs/product/teams.md` (unchanged behaviour; verify wording)
- `docs/components/mobile.yaml`, `docs/components/team-coach.yaml` (new module)

## Risks / Trade-offs

- **Golden drift:** the website's matchup card still uses `computeMatchup`. A change
  there won't reach the coach. This is acceptable: the card is display and the coach
  owns its facts, and the golden test pins the coach.
- **Extra analysis work per question:** up to two more opponent-free analyses (DB
  reads, ~tens of ms). Fine for a single-user app.
- **Cards act on stale members** if the team changed after the answer. The website has
  the same behaviour; the server validates every save, so a bad save is rejected (422)
  and shown.
