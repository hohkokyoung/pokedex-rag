# Design

## Context

- **One runner for every surface.** Ask, the team coach and the calc coach all go through `app/agent/runner.run_question`, which yields `plan`, `step`, `view`, `sources`, `delta` and `done` events.
- **Each route logs separately today.** `api/ask.py`, `api/teams.py` and `api/calc.py` each have a near-identical `_log(question, planner)`. It writes `question_log(question, route)` with route `agent-*`, `coach-*` or `calc-*`, just before `done`, and swallows any failure. The non-streaming `POST /api/ask` logs too.
- **The runner holds the trace data, but loses part of it.** Everything the trace needs passes through the runner:
  - **Kept:** the final plan, the `_Run` results (state and summary per step), the `step` events (with `ms`), `usage` and `run.fallback`.
  - **Thrown away:** `_choose_plan` returns only `(plan, fell_back)`. The keyword plan, its `confident` flag, the LLM's own plan when it was rejected, and the *reason* for a fallback go to `log.info` or nowhere. The answer tier is decided inside `_answer` and not kept.
- **Logged questions feed personalization.** `question_log` is read by `personalize.recent_questions` (the last 5) to personalize answers.
- **The eval doesn't log.** It calls `run_question` directly and never writes `question_log`.

## Goals / Non-Goals

**Goals:**
- One trace per answered question on every scope, built in the runner and stored with the existing log row.
- Fallback *reasons* and the rejected/alternative plan captured where they happen today.
- No change to answers, prompts, LLM calls, SSE events or route timing.
- Readable locally from a CLI and a read-only API.

**Non-Goals:**
- No UI page.
- No reasoning text, raw provider payloads, answers or chunk contents.
- No metrics, aggregation or external logging.
- No auth.

## Decisions

### 1. Storage: a nullable `trace` JSONB column on `question_log`

- **The change:** one Alembic migration adds `trace JSONB NULL`. Existing rows stay `NULL`, with no backfill. Downgrade drops the column.
- **Why this table:**
  - It's the row the routes already write at the same moment, so the write count stays at one insert.
  - The question, route and time are already there.
  - The CLI and API need no join.
- **Alternative considered:** a separate `plan_trace` table with a foreign key. Rejected: a second insert per question and a join for every read, with no benefit for a single-user app.
- **Autogenerate:** the migration is hand-checked so it doesn't touch the DB-managed `content_tsv` (the existing `include_object` guard already excludes it).

### 2. Trace shape (version 1)

JSON, built by `app/agent/trace.py`, with strings capped so a trace stays under ~8 KB:
- `why` and `summary`: 200 characters;
- argument values: 300 characters;
- at most 12 steps per plan.

Arguments are dumped with `model_dump(mode="json")`, so nested models such as `StatFilter` serialize.

```json
{
  "v": 1, "scope": "ask", "ms": 1840,
  "planner": "llm",                 // cached | keyword | llm
  "skip_llm": null,                 // fast-path | no-llm | null (LLM was asked)
  "fallback": null,                 // rate-limited | timeout | provider-error:<Type> | no-valid-steps | null
  "keyword": {"confident": false, "steps": [{"tool": "learnset", "args": {…}, "why": "…"}]},
  "llm": {"steps": [{"tool": "…", "args": {…}, "why": "…"}], "unhandled": ["…"], "needs_followup": false},
  "replan": {"steps": […], "error": null},
  "steps": [{"id": "s1", "tool": "learnset", "state": "done", "summary": "…", "ms": 41}],
  "answer": {"tier": "code", "fallback": null},   // code | llm | no-llm | abstain; fallback: rate-limited | <Type>
  "usage": {"llm_calls": 1, "input_tokens": 2510, "output_tokens": 170}
}
```

`keyword` is recorded whenever the keyword planner ran, which is every uncached question. `llm` is recorded whenever the LLM was asked, including when its plan was rejected. Coach traces include the built-in context step (`team_context` / `calc_context`) in `steps`.

### 3. Capturing reasons where they happen

