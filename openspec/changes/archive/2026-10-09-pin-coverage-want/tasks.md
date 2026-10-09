# Tasks

## 1. Pin coverage `want` to the question

- [x] 1.1 Failing runner test: an LLM plan with the wrong `want` runs and caches the question's `want` (both directions)
- [x] 1.2 `_pin_coverage_want` in `runner._choose_plan`, before the plan cache; keep the LLM's original plan
- [x] 1.3 Record overrides in the trace (`corrected`)
- [x] 1.4 Eval: x3 expects `want="pokemon"`
- [x] 1.5 `make test`, `make lint`, keyless eval

## 2. Docs

- [x] 2.1 `docs/architecture/ask-agent-traces.md`: the `corrected` field
