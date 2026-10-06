# Evaluation

A labelled eval set (`backend/eval/dataset.py`) and harness (`backend/eval/harness.py`)
for the agent: 45 Ask cases, 10 team-coach cases and 7 calc-coach cases.

Each case states the question and the **tools it expects** (`expect_tools`, with the
arguments that matter), plus — for answer grading — facts the answer must contain or
an expectation that it abstains.

## Running it

```bash
make eval
```

```bash
cd backend && uv run python -m eval.run --keyless
```

```bash
cd backend && uv run python -m eval.run --plans-only
```

| Mode | LLM calls | Measures |
|---|---|---|
| `make eval` | yes (if keyed) | plans, retrieval recall, answer correctness, citations, abstention, LLM calls/tokens |
| `--keyless` | none | the keyword planner's plans and recall only |
| `--plans-only` | planning only | plan accuracy without answer calls |

`make eval` spends tokens. It's paced to Groq's free-tier limit (`--tpm`, default
8000 tokens per minute); a 429 is recorded and handled, not retried. Ask before
running it on a shared key.

## When to add cases

- A new tool or planner phrasing → a case with its `expect_tools`.
- A bug fixed in planning or retrieval → a case that would have caught it.
- Retrieval/coach changes in OpenSpec must include eval updates (`openspec/config.yaml`).
