## ADDED Requirements

### Requirement: A report that reads at a glance
The team report's type profile SHALL put each group's label above its chips, with shared counts inside the chip. "Hits hard" SHALL name only the types it misses, when there are few. Defence SHALL list the types more of the team is weak to than resists, with "Show the other N" for the rest, and omit an empty resist line.

#### Scenario: Strong coverage
- **WHEN** a team hits 17 of 18 types hard
- **THEN** the report reads "17 of 18 types · misses" and the one type
