# Ask agent: planners

How a question becomes a plan. The order they run in, and when the LLM is skipped, is
in [ask-agent.md §3](ask-agent.md#3-choosing-a-planner).

## Keyword planner (`keyword_planner.py`)

1. **Find names.** `names.find_in_text` scans the question against every Pokémon, form,
   move, type, ability and item name in the DB, longest first ("Mewtwo" before "Mew",
   "Fire Punch" before "Fire"). A span can match two kinds ("Psychic" = type and move).
2. **Pick a tool** from what was found and a few cue words (`_decide`):
   Pokémon + move → `learnset`; move alone → `move_info`; Pokémon + "like" →
   `similar_to`; type + "weak" → `type_matchup`; nothing named → `query_pokemon` if a
   ranking/filter is recognised, else `semantic_search`.
3. **Fill the other args** with small parsers: `nlfilters.restricted_filters`
   (legendary/mythical, with negation), physical/special, learn method, a level cap
   ("below lvl 30" → `max_level=29`, "by level 30" → 30; implies level-up), game
   (`learnset.find_game_in_text`), stat words and thresholds (`sql_retrieval.plan`). A game
   the question clearly names but no version group matches ("in the gizmo game") goes in the
   plan's `unhandled` (`learnset.unresolved_game`), so the answer says it wasn't applied.

**Confident** means: one valid step, every name has one meaning, no extra filters
(game, method, types, legendary), and the question — with names replaced by
placeholders — matches a fixed template:

```
"Can Pikachu learn Surf?"  →  "can P learn M"  →  confident
"Can Pikachu learn Surf in Scarlet?"            →  not confident (game filter) → LLM
```

The keyword planner matches names exactly (after lowercasing and stripping
punctuation). Misspelled names are fixed later, inside the tools (`names.resolve`,
`difflib` ≥ 0.85).

## LLM planner (`llm_planner.py`)

One strict-JSON call. The schema is built from the tools' Pydantic models: each step is
an `anyOf` of per-tool objects, so choosing `learnset` forces learnset's argument
shape. Groq uses `json_schema` mode, Anthropic a forced tool call; SDK retries are off.

The prompt lists tool names + one-line descriptions, rules ("set a filter only when
the question states it", "use names as written", "never supply a Pokémon's stats from
memory"), and four examples. It must stay under `PROMPT_BUDGET` (11k characters,
~2.75k tokens) for Groq's free-tier tokens-per-minute limit; a test fails any scope
that goes over. **The budget is nearly full** (Oct 2026: ask ~10.0k, team ~10.7k, calc
~10.5k) — a new tool in team or calc scope will likely need a shorter description or
another tool trimmed. Check with `llm_planner.prompt_size(scope)`.

The plan also has `unhandled`: constraints no argument can express ("cute"). The
answer opens by saying they weren't applied.

## Validation (`plan.py`)

Both planners' raw steps go through `make_step`: the tool must exist in this scope,
nulls are dropped for non-nullable fields, `model_validate` checks types and enums,
and `legendary=False` also sets `mythical=False` (colloquial "non-legendary"). A bad
step gets `error` instead of raising.
