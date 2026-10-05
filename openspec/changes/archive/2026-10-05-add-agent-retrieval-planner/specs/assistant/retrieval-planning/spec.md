# Spec Delta

## Purpose

Turns each user question into an explicit plan of data-retrieval tool calls. The plan is decided by an LLM when that adds value, and by a names-first keyword planner otherwise. Questions with more than one part are answered from the local Pokédex data with as few LLM calls as possible.

## ADDED Requirements

### Requirement: Every question is answered from a retrieval plan
Every Ask question SHALL be answered by running a plan: an ordered list of 1–6 steps, each naming one available tool, its arguments, and a one-line reason. The plan SHALL come from either the LLM planner or the keyword planner, never from a fixed list of intents or routes.

#### Scenario: Single-intent question
- **WHEN** the user asks "Which Pokémon has the highest Attack?"
- **THEN** the plan contains a Pokémon query step sorted by Attack, descending
- **AND** the answer's top result is Kartana

#### Scenario: Multi-part question with an LLM available
- **WHEN** an LLM key is configured and the user asks "Which Fire types learn Will-O-Wisp, and what is Fire weak to?"
- **THEN** the plan contains a learnset step for Will-O-Wisp restricted to Fire types and a type-matchup step for Fire
- **AND** evidence from both steps is available to the answer

### Requirement: Keyword planner resolves names first
The keyword planner SHALL use no LLM. It SHALL first resolve Pokémon, move, ability, item and type names in the question against the ingested data, then pick tools from what was found and from keyword cues. A name that matches more than one kind of thing SHALL produce one step per kind. It SHALL produce at most 3 steps, and SHALL default to a semantic search step when nothing more specific applies.

#### Scenario: Move name alone
- **WHEN** the keyword planner receives "What does Earthquake do?"
- **THEN** the plan is a single move-info step for Earthquake, not a semantic search over Pokémon descriptions

#### Scenario: Move learners
- **WHEN** the keyword planner receives "Who learns Earthquake?"
- **THEN** the plan is a learnset step listing the learners of Earthquake

#### Scenario: Pokémon and move together
- **WHEN** the keyword planner receives "Can Garchomp learn Earthquake?"
- **THEN** the plan is a learnset check step for Garchomp and Earthquake

#### Scenario: Name that is both a type and a move
- **WHEN** the keyword planner receives "Tell me about Psychic"
- **THEN** the plan contains both a type-matchup step for Psychic and a move-info step for Psychic

#### Scenario: Ranking cue
- **WHEN** the keyword planner receives "Which Pokémon has the highest Attack?"
- **THEN** the plan is a Pokémon query step sorted by Attack, descending

#### Scenario: Pokémon profile, similarity and lore
- **WHEN** the keyword planner receives "Tell me about Snorlax", "Pokémon like Gengar", or "Which Pokémon live in volcanoes?"
- **THEN** it plans a Pokémon profile step for Snorlax, a similar-Pokémon step for Gengar, and a semantic search step, respectively

### Requirement: Fast path skips the LLM planner for simple questions
When an LLM is available, the keyword planner SHALL still run first. Its plan SHALL be used without calling the LLM planner only when it is confident: exactly one unambiguous name resolved (or none, for a single ranking or recommendation cue), and the question matches one of a fixed set of simple phrasings — profile, what-does-X-do, can-X-learn-Y, who-learns-Y, highest/lowest stat, Pokémon-like-X, where-to-catch-X, what-is-type-X-weak-to, or recommend-me-a-Pokémon. Every other question SHALL go to the LLM planner.

#### Scenario: Confident simple question
- **WHEN** an LLM key is configured and the user asks "Can Garchomp learn Earthquake?"
- **THEN** the keyword plan is used, the LLM planner is not called, and the plan reports planner `keyword`

#### Scenario: Simple lookups beyond moves
- **WHEN** an LLM key is configured and the user asks "Pokémon similar to Blaziken", "Where can I catch Pikachu?", "What is Fire weak to?" or "Recommend a Pokémon for me"
- **THEN** each is answered from its keyword plan (similar Pokémon, encounters, type chart, profile picks) without calling the LLM planner

#### Scenario: Ambiguous name
- **WHEN** an LLM key is configured and the user asks "Tell me about Psychic"
- **THEN** the LLM planner is called, because "Psychic" resolves to both a type and a move

#### Scenario: Several conditions
- **WHEN** an LLM key is configured and the user asks "Fastest non-legendary Fire type that learns Will-O-Wisp"
- **THEN** the LLM planner is called and its plan sets the type, legendary and move filters as explicit arguments

### Requirement: Tools are limited to read-only Pokédex data
Every tool available on Ask SHALL read only from the locally ingested database or the user's local profile. No tool SHALL call an external data API. No tool on Ask SHALL change stored data, other than logging the asked question to history as today.

#### Scenario: Plan names an unknown tool
- **WHEN** a plan includes a step whose tool is not registered for the Ask scope
- **THEN** that step is not executed and is reported as an error step, and the remaining steps still run

#### Scenario: Invalid tool arguments
- **WHEN** a step's arguments fail validation against the tool's schema (for example an unknown stat name)
- **THEN** that step is reported as an error step with a short reason and contributes no evidence

