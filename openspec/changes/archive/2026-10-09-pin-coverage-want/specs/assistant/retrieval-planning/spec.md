# Spec Delta

## ADDED Requirements

### Requirement: Coverage lists Pokémon or moves as the question asks
Whether a coverage step lists Pokémon or moves SHALL be decided from the question's wording by code, the same way on every planner path. An LLM plan that chose otherwise SHALL be corrected before it runs or is cached. A question about attackers or Pokémon SHALL list Pokémon; one that asks for moves SHALL list moves.

#### Scenario: Attacker question lists Pokémon
- **WHEN** the user asks "Which special attacker has coverage against Dark?" and the LLM plans coverage with moves
- **THEN** the coverage step that runs lists Pokémon, and the cached plan lists Pokémon too

#### Scenario: Moves question lists moves
- **WHEN** the user asks "What moves beat Dark types?" and the LLM plans coverage with Pokémon
- **THEN** the coverage step that runs lists moves

#### Scenario: No key or rate-limited
- **WHEN** no LLM is configured, or the LLM planner is rate-limited, and the user asks "Which special attacker has coverage against Dark?"
- **THEN** the keyword plan's coverage step lists Pokémon
