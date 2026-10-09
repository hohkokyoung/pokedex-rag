# Spec Delta

## MODIFIED Requirements

### Requirement: Team context is always attached
Every coach question SHALL include team-context evidence without it being planned. The context covers the team report, each member's set, the deterministic team analysis and the per-slot suggestions. When an opponent is selected it also covers the opponent's members and the matchup. The team report SHALL be built by the server from the backend's ratings and matchup: both teams' overall grade with every area's verdict and fix, and with an opponent the matchup verdict and tally, their top threats with your best answer to each, the best lead, and the members that win no pairing. Clients SHALL NOT send report text. This evidence SHALL be citable like any other source and SHALL come first in the sources.

#### Scenario: Plain team question
- **WHEN** the user asks "What's my team's biggest weakness?"
- **THEN** the answer cites the team analysis, and no extra lookup is required to answer

#### Scenario: Opponent selected
- **WHEN** an opponent team is selected and the user asks "How do I beat them?"
- **THEN** the evidence includes the opponent's members and the matchup (verdict, best answers, threats)

#### Scenario: Same report for every client
- **WHEN** the website and the app ask the same question about the same teams
- **THEN** the team report in the evidence is identical, and it matches the text the website used to build for the same teams (except an empty opponent, below)

#### Scenario: Empty opponent
- **WHEN** the selected opponent has no members
- **THEN** the report has the team's rating and no opponent or matchup lines