### Requirement: Filters are explicit tool arguments
Filters a planner decides, such as types, damage class, legendary/mythical inclusion, generation, game, and stat thresholds, SHALL be passed as tool arguments. Tools SHALL apply them as given rather than re-deriving them from the question text.

#### Scenario: Legendary exclusion on learners
- **WHEN** a plan has a learnset step for Earthquake with `legendary: false`
- **THEN** no legendary Pokémon appears among the returned learners, whatever the question's wording

### Requirement: Independent steps run concurrently
Steps that do not declare a dependency SHALL run concurrently. A step that declares a dependency SHALL run only after the steps it depends on finish. Each step SHALL be bounded by a timeout. A failed or timed-out step SHALL NOT fail the request.

#### Scenario: One step times out
- **WHEN** one of three independent steps exceeds its timeout
- **THEN** the other two steps' evidence is still used and the timed-out step is reported as an error step

### Requirement: Names are resolved against the database
Tools that take a Pokémon, move, ability, item or type name SHALL resolve it against the ingested data. Resolution includes case-insensitive and close-match matching, and forms. A name that can't be resolved SHALL produce an empty result, never invented data.

#### Scenario: Loose spelling
- **WHEN** a step asks for the Pokémon "charizrd"
- **THEN** the tool resolves it to Charizard and reports the resolved name in its step summary

#### Scenario: Nonexistent Pokémon
- **WHEN** a step asks for a Pokémon that does not exist in the data
- **THEN** the step completes as empty with a summary saying no match was found

### Requirement: Empty results are answers; re-plan is rare
A query that legitimately matches nothing (for example a filter no Pokémon meets) SHALL be treated as an answer, not a reason to re-plan. The assistant SHALL re-plan at most once per question, and only when a step errored or a name still could not be resolved after close-matching. The re-plan SHALL see only short per-step summaries and SHALL NOT repeat a step that already succeeded.

#### Scenario: Filter matches nothing
- **WHEN** a query step for Fire types with Speed above 200 returns no rows
- **THEN** no re-plan is made, and the answer reports that no Pokémon match

#### Scenario: Unresolvable name
- **WHEN** a step's Pokémon name cannot be resolved even by close match
- **THEN** one re-plan is made with that step's summary, and no further re-plan happens regardless of its outcome

### Requirement: Fallback to the keyword planner
The keyword planner's plan SHALL be used for every question when no LLM key is configured or the agent's LLM planning is disabled by configuration. It SHALL also be used for a single question when the LLM planning call fails, returns no valid steps, times out, or is rate-limited (HTTP 429). In those cases the LLM planning call SHALL NOT be retried.

#### Scenario: No key
- **WHEN** neither an Anthropic nor a Groq key is set and the user asks "What does Earthquake do?"
- **THEN** the keyword plan (move info for Earthquake) runs, and the plan reports planner `keyword`

#### Scenario: Planner rate-limited
- **WHEN** the provider responds 429 to the planning call
- **THEN** the question is answered from the keyword plan within the same request, with no planning retry

#### Scenario: Planner returns no usable steps
- **WHEN** every step in the LLM's plan is invalid
- **THEN** the question is answered from the keyword plan

### Requirement: LLM usage per question is bounded and measured
A question SHALL use at most three LLM calls: plan, optional re-plan, and answer. Questions answered by the fast path with a code-rendered answer SHALL use none. Each answer SHALL report how many LLM calls it used and their token usage. The planning prompt SHALL stay within a fixed size budget and include only the tools of the current scope.

#### Scenario: Fast path plus code-rendered answer
- **WHEN** an LLM key is configured and the user asks "Can Garchomp learn Earthquake?"
- **THEN** the answer reports 0 LLM calls

#### Scenario: Multi-part question
- **WHEN** the LLM planner plans two steps whose results need explaining
- **THEN** the answer reports 2 LLM calls (plan and answer) with their token counts

### Requirement: Repeated questions are served from cache
Plans, and answers that don't depend on the user's profile, SHALL be cached in memory per scope by normalized question text for the life of the backend process. A repeated question SHALL be served without new LLM calls. Answers from plans that read the user's profile SHALL NOT be served from cache.

#### Scenario: Same question twice
- **WHEN** the user asks "Which Fire types learn Will-O-Wisp?" twice
- **THEN** the second answer reports 0 LLM calls and has the same plan, views and sources

#### Scenario: Personalized question
- **WHEN** the user asks "Recommend a Pokémon for me" twice and changes their favourites in between
- **THEN** the second answer reflects the updated profile

### Requirement: Works on both supported providers
LLM planning SHALL work with both supported providers (Groq and Anthropic) and produce the same plan structure on either. When both keys are present, the provider preference is unchanged from today.

#### Scenario: Groq only
- **WHEN** only a Groq key is configured and a question is not fast-pathed
- **THEN** the plan is produced with schema-constrained output and reports planner `llm`

#### Scenario: Anthropic only
- **WHEN** only an Anthropic key is configured and a question is not fast-pathed
- **THEN** a plan with the same structure is produced and reports planner `llm`