- **`_choose_plan`** returns a `PlanChoice` dataclass instead of a tuple:
  - `plan` and `fell_back`, as today;
  - `keyword` (the `KeywordPlan`);
  - `llm_plan` (when made, even if rejected);
  - `skip_llm`;
  - `fallback_reason`, using the same classification as the existing `log.info` (`answer_service.is_rate_limited`, `asyncio.TimeoutError` → `timeout`, otherwise `provider-error:<Type>`, or `no-valid-steps`).

  Callers (the runner, and the eval harness's `plans_only` paths) are updated to read the fields; the eval only needs `plan` and `fell_back`.
- **Re-plan:** the runner records the steps it added, or the error type.
- **`_answer`:** records `run.answer_tier` and `run.answer_fallback` at the branch it takes (closed-form render, empty-plan abstain, no-LLM, LLM, LLM failed → extractive).
- **Step timings:** taken from the `step` events the run already emits (their `ms`).
- **Total time:** measured with `time.perf_counter()` from the start of `run_question`.

### 4. Handing the trace to the routes without changing `done`

- **The handoff:** just before yielding `done`, the runner stores the finished trace in `ctx.extra["trace"]`. That's the same `AgentContext` the routes already build for the team and calc coaches.
- **Ask:** the Ask routes (streaming and non-streaming) start passing an `AgentContext(scope="ask")` too, so all three read the trace from the same place.
- **Why not `done`:** the `done` payload and the SSE contract stay as they are; the trace never goes to the client.
- **Cached Ask answers** build a minimal trace (`planner: "cached"`, zero usage, `ms`).

### 5. One recorder, three route labels

- **The recorder:** `app/agent/trace.py: record(question, route, trace)` replaces the bodies of the three `_log` functions. It inserts the `question_log` row with the trace, then prunes. Each route keeps a thin `_log(question, planner, trace)` that picks its label (`agent-` / `coach-` / `calc-`), so existing tests that monkeypatch `_log` keep working with the extra argument.
- **`personalize.log_question`** gains an optional `trace` argument; its other callers are unchanged.
- **Best-effort:** any exception is caught and logged at warning level. The write still happens before `done`, as today.

### 6. Retention: clear traces beyond the newest N

- **The rule:** after each insert, one statement clears the trace on rows older than the newest N traced rows:
  ```sql
  UPDATE question_log SET trace = NULL
  WHERE trace IS NOT NULL
    AND id < (SELECT id FROM question_log WHERE trace IS NOT NULL
              ORDER BY id DESC OFFSET :n - 1 LIMIT 1)
  ```
- **The setting:** N is `TRACE_RETENTION`, defaulting to 2,000.
- **Why clear rather than delete:** the questions stay for personalization.

### 7. Read paths

- **CLI:**
  - Run as `python -m app.agent.trace_cli [--scope ask|team|calc] [--planner …] [--fallback] [--limit 20] [--id N]`, via `make traces ARGS="…"` against the Compose DB (host port 5433, like `make eval`).
  - The list shows one line per question: id, time, scope, planner, a fallback reason if any, step tools, LLM calls and the question.
  - `--id` prints the full trace, formatted.
- **API:** `app/api/traces.py`, registered in `main.py`:
  - `GET /api/traces` with `scope`, `planner`, `fallback: bool` and `limit` (≤ 200, default 50), newest first. Rows carry `id, created_at, question, route, scope, planner, fallback, answer_tier, llm_calls, tools`.
  - `GET /api/traces/{id}` returns the full trace, or 404 if the row is missing or has no trace.

  Both are read-only and filter on JSONB keys (`trace->>'scope'`, and so on) on at most N rows, so no index is needed.

### Modules reused, changed, removed

- **Reused:** `QuestionLog`, `personalize.log_question` (with the extra argument), the runner's `_Run`, `step` events, `Usage`, `answer_service.is_rate_limited`, and the Compose DB settings.
- **Changed:** `runner._choose_plan` (returns `PlanChoice`), `runner._answer` (records its tier), `runner.run_question` (builds the trace), the three API `_log` helpers (now thin wrappers), and the eval harness call sites of `_choose_plan`.
- **Removed:** the duplicated bodies of the three `_log` functions. Nothing becomes fallback-only.

### LLM budget

**0 extra LLM calls and 0 extra tokens per question on every scope.** The per-question budgets in the existing specs are unchanged. The extra database work is one UPDATE (the prune) per question, in the same best-effort write.

### Docs affected

- **`docs/architecture/ask-agent.md`:** a "Plan traces" section covering what's recorded, where, retention and how to read it.
- **`docs/guides/local-dev.md`:** `make traces` and `/api/traces`.
- **`CLAUDE.md`:** one convention, "new runner decisions (planner choice, fallbacks, answer tiers) are recorded in the trace".

## Risks / Trade-offs

- **Stale fields when the runner changes.** Mitigation: the trace has a version (`v`), the builder lives next to the runner, and tests assert the trace for each path.
- **Trace size.** A plan of 6 steps with long arguments could grow. Mitigation: the string and step caps above, and a test asserting a full multi-step trace stays under 8 KB.
- **Changing `_choose_plan`'s return type touches the eval harness and tests.** Mitigation: `PlanChoice` keeps `plan` and `fell_back`, and the call sites are updated in the same task.
- **Questions are stored verbatim with their plans.** That's acceptable for a single-user local app; it's the same data `question_log` already holds.
- **The prune UPDATE on every question.** It's cheap at this size (≤ a few thousand rows) and skipped when fewer than N traces exist.

## Migration Plan

1. Apply the migration (`make migrate`). Existing rows keep `trace = NULL`.
2. Deploy the backend. New questions get traces; nothing else changes.
3. Rollback: downgrade the migration (drops the column). The routes' best-effort writes tolerate a missing column by logging a warning, though rollback normally reverts the code too.

## Open Questions

None blocking. Whether to add a small UI page later is left for a separate change.
