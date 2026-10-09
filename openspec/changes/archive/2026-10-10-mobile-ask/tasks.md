# Tasks

## 1. Backend: typed views

- [x] 1.1 Type `AskResponse.views` as the `View` union, add `step` to each view, and set `step` after the dump in the runner. Verify: `make test` (the runner test caught the overwrite and passes after the fix) and the OpenAPI lists every view schema.
- [x] 1.2 Add a backend test that `/api/ask` (keyless) returns typed views with their `step`, and that the schema declares the union with `kind` as discriminator. Verify: pytest.

## 2. App: API and stream

- [x] 2.1 Add `/api/ask` and `/api/ask/status` to the OpenAPI slice and run `make mobile-api`. Verify: the drift test, `flutter analyze`, and a recorded `/api/ask` fixture decoding into the generated union.
- [x] 2.2 Write the SSE frame parser and `AskRun` (plan, step, view, sources, delta, done, error; unknown view skipped; cancel on a new question). Verify with unit tests on a recorded event stream: steps reach terminal states, views decode, answer text concatenates, an unknown kind is skipped, and an error event sets the error.

## 3. App: screen and cards

- [x] 3.1 Add the Ask tab (third branch): question box, starters, keyless status, plan steps, streaming answer with tappable citations (source sheet), the "How it was answered" line, the unhandled notice, and the error/can't-reach states. Verify with widget tests over the fake stream: steps and text render, tapping [1] shows the snippet, and keyless status shows.
- [x] 3.2 Build the cards: ranking, pokemon_list, type_chart, move_list, learnset, learners, learn_check, each with its source numbers and Pokémon links. Verify with widget tests from recorded views of real questions.
- [x] 3.3 Add Ask next (follow-ups from cited Pokémon, hidden on abstain) and the profile sheet (preferred types PUT, favourites). Verify with widget tests: Garchomp cited → two follow-ups; picking Dragon PUTs `preferred_types` including dragon.

## 4. Check and docs

- [x] 4.1 In the Simulator, against the real server: a ranking question, a learn check, a type chart, a multi-part question, and a starter. Check citations and follow-ups. Restore any preferred-types change afterwards. Run `make test`, `make lint` and `make mobile-test`.
- [x] 4.2 Update `docs/architecture/ask-agent.md` (typed views), `docs/product/mobile.md` (Ask) and `docs/components/mobile.yaml`. Verify: `make test`.
