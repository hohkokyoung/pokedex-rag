# Design

## Context

### What exists
Phases 1–2 (archived) built the agent core in `app/agent/`, used by Ask (scope `ask`) and
the team coach (scope `team`). That covers:
- tool registry with scopes and a `plannable` flag
- names-first keyword planner with a fast path
- LLM planner (strict per-tool `anyOf`, roster line, empty plans allowed outside Ask)
- built-in context step prepended by the runner
- code renderers
- SSE events, the frontend run reducer (`runState.ts`), `PlanSteps` and `ViewBlock`

### The calculator today (`frontend/app/page.tsx`, `DamageCalcTile`)
- **State:** 4 slots (0–1 your side, 2–3 the opponent's; singles uses 0 and 2). Each slot
  holds a Pokémon (`CalcMon`: id, form, types, base stats), nature, EVs, IVs, item,
  ability, current HP % and a chosen move. Plus aims, level, singles/doubles, and field
  toggles: weather, terrain, Reflect, Light Screen, crit, burn, Friend Guard.
- **Maths:** `calcHit` computes one hit: stats via `statFull`/`natMul`, then base damage,
  STAB, `typingEff`, field and item/ability modifiers, giving min–max % and hits-to-KO.
- **Turn simulation:** `hitsFor` + `steps` add move order, spread/Helping Hand targeting,
  Focus Sash carry-over and the battle-log text.
- **The coach box:** `runCoach` / `followUp` call `suggestBuild` (the
  `/api/builder/builds/suggest` endpoint) with an optional current build and chat
  thread. They show a was → now card with Apply/Revert into the calc, quick chips, and a
  "Full moveset" picker.

### Elsewhere
- `battle.py` is the team engine: average roll, Lv 50. Its numbers differ from the
  calculator's on purpose.
- The frontend has no test runner, but Node 26 strips TypeScript types natively.

Motivation: see `proposal.md`. Requirements: see `specs/calc-coach/*` and the modified
`specs/assistant/result-views`.

## Goals / Non-Goals

**Goals:**
- One damage formula, in two languages, provably equal on the reference cases.
- The calc coach answers damage, threshold, build and dex questions from the calculator's
  real state, with damage and threshold answers costing 0 LLM calls.
- Reuse the agent core, `build_suggest` and the existing calc coach card.

**Non-Goals:**
- Changing `battle.py` or team analysis numbers.
- Porting the turn simulation or doubles targeting to the backend. Context hits come from
  the client (Decision 4), and tools compute single hits.
- Saving calculator builds to teams.

## Decisions

### 1. Extract the maths into `frontend/lib/damageCalc.ts`
- **What moves out of `page.tsx` / `components/calc/fields.tsx`, unchanged in
  behaviour:**
  - types `SKey`, `EVs`, `DcSet`-like `CalcSide`, `CalcMoveIn`, `DcField`, `DcResult`
  - `NAT`, `natMul`, `statFull`
  - `TYPE_BOOST`, `RESIST_BERRY`
  - `calcHit`
- **Imports:** relative only (`./typeChart` for `typingEff`; its one import is type-only
  and erased). `fields.tsx` re-exports `NAT`, `natMul`, `statFull` and the types, so other
  imports don't change.
- **Why extract:** a pure module is what both the app and the reference-case script can
  import. `page.tsx` is a React file Node can't load.

### 2. Reference cases tie the TypeScript and Python versions together
- **Generator:** `frontend/scripts/damage-fixtures.ts`, run with
  `node --import ./scripts/ts-resolve.mjs scripts/damage-fixtures.ts`. The ~10-line hook
  appends `.ts` to extensionless relative imports. No new dependency.
- **What it writes:** `backend/tests/fixtures/damage_cases.json`, about 250 cases.
  - **Hand-picked:** immunities, 4×, STAB/Adaptability, Huge Power, Technician ≤ 60,
    Choice Band/Specs, Life Orb, Expert Belt, type boosters, resist berries, Assault
    Vest, Eviolite, Thick Fat, Multiscale at full and lower HP, Filter/Solid Rock, Tinted
    Lens, rain/sun, terrains, Reflect/Light Screen in singles and doubles, crit ignoring
    screens, burn with and without Guts, doubles spread, Helping Hand, Friend Guard,
    Lv 50 and Lv 100, current HP < 100.
  - **Seeded random combinations,** using a deterministic LCG, over embedded base stats
    for about 20 species.
  - Each case stores the inputs and the full `DcResult`.
- **How it's checked:** `backend/tests/test_damage_calc.py` loads the JSON, runs the port,
  and asserts `minPct`/`maxPct` (±0.01), `ko`, `te`, `stab`, `A`, `D` and `base` are
  equal.
- **Regenerating:** the fixture records the generator's version. CLAUDE.md says to
  regenerate whenever `damageCalc.ts` changes. `make damage-fixtures` runs the script.
- **Rejected — calling the TS from Python at test time:** it needs Node in the backend
  container and in CI. Rejected — no shared check at all: the two would drift silently.

### 3. Backend port `app/services/damage_calc.py`
- **A line-for-line port** of `natMul`, `statFull` and `calcHit`. `Math.floor` becomes
  `math.floor` and the multiplication order is kept, so floating-point rounding matches.
  The item and ability names are the calculator's display names.
- **Type chart:** a copy of the frontend's static chart in `damage_calc.py`, because the
  results must match the calculator exactly and the frontend chart is what the calculator
  uses. A test asserts it equals the DB chart (`matchups._chart`), so the copy can't drift
  from the data either.
- **Also in the module:**
  - `survive(defender, attacker, move, field)`, described in Decision 6
  - `apply_changes(side, changes)` for what-ifs
- **Rejected — reusing `battle.damage_pct`:** different maths (average roll, Lv 50, no
  field), so it would contradict the screen.

### 4. Calc state and the built-in `calc_context` step
- **Request schema** for `POST /api/calc/ask` (`schemas/calc.py`):
  - `question`, `level`, `doubles`
  - `field{weather, terrain, reflect, lightscreen, crit, burn, friend_guard}`
  - `slots[{slot, side, pokemon_id, form_id, name, nature, evs, ivs, item, ability, hp,
    move?{name}, aim?}]`
  - `focus`
  - `hits[{from, to, move, min_pct, max_pct, ko, te}]`: the calculator's own turn result
  - `proposal?{slot, build, thread}`
- **The server doesn't trust client stats.** It resolves types, base stats and the
  chosen move's type/class/power from the DB (`PokemonForm` for forms). The client's
  `hits` are used verbatim as "what the calculator shows", because they include the turn
  simulation that isn't ported.
- **`calc_context`** (built-in, `plannable=False`, scope `calc`) produces chunks for:
  - each filled slot, with its set and computed Lv-N stats
  - the field
  - the calculator's hits, labelled as the calculator's results
  - the current proposal and the last 3 thread turns
  - Note: a calc coach note (answer from the calculator state and tool results; never
    invent damage numbers).
- **The runner's `_with_context`** generalises from team-only to `{team: team_context,
  calc: calc_context}`. Coach caching stays off for `team` and `calc`, since their state
  is mutable.

### 5. Calc tools (`app/agent/calc_tools.py`, scope `calc`)

| Tool | Args | Does | View | Closed-form |
|---|---|---|---|---|
| `damage_calc` | `attacker: str`, `defender: str`, `move?: str`, `changes: [{who: attacker\|defender\|field, key, value}]` | port `calc_hit` for the current state; with changes, also the what-if | `damage` | yes |
| `survive_threshold` | `defender: str`, `attacker: str`, `move?: str` | Decision 6 | `survive` | yes |
| `propose_build` | `pokemon: str`, `request: str` | `build_suggest(attempts=1, current=proposal if same slot, history=thread)` | `build_proposal` | yes (why = answer) |
| Ask dex tools | — | already scoped to `team`; add `calc` | — | as on Ask |

- **Names resolve against the calc slots** by name, falling back to the focused slot for
  the attacker and its aim for the defender. The move defaults to the slot's chosen move.
  A named move must be in that Pokémon's legal learnset (`builder.legal_moves`).
- **`changes` keys:** `item`, `ability`, `nature`, `evs` ("252 Atk / 4 HP"), `hp`,
  `weather`, `terrain`, `crit`, `reflect`, `lightscreen`, `burn`. Unknown keys or values
  make the step an error. Items and abilities outside the calculator's modelled lists are
  allowed and simply don't change damage, as in the UI, which marks them that way.
- **Prompt budget:** the calc planning prompt must stay ≤ 10,500 characters, the same
  budget as team. The calc tool schemas are deliberately small (`changes` is one array of
  `{who, key, value}` strings).

### 6. Survival threshold algorithm
- **The goal:** find the defender's HP and relevant defense EVs (Def for physical, SpD
  for special) that survive the attacker's maximum damage from the defender's current HP.
- **The search:** every (HP EV, Def EV) pair in steps of 4 up to 252 each, keeping the
  defender's other EVs, with total ≤ 508. That's ~4k `calc_hit` evaluations, which is
  cheap. Pick the smallest total investment, preferring HP on ties because it helps
  against both attack types.
- **Nature fallback:** if EVs alone aren't enough, retry with a nature that raises the
  defense stat and lowers the defender's less useful attack stat (the lower of its Atk
  and SpA).
- **Result:** `survives`, `needed{hp, def|spd, nature?}`, `range` at that spread, and
  `current` (the range at today's spread). If nothing survives: `survives=false`, plus
  the best spread and its range.
- **Already survives** (found in the browser check): if today's spread already lives,
  the view says so (`already=true`) and offers no Apply — the minimal spread could be
  *less* bulk than the user has. When the free EVs are what rule survival out, the text
  says "with the EVs it has free (the rest are in Atk / Spe)", not "any legal spread".

### 7. Planning the calc scope
- **Keyword planner (`scope="calc"`, using the slot roster):**
  1. **KO / damage cues** ("OHKO", "2HKO", "KO", "how much (damage)", "does X do") +
     resolvable slots → `damage_calc`. "with <item/nature/…>" is parsed into `changes`
     when it names a known item, nature, or EV spread. Confident when the slots resolve
     and nothing else is asked.
  2. **Survive cues** ("survive", "live", "tank") → `survive_threshold`. Confident.
  3. **Build cues** ("best build", "build", "set", "make it …", "bulkier", "faster",
     "special set") → `propose_build` for the focused slot (or the named one). Confident.
  3b. **With a proposal on the table**, an imperative tweak ("no Choice item", "swap X
     for Y", "use … instead") → `propose_build` to revise it (the old follow-up path),
     confident. "Explain the EVs" stays a plain question.
  4. **Otherwise the Ask rules** (dex lookups), filtered to calc-scoped tools.
  5. **Nothing → no extra steps** (plain question, answered from the context). Confident.
- **LLM planner:** `plan_schema("calc")`, a calc roster line ("Calc (Lv 100, singles):
  yours Garchomp [Earthquake]; foe Salamence [Dragon Claw]; focused Garchomp"), calc
  rules, and 3 few-shots (OHKO with a what-if, survive, build + damage).

### 8. Answers and views
- **New view models:**
  - `DamageView{attacker{slot,name}, defender{slot,name}, move{name,type,damage_class,
    power}, current{min_pct,max_pct,ko,te,stab}, whatif?{changes, min_pct, max_pct, ko},
    apply?{slot, fields}}`
  - `SurviveView{defender, attacker, move, survives, needed{hp, stat, ev, nature?},
    range{min_pct,max_pct}, current{min_pct,max_pct}, apply{slot, fields}}`
  - `BuildProposalView{slot, pokemon, build: BuildSuggestion}`
- **Renderers:**
  - damage: "Garchomp's Earthquake does 84–99% to Salamence — a 2HKO (a high roll can
    OHKO from 95% HP)", plus a what-if bullet
  - survive: "Salamence survives Close Combat with 252 HP / 124 Def (Impish): 71–84%"
    or "can't survive…"
  - build: the build's `why`
- **KO wording, from the calculator's convention** (min damage vs current HP), so it
  matches the battle-log text:
  - `ko == 1` → "guaranteed OHKO"
  - max ≥ current HP but min below it → "possible OHKO (high rolls)"
  - otherwise "nHKO"

### 9. Frontend
- **`lib/api.ts`:** `calcAskStream(state, question, handlers)` plus the three view types.
- **`page.tsx` coach box:**
  - `sendCoach` builds the state from `sets`, `mvs`, the field toggles, `hits`, `focus`
    and `coach` (proposal + thread) and streams with the shared reducers.
  - Each turn is appended to the coach thread, and compact `PlanSteps` show while it runs.
  - A `build_proposal` view sets `coach.build`; the existing card, Apply/Revert, "Full
    moveset" chips and quick chips are unchanged.
  - `damage` and `survive` views render as compact cards inside the coach box, with an
    Apply button when they carry `apply` (patching the calc slot, Revert restoring it).
- **Removed:** the direct `suggestBuild` calls (`runCoach` / `followUp` become
  `sendCoach`). `suggestBuild` stays in `api.ts`, because nothing else uses it and
  removing it is optional cleanup, not required.

### Existing modules: reused, slimmed, removed
- **Reused:**
  - `build_suggest.suggest_build` (`attempts=1`, `usage`)
  - the agent core (planners, executor, runner, renderers, `runState`, `PlanSteps`)
  - the Ask dex tools
  - `builder.legal_moves`
  - `pokemon_query` for forms
- **Moved:** `calcHit` and its helpers, from `page.tsx`/`fields.tsx` to
  `lib/damageCalc.ts` (re-exported).
- **Removed:** `page.tsx`'s direct `suggestBuild` calls.

### Per-question LLM budget (calc)

| Question | Plan | Build coach | Answer | Total |
|---|---|---|---|---|
| "Can Garchomp OHKO Salamence?" (fast path) | 0 | 0 | 0 (code) | 0 |
| "How much Def to survive Close Combat?" (fast path) | 0 | 0 | 0 | 0 |
| "Best build" / "make it bulkier" (fast path) | 0 | 1 | 0 (why) | 1 |
| "Who wins this?" (plain, context only) | 0 | 0 | 1 | 1 |
| Mixed ("OHKO with Choice Band, and a bulkier set?") | 1 | 1 | 0 | 2 |

### Eval
- Calc cases in `eval/dataset.py` (`CalcCase`): a fixed calc state (Garchomp vs Salamence,
  singles, Lv 100) plus questions with `expect_tools` and `fast_path`. They cover OHKO,
  a what-if with an item, survive, best build, make-it-faster, a dex lookup, and a plain
  question.
- `evaluate_calc` runs keyless (keyword plans), and with an LLM in `--plans-only` or full
  mode, like the coach eval.

## Risks / Trade-offs

- **[The TS and Python maths drift]** → The reference-case test fails on any mismatch.
  The fixtures are regenerated with one command, and CLAUDE.md says when.
- **[Floating-point differences between JS and Python]** → The port keeps the operation
  order and `floor` semantics. Percentages are compared to ±0.01, and the KO counts
  exactly.
- **[Client-sent state could be stale or inconsistent]** → Types, stats and moves are
  re-resolved server-side. Client `hits` are only labelled as the calculator's display.
  Tools always recompute.
- **[The calc prompt grows past budget]** → Compact `changes` schema, scope-filtered Ask
  tools, and a prompt-size test.
- **[Survive search cost]** → At most ~4k (×2 with natures) pure-Python `calc_hit` calls,
  about 10 ms. A test bounds the run time.

## Migration Plan

- **No migrations.** Backend and frontend ship together (new endpoint, coach box
  rewired). `/api/builder/builds/suggest` stays.
- **Rollback:** a git revert. `ASK_AGENT_ENABLED=false` falls back to keyword plans for
  the calc scope too.

## Open Questions

- The exact species list and seed for the random reference cases. Chosen during
  implementation; it doesn't affect the specs.
