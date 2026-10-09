# Spec Delta

## MODIFIED Requirements

### Requirement: Non-streaming Ask returns the plan and views
The non-streaming Ask response SHALL contain the answer, the `planner`, the executed steps with their final states, the views, the sources, and usage. It SHALL NOT contain a `route`. Its views SHALL be declared in the API schema as a union of the view types, discriminated by `kind`, each with the id of the plan step that produced it.

#### Scenario: Non-streaming answer
- **WHEN** a client POSTs a question to the non-streaming Ask endpoint
- **THEN** the response contains the planner, the steps with terminal states, the views, the sources and usage, and no `route` field

#### Scenario: Views are typed in the schema
- **WHEN** a client reads the API schema
- **THEN** the Ask response's views are a `kind`-discriminated union of the view types (ranking, pokemon_list, type_chart, move_list, learnset, learners, learn_check and the coach views), each with an optional `step`

#### Scenario: Each view keeps its step
- **WHEN** a streamed or non-streamed answer includes a view
- **THEN** the view's `step` is the id of the plan step that produced it
