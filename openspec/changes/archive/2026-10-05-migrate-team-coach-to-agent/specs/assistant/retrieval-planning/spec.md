# Spec Delta

## MODIFIED Requirements

### Requirement: Tools are limited to read-only Pokédex data
Every tool available on Ask SHALL read only from the locally ingested database or the user's local profile. No tool SHALL call an external data API. No tool on Ask SHALL change stored data, other than logging the asked question to history as today. In the team coach scope, the only tool that may change stored data is the explicit add, under the rules in `team-coach/coach-actions`; every other tool in any scope is read-only.

#### Scenario: Plan names an unknown tool
- **WHEN** a plan includes a step whose tool is not registered for the Ask scope
- **THEN** that step is not executed and is reported as an error step, and the remaining steps still run

#### Scenario: Invalid tool arguments
- **WHEN** a step's arguments fail validation against the tool's schema (for example an unknown stat name)
- **THEN** that step is reported as an error step with a short reason and contributes no evidence

#### Scenario: Team tool planned on Ask
- **WHEN** a plan on Ask names a team-only tool such as the add or set-edit tool
- **THEN** that step is reported as an error step and nothing is changed
