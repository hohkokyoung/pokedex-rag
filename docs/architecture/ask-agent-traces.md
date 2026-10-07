# Ask agent: plan traces

Every answered question, on Ask, the team coach and the calc coach, stores a **plan trace**
with its `question_log` row (`trace` JSONB). The runner builds it just before `done` from what
it already holds, so it costs no LLM calls, and leaves it in `ctx.extra["trace"]`. The route
saves it best-effort with the question (a failed write only logs a warning). The trace
never goes to the client.

| Field | What it records |
|---|---|
| `planner` | `cached`, `keyword` or `llm` |
| `skip_llm` | why the LLM wasn't asked: `fast-path` (confident keyword plan) or `no-llm` (no key / `ASK_AGENT_ENABLED=false`) |
| `fallback` | why the keyword plan stood in for the LLM: `rate-limited`, `timeout`, `provider-error:<Type>`, `no-valid-steps` |
| `keyword` | the keyword plan and whether it was confident |
| `llm` | the LLM's plan (tool, args, why), also when rejected, plus `unhandled` and `needs_followup` |
| `replan` | steps a re-plan added, or why it failed |
| `steps` | each executed step's state, summary and time (incl. the coach context step) |
| `answer` | `tier` (`code`, `llm`, `no-llm`, `abstain`, `cached`) and an answer `fallback` reason |
| `usage`, `ms` | LLM calls and tokens; total time |

Strings are capped (reasons and summaries 200 chars, arg values 300), so a trace stays
under ~8 KB. Only the newest `TRACE_RETENTION` (default 2,000) rows keep a trace; older rows
keep their question, which personalization reads. Read them with `make traces` (see
[local development](../guides/local-dev.md#plan-traces)) or `GET /api/traces` and
`GET /api/traces/{id}`. When the runner gains a decision (a new fallback or answer path),
record it in the trace.
