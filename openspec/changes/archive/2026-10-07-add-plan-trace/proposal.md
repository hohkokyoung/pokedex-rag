# Proposal

## Why

The assistant's decisions (which planner ran, the plan it chose and why, what it couldn't express, what each step returned, and why a fallback happened) are shown live in the UI, but almost none of it is kept. `question_log` stores only the question, a route label and a time, and the rest reaches the backend console at best. Every recent investigation (u7 planned as lore search, "evolve by trading" falling back and guessing, silent 429s in the coach evals) needed one-off scripts that re-ran Groq calls. A per-question plan trace makes those decisions reviewable after the fact, at no LLM cost.

## What Changes

- Every question on every surface (Ask, team coach, calc coach) records a **plan trace** when it finishes: scope, which planner answered (cached / keyword fast path / LLM / keyword fallback), the fallback reason (rate-limited, timeout, provider error, no valid steps, answer failure), the keyword plan and its confidence, the LLM plan (each step's tool, args and why), `unhandled` constraints, re-plan steps, each step's final state, summary and time, the answer tier (code-rendered / LLM / no-LLM / abstain), usage (LLM calls, tokens) and total latency.
- The trace is built in the shared runner from data it already holds, so all three surfaces get it from one place. The three API routes' near-identical `_log` helpers become one shared recorder.
- Storage: a nullable `trace` JSONB column on `question_log` (one Alembic migration). It's written with the existing question log before `done`, and best-effort: a failed write never fails or delays an answer.
- Retention: only the newest 2,000 rows keep their trace. Older rows keep their question (personalization uses the question history) with the trace cleared.
- Reading traces:
  - `make traces`: a CLI listing recent questions with planner, fallback, steps and usage, filterable by scope, planner and fallback, plus one trace in full.
  - `GET /api/traces` and `GET /api/traces/{id}`: read-only.
- No change to answers, plans, prompts or LLM calls: **0 extra LLM calls, 0 extra tokens**.

### Out of scope

- A UI page for traces. The read endpoint makes one possible later.
- Storing the planner's reasoning text or raw provider responses. This avoids size, and the model's reasoning isn't requested.
- Storing answers, retrieved chunk contents or views. The trace keeps step summaries, not evidence.
- Metrics dashboards, aggregation jobs, external log shipping, or any auth (single-user, local).
- Tracing the eval harness: it calls the runner directly, so it records nothing, and its cleanup is unchanged.

## Capabilities

### New Capabilities

- `assistant/plan-trace`: persistent per-question records of how the assistant planned and answered (planner choice, fallback reasons, plans, step outcomes, answer tier, usage), their retention, and the read paths (CLI and read-only API), across the Ask, team-coach and calc-coach scopes.

### Modified Capabilities

(none). Planning, answering and the coach behaviours are unchanged; the trace only records them.

## Impact

- **Backend:**
  - `app/agent/runner.py`: plan choice reports its reason and the keyword plan; the answer step records its tier; the trace is built at `done`.
  - New `app/agent/trace.py`: trace builder and recorder.
  - `app/models/user.py`: `QuestionLog.trace`.
  - One Alembic migration.
  - `app/api/{ask,teams,calc}.py`: shared recorder.
  - New `app/api/traces.py` and router registration.
  - A CLI module, plus a `make traces` target.
- **Tests:** trace contents per path (fast path, LLM plan, 429 fallback, no-key, re-plan, unhandled abstain, coach and calc scopes), best-effort writes, retention, read endpoint and CLI.
- **Docs:** `docs/architecture/ask-agent.md` and `docs/guides/local-dev.md`.
- **No new dependencies, no frontend changes, no change to the SSE contract.**
