# Tasks

## 1. Plumbing

- [x] 1.1 Add `/api/calc/ask` to the OpenAPI slice (`make mobile-api`); decode `damage`, `survive`, `build_proposal`. Verify: drift test, analyze, decode test on recorded views.
- [x] 1.2 Record keyless calc-coach streams (damage, survive, keyless build) and write a build-proposal stream by hand. Verify: fixtures decode; recorder reports 0 LLM calls.

## 2. Coach

- [x] 2.1 Coach state + request (state, hits from the server turn, proposal + thread) + stream. Verify: unit/widget test on the request body for "Can Garchomp OHKO Corviknight?".
- [x] 2.2 UI: quick questions, box, conversation (answer without [n], How line, error), damage and survive cards with Apply / Revert, build card with diff, move chips, Apply / Revert. Verify widget tests: survive Apply → EVs set, Revert → restored; build Apply → set + move, Revert → previous; revised build resets Apply; keyless build shows no card.

## 3. Check and docs

- [x] 3.1 Simulator: a damage and a survive question (0 LLM). `make test`, `make lint`, `make mobile-test`.
- [x] 3.2 Docs. Verify: `make test`.
