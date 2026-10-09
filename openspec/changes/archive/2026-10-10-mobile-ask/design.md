# Design

## Context

- `/api/ask/stream` emits SSE events:
  - `plan` (planner, cached, replan, steps[id, tool, why, args, error], unhandled?);
  - `step` (id, state: running/done/empty/error, summary);
  - `view` (a view dict + step);
  - `team_updated` (coach only);
  - `sources` ([Source]) and `delta` ({text});
  - `done` ({usage, fallback}) and `error` ({message}).
- `/api/ask` folds the same events into `AskResponse`. Its `views` were `list[dict]`,
  so the OpenAPI schema didn't describe them and clients couldn't generate them.
- The website renders views in `components/agent/` (AskBento, ViewBlock, views/*).
  Starters are `SUGGESTIONS` in `AskConsole.tsx`; follow-ups are `followUps()` in
  `lib/askEvidence.ts` (from cited Pokémon names); the abstain pattern is `ABSTAIN`.
- `/api/ask/status` returns `{enabled, provider}`.

## Decisions

1. **Typed views in the API:**
   - `AskResponse.views: list[View]`, using the agent's existing discriminated union.
     That's the same models the runner dumps, so the wire format doesn't change. It
     does start validating views on the non-streaming path.
   - Each view model gains `step: str | None`.
   - The runner now writes `{**view.model_dump(), "step": id}`. The old
     `{"step": id, **dump}` would let the new `step: None` overwrite the id; a
     runner test caught that during apply.
2. **The app reads SSE with dio.**
   - A `POST /api/ask/stream` with `ResponseType.stream`, split into `event:`/`data:`
     frames by a small parser (`features/ask/sse.dart`).
   - Event *payloads* use generated types: views via
     `AskResponseViewsSealed.fromJson`, sources via `Source.fromJson`. Only the
     small envelopes (plan steps, step state, delta, done, error) are read by hand.
     They're protocol framing, not domain types.
   - An unknown view `kind` throws in the generated decoder; the parser catches it and
     skips that view.
3. **State:** an `AskRun` notifier holds the status (idle / streaming / done / error),
   steps, views, sources, answer text, usage, elapsed time, unhandled and the error.
   A new question cancels the previous stream (dio `CancelToken`).
4. **Cards:** native widgets per view kind, reusing TypeChip, Artwork, Section and
   GradeBadge where they fit:
   - ranking: rows with the stat value;
   - pokemon_list and learners: compact Pokémon rows with `via`;
   - type_chart: rows like the detail matchups;
   - move_list;
   - learnset: groups;
   - learn_check: a yes/no verdict with how.

   Each card lists its `chunk_refs` as source numbers.
5. **Citations:**
   - The answer text is split on `[n]` / `【n】`, and citation spans are tappable.
   - A sheet shows the source's snippet, chunk type, and "Open {Pokémon}" when the
     source has a dex number.
6. **Follow-ups and abstention** mirror `followUps()` and `ABSTAIN`. They're UI wording
   over cited names, not game rules (ADR-010's "computes no game rules" holds).
7. **Profile sheet:** preferred types as TypeToggles (PUT `/api/profile`) and the
   favourites list (from phase 2).
8. **Navigation:** a third shell branch, `/ask`.

LLM budget: the server's, unchanged: ≤ 3 calls per question, 0 for fast-path
closed-form questions. The app never retries an answer on its own. A 429 is the
server's fallback, shown as delivered.

## Risks / Trade-offs

- [Typed views reject a malformed view on `/api/ask`] → All view dicts come from
  these models' own dumps, and the full backend suite (agent, eval harness tests)
  passes.
- [SSE through dio on iOS] → Streams over plain HTTP on the LAN like any response. The
  widget tests feed recorded event streams through the fake adapter.
- [A long answer reflows while streaming] → The text updates as one widget, and the
  cards append below.

## Docs affected

- `docs/architecture/ask-agent.md`: typed views in `AskResponse`.
- `docs/product/mobile.md`: Ask.
- `docs/components/mobile.yaml`: interfaces.
