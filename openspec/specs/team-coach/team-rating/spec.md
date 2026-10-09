# team-coach/team-rating Specification

## Purpose

Grades a saved team and describes what kind of team it is, deterministically and on the
server, so every client (the website, a future mobile app) and every server feature
shows the same rating for the same team.

## Requirements


### Requirement: The backend rates every non-empty team
The team analysis for a team with at least one member and no opponent SHALL include a rating: an overall score 0–100, a letter grade (A/B/C/D/F), whether the overall is capped because the roster isn't six distinct species, the ceiling the roster can reach, and per-type coverage and threat detail. It SHALL also include six area grades (Coverage, Defence, Speed, Roles, Sets, Roster), each with a score, grade, one-line headline and fix text or none.

#### Scenario: Full team
- **WHEN** a client requests the analysis of a team with six distinct members and no opponent
- **THEN** the response contains a rating with an overall score, a grade, `capped` false, a ceiling of 100, six area grades, 18 coverage entries and 18 threat entries

#### Scenario: Partial team is capped
- **WHEN** a client requests the analysis of a team with three distinct members
- **THEN** the rating's `capped` is true, its ceiling is 50, and its overall is the weighted area score scaled by 3/6

#### Scenario: Duplicate species
- **WHEN** a team holds two of the same species
- **THEN** the Roster area counts that species once, its headline names the repeated species, and its fix asks the user to swap the second one

#### Scenario: Empty team
- **WHEN** a client requests the analysis of a team with no members
- **THEN** the rating and profile are absent

### Requirement: The rating is independent of the selected opponent
The rating and profile SHALL describe the team on its own. When the analysis is requested with an opponent, the rating and profile SHALL be absent from that response, and clients SHALL read them from the opponent-free analysis. A team's grade is then the same on the team list and on its detail page, whichever opponent is selected.

#### Scenario: Analysis with an opponent
- **WHEN** a client requests a team's analysis with an opponent selected
- **THEN** the response contains the vs-opponent comparison and no rating or profile

#### Scenario: Same grade on the list and the detail page
- **WHEN** the user opens `/teams` and then the team's detail page with an opponent selected
- **THEN** both pages show the same overall score, grade and area grades

### Requirement: The backend profiles every non-empty team
The opponent-free team analysis SHALL include a profile with these fields:
- play style and the numbers behind it
- physical/special lean and the member counts behind it
- average stats as built, and the average base-stat total
- members by speed, and how many reach the fast threshold
- most common member types
- types the team is weak to, hits super-effectively and resists, with net counts
- moves set, items held and priority moves
- a one-line gist

#### Scenario: Profile uses stats as built
- **WHEN** a member has EVs, IVs or a nature that change its stats
- **THEN** the profile's style, lean and speed figures use that member's as-built stats, not its base stats

#### Scenario: One-member team still shows weaknesses
- **WHEN** a team has a single member that is weak to a type
- **THEN** the profile lists that type among the types it is weak to, even though the Defence grade only counts types hitting two or more members

### Requirement: The rating matches the previous client rating exactly
For the same team and analysis, the backend rating and profile SHALL equal the values the website computed before this change. That covers every score, grade, count, ordering and text string. The thresholds, weights and wording SHALL NOT change as part of this move.

#### Scenario: Golden parity
- **WHEN** the backend rates each recorded reference team
- **THEN** the rating and profile equal the recorded output of the previous client-side rating for that team, field by field

#### Scenario: Rounding parity
- **WHEN** an area score falls exactly on a .5 boundary
- **THEN** it rounds half up, as the previous client rating did, not half to even

### Requirement: Rating never calls the LLM
Computing the rating and profile SHALL NOT call the LLM. It SHALL work identically with no LLM key configured and while the LLM provider is rate-limiting, and opening a team page SHALL still cost zero LLM calls.

#### Scenario: No LLM key
- **WHEN** no LLM key is configured and a client requests a team's analysis
- **THEN** the response contains the full rating and profile

#### Scenario: Provider rate-limited
- **WHEN** the LLM provider is returning 429s and a client requests a team's analysis
- **THEN** the rating and profile are returned unchanged and no LLM call is attempted

### Requirement: Clients show the backend rating
The team list cards, the team detail page's report and its matchup text SHALL display the rating and profile the backend returns. They SHALL NOT compute their own. Clients MAY still choose how a grade is styled (its tone) and how vs-opponent factors are worded.

#### Scenario: Team card
- **WHEN** the user opens `/teams`
- **THEN** each non-empty team's card shows the grade, score, style and lean from that team's backend rating and profile

#### Scenario: Grade updates after an edit
- **WHEN** the user changes a slot on the team detail page
- **THEN** the report re-reads the opponent-free analysis and shows the backend's new rating
