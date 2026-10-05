# Spec Delta

## Purpose

Guarantees that every assistant answer is built only from evidence the retrieval tools returned, cites that evidence consistently, uses code instead of an LLM wherever the data alone is the answer, and abstains when the data can't answer.

## ADDED Requirements

### Requirement: Answers use only tool evidence
The answer to a planned question SHALL be produced only from the evidence passages returned by that question's executed steps, plus the user's local profile hints when a profile tool ran. The answer SHALL NOT state Pokémon facts, names or numbers that are not in that evidence.

#### Scenario: Fact not in evidence
- **WHEN** the user asks for something the tools cannot retrieve, such as competitive usage percentages
- **THEN** the answer says the Pokédex data doesn't have it instead of guessing

#### Scenario: Off-topic question
- **WHEN** the user asks "What is the capital of France?"
- **THEN** the assistant abstains with a brief "not in the Pokédex data" style reply

### Requirement: Citations match the evidence list
All evidence passages from all steps SHALL be numbered once, in plan step order, as a single sources list. Every `[n]` citation in the answer SHALL refer to an entry in that list. The same list SHALL be sent to the client as the question's sources.

#### Scenario: Evidence from two steps
- **WHEN** step 1 returns 3 passages and step 2 returns 2 passages
- **THEN** the sources are numbered 1–5 with step 1's passages first, and a citation `[4]` refers to step 2's first passage

### Requirement: Closed-form results are answered by code
When every step of a plan is closed-form and returned evidence, the answer SHALL be rendered from the data by code without an LLM writing it. Closed-form steps are: a Pokémon ranking or count query, a learn check, move info, a type matchup, or a learner list. The rendered answer SHALL follow the usual shape (one direct opening sentence, then bullets for further items) with citations, so names, numbers, counts and citations can't be hallucinated.

#### Scenario: Ranking question
- **WHEN** the user asks "Top 5 Pokémon by base stat total"
- **THEN** the answer lists the five rows in order with their values and citations exactly as the query returned them

#### Scenario: Learn check
- **WHEN** the plan is a single learnset check for Garchomp and Earthquake
- **THEN** the answer states whether Garchomp learns Earthquake and how (method and level where known), with a citation, and no LLM answer call is made

#### Scenario: Closed-form mixed with descriptive steps
- **WHEN** a plan contains a ranking query and a semantic search step
- **THEN** the LLM writes the answer from all the evidence, and the ranking's view still shows the exact rows

### Requirement: Empty results are reported honestly
When a closed-form query matches nothing, the answer SHALL say that nothing matches the stated conditions, citing nothing. It SHALL NOT substitute other results.

#### Scenario: No match
- **WHEN** the plan is a single query for Fire types with Speed above 200 and it returns no rows
- **THEN** the answer says no Pokémon match those conditions

### Requirement: Extractive answer when no LLM can answer
When an answer needs an LLM but no LLM key is configured, or the answer call fails or is rate-limited (HTTP 429), the answer SHALL be composed from the same evidence by code, with the same citation numbering. It SHALL say that it is shown straight from the data. The request SHALL NOT end in an error for this reason.

#### Scenario: Keyless descriptive question
- **WHEN** no LLM key is configured and the user asks "Describe Snorlax"
- **THEN** the answer quotes Snorlax's profile and/or dex entry with citations and the "straight from the Pokédex" framing

#### Scenario: Answer call rate-limited
- **WHEN** the plan ran but the provider responds 429 to the answer call
- **THEN** the stream still delivers an extractive answer over the same sources and ends with `done`
