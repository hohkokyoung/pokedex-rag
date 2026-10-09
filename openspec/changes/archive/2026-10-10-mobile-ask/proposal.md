# Proposal

## Why

Ask is pokérag's centrepiece: questions answered only from the data, with citations,
the plan shown, and code-written results for closed-form questions. The app has the
Pokédex and Teams; without Ask it isn't the product. The backend already streams
everything a client needs over SSE. This change makes those payloads typed for
generated clients and renders them natively.

## What Changes

- **Backend: typed views.**
  - `AskResponse.views` becomes the agent's `View` union (discriminated by `kind`)
    instead of untyped dicts. The OpenAPI schema now documents every view, and the
    app's client generates them.
  - Each view gains an optional `step` field. The runner already sends it, and it was
    previously an undeclared extra key.
- **Ask tab** (the bottom bar becomes Pokédex | Teams | Ask):
  - a question box with the website's five starter questions, labelled by kind;
  - the LLM/keyless status, with "keyless: answers quote the records" when no key is
    set.
- **Streaming answer** over `/api/ask/stream`:
  - plan steps appear as they run (their "why" and state);
  - the answer streams in, with **[n] citations** that open the cited record (snippet,
    Pokémon link);
  - a "How it was answered" line: keyword / LLM / cached, the time and the LLM calls;
  - the plan's "couldn't apply" notice up front; errors and an unreachable server are
    shown plainly.
- **Result cards** for every Ask view: ranking, pokemon_list, type_chart, move_list,
  learnset, learners and learn_check. Each ends with its sources. Tapping a Pokémon
  opens its page.
- **Ask next:** once answered, follow-up questions built from the cited Pokémon (as on
  the website).
- **Profile:** preferred types (edit) and favourites (list), the inputs to "for you"
  questions.

## Out of scope

- Team and calc coach views (`candidates`, `set_edit`, `member_added`, `duel`,
  `damage`, `survive`, `build_proposal`); phase 5.
- Caching answers in the app (the server's cache applies as for the website).

## Capabilities

### New Capabilities
- `mobile/ask`: asking pokérag in the app, with streamed, cited answers and typed
  result cards.

### Modified Capabilities
- `assistant/result-views`: the Ask response's views are declared as a typed union in
  the API (including the step that produced each).

## Impact

- **Backend:** `schemas/ask.py` (`views: list[View]`); `agent/views.py` (`step` on each
  view); `agent/runner.py` (`step` set after the dump, so it isn't overwritten). No
  behaviour change for the website, which reads the same keys.
- **Mobile:** `features/ask/` (SSE client, screen, cards, profile sheet); the OpenAPI
  slice gains `/api/ask` and `/api/ask/status`.
- **Docs:** `docs/product/mobile.md`, `docs/architecture/ask-agent.md` (typed views),
  `docs/components/mobile.yaml`.
- **LLM:** unchanged per question (≤ 3 calls; 0 on the fast path), the same budget as the
  website. Each app question is one server run.
