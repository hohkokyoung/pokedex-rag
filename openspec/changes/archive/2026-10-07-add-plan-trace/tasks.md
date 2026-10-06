# Tasks

## 1. Storage

- [x] 1.1 Add `QuestionLog.trace` (nullable JSONB) and an Alembic migration that only adds/drops that column. Apply it with `make migrate`, check `\d question_log` shows `trace jsonb`, and confirm the generated migration doesn't touch `content_tsv`.
- [x] 1.2 Add the `TRACE_RETENTION` setting (default 2000) to `core/config.py`. Verify with a pytest that the default is 2000 and an env override is read.

## 2. Building the trace in the runner

- [x] 2.1 Change `runner._choose_plan` to return a `PlanChoice`: `plan`, `fell_back`, `keyword` (`KeywordPlan`), `llm_plan` (even when rejected), `skip_llm` (`fast-path` / `no-llm` / `None`) and `fallback_reason` (`rate-limited` / `timeout` / `provider-error:<Type>` / `no-valid-steps`). Update the runner and the three eval-harness call sites. Verify that `make test` and `python -m eval.run --keyless` pass unchanged.
- [x] 2.2 Record the answer tier (`code` / `llm` / `no-llm` / `abstain`) and the answer fallback reason in `_answer`, and the re-plan steps or error in `run_question`. Verify with stubbed-LLM pytests that each branch sets its tier (closed-form render, empty-plan abstain, no key, LLM answer, answer 429).
- [x] 2.3 Add `app/agent/trace.py: build(...)`, which makes the version-1 trace from the `PlanChoice`, the run, its `step` events (`ms`), usage and the total time. Apply the string and step caps, and dump args with `model_dump(mode="json")`. Store it in `ctx.extra["trace"]` before `done`, including the minimal `cached` trace. Verify with pytests on a fixed question:
  - fast path: `keyword`, confident, 0 calls, tier `code`;
  - LLM plan: `llm`, keyword not confident, steps with why, usage;
  - planner 429 → fallback `rate-limited` with the keyword plan used;
  - no valid steps → `no-valid-steps` with the rejected LLM plan;
  - no key → `skip_llm: no-llm`, no fallback;
  - unhandled abstain → tier `abstain` and `unhandled` listed;
  - cached → `cached`;
  - a 6-step trace is under 8 KB.

  Also check that the SSE events and the `done` payload are byte-identical with and without tracing.

## 3. Recording from every surface

- [x] 3.1 Add `trace.record(question, route, trace)`: insert the `question_log` row with the trace, then clear traces beyond the newest `TRACE_RETENTION`. Catch and log any failure. Extend `personalize.log_question` with an optional `trace`. Verify with DB pytests:
  - a row is written with its trace;
  - with retention 3, the 4th write clears the oldest trace and keeps its question;
  - a raising DB call logs a warning and returns normally.
- [x] 3.2 Pass an `AgentContext` from both Ask routes (streaming and non-streaming), and make the three route `_log` helpers thin wrappers that pass `ctx.extra["trace"]` to `trace.record`, still before `done`. Update the existing route tests that monkeypatch `_log` for the new argument. Verify with httpx pytests on each of `/api/ask/stream`, `/api/ask`, `/api/teams/{id}/ask` and `/api/calc/ask` that the logged trace has the right scope and planner, with a temporary team that is deleted afterwards.

## 4. Reading traces

- [x] 4.1 Add `app/api/traces.py` (`GET /api/traces` with `scope`, `planner`, `fallback`, `limit` ≤ 200, newest first; `GET /api/traces/{id}` returning 404 when the row is missing or has no trace) and register it in `main.py`. Verify with httpx pytests: the filters, the limit cap, the ordering, the full trace, and the 404.
- [x] 4.2 Add `app/agent/trace_cli.py` (list with `--scope/--planner/--fallback/--limit`, and `--id` for a full trace), plus a `make traces` target that passes `ARGS`. Verify with a pytest calling the CLI's `main()` on seeded rows (list line format, `--fallback` filter, `--id` and an unknown id), then run `make traces` against the Compose DB.
- [x] 4.3 Document the feature:
  - `docs/architecture/ask-agent.md`: a "Plan traces" section (contents, where stored, retention, read paths);
  - `docs/guides/local-dev.md`: `make traces` and `/api/traces`;
  - `CLAUDE.md`: the Commands line, and the convention that new runner decisions are recorded in the trace.

  Verify the documented commands run as written.

## 5. Integration

- [x] 5.1 Run `make test` and `make lint` and verify both pass. Then ask one question on each surface through the running app with no LLM tokens (keyword fast path: an Ask learn check, a team-coach plain question, a calc OHKO). Verify `make traces` lists all three with the right scope and planner and `--id` shows their steps. Delete those `question_log` rows afterwards.
- [x] 5.2 With the user's OK (it spends Groq tokens), ask one LLM-planned Ask question and confirm its trace shows the LLM plan, the steps' reasons and its usage. Then delete the row.

## Notes — 5.1 / 5.2 (2026-10-06)

- 5.1 (no tokens): Ask "Can Garchomp learn Earthquake?", team "Can Arcanine learn Flare Blitz?"
  (temporary team), calc "Can Garchomp OHKO Corviknight?" → `make traces` listed all three
  (ask/team/calc, keyword, 0 calls); `--id` showed steps; `/api/traces?scope=calc` and a
  missing id (404) checked. Found: the coach context step appeared inside the recorded
  keyword plan (the runner inserts it into the same plan object) → excluded from recorded
  plans, kept in executed `steps`. Rows and team deleted.
- 5.2 (1 Groq call): "Which Fire types learn Will-O-Wisp, and what is Fire weak to?" →
  planner llm, keyword not confident, LLM steps learnset(Will-O-Wisp, fire) +
  type_matchup(fire) with their reasons, both done (~140 ms), tier code, 1 call /
  2,566 + 225 tokens. Row deleted.
