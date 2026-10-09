# Proposal

## Why

Phase 5 of the mobile app: the team coach is the last part of the website's Teams page
the app lacks. One thing blocks it. The website writes the coach's "page report" (both
ratings with each grade's verdict and fix, the matchup verdict, their top threats with
your best answers, the best lead) in the browser (`reportFacts` / `computeMatchup` in
`TeamMatchupText.tsx`) and sends it with every question. That text is authoritative
for the coach. A second copy in Dart would drift; per ADR-009 it belongs on the server.

## What Changes

- **Backend:** the coach builds the report facts itself
  (`services/coach_report.py`, a port pinned to the website's old output by golden
  cases) from the opponent-free ratings and the matchup. `CoachAskRequest.report` is
  removed; the website stops building and sending it. Its Matchup card keeps
  `computeMatchup` for display.
- **App:** a Coach section on the team page, like the website's:
  - quick questions, a question box, and a thread of turns;
  - each turn shows the streamed answer with citations, the How line and steps, and
    an error line when the stream fails;
  - cards: a set change (was → now, **Apply** / **Dismiss**, then **Revert**);
    candidates (**Add** into the next empty slot or **Replace…** a member, each with
    **Revert**); an explicit add (**Undo**); a duel; and the Ask cards for dex views.
- An add the coach made itself (`team_updated`) or any Apply / Add / Replace / Revert
  / Undo refreshes the slots and report.
- The coach SSE client shares the Ask stream reader. `/api/teams/{id}/ask` joins the
  OpenAPI slice.

## Capabilities

### New Capabilities
- `mobile/team-coach`: the coach on the app's team page: asking, the thread, and the
  user's Apply / Add / Replace / Revert / Undo clicks.

### Modified Capabilities
- `team-coach/coach-planning`: "Team context is always attached" — the report facts
  are built by the server, not sent by the page.

## Out of scope

- The calc coach and the damage calculator (phase 6).
- The website's written matchup card (`TeamMatchupText`) on the app; the app keeps its
  verdict + scorecard card.
- Keeping the thread across app restarts (the website doesn't either).
- Any new coach capability or tool; the coach's behaviour, budget and write gate are
  unchanged.

## Impact

- Backend: `services/coach_report.py` (new), `api/teams.py` (coach endpoint),
  `schemas/team.py` (`report` removed), `agent/team_tools.py` (unchanged contract:
  `ctx.report` is now always server-built). Tests: golden report cases, endpoint test.
- Website: `TeamWorkbench.tsx`, `TeamCoach.tsx`, `lib/api.ts`, `TeamMatchupText.tsx`
  (`reportFacts` removed).
- App: `lib/features/ask/` stream reader generalised; `lib/features/teams/coach*.dart`
  (new); team page; OpenAPI slice + generated client.
- Docs: `docs/architecture/team-coach.md`, `docs/product/mobile.md`,
  `docs/components/mobile.yaml`, `docs/components/team-coach.yaml`.
