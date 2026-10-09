# Spec Delta

## Purpose

Lets the owner ask the team coach from the app's team page and act on its proposals,
with the same answers and the same write rules as the website's coach.

## ADDED Requirements

### Requirement: Coach on the team page
The app's team page SHALL offer the team coach: quick questions (the website's), a question box, and a thread of the questions asked while the page is open. The coach SHALL be unavailable while the team is empty. When an opponent is picked, questions SHALL be asked with that opponent.

#### Scenario: Quick questions
- **WHEN** the owner opens a team whose first member is Garchomp and no opponent is picked
- **THEN** the coach offers "What's my team's biggest weakness?", "Which type should I add for coverage?", "Give Garchomp its best set" and the drafting question

#### Scenario: Empty team
- **WHEN** the team has no members
- **THEN** the question box and quick questions are disabled with a prompt to add a Pokémon first

#### Scenario: Opponent picked
- **WHEN** an opponent is picked and the owner asks a question
- **THEN** the request carries that opponent, and a quick question asks how to beat it

### Requirement: Streamed coach answers
Each turn SHALL stream like Ask: the answer with tappable citations, the How-it-was-answered line with its steps, and the result cards. A failed stream SHALL show an error line in its turn; an unreachable server SHALL say so in the turn, not blank the page.

#### Scenario: Plain team question
- **WHEN** the owner asks "What's my team's biggest weakness?"
- **THEN** the turn shows the answer citing the team context, and the How line shows 0 planning calls

#### Scenario: Keyless or rate-limited server
- **WHEN** the server has no LLM key, or the LLM is rate-limited
- **THEN** the turn still shows the server's fallback answer (the report, an analysis brief or the candidate list), and asking for a set change says it needs a key

#### Scenario: Stream error
- **WHEN** the stream sends an error event
- **THEN** that turn shows the error message and the next question can still be asked

### Requirement: The owner applies coach proposals
A set change SHALL be shown was → now (ability, nature, item, EVs, moves added and dropped) and SHALL save only on **Apply**; after Apply, **Revert** SHALL restore the member exactly as it was. Candidates SHALL save only on **Add** (into the next empty slot) or, on a full team, **Replace…** → pick a member → **Confirm**; each SHALL offer **Revert**. An add the coach made for an explicit command SHALL offer **Undo**, which clears that slot. A proposal for the opponent SHALL be marked and saved to the opponent. A failed save SHALL show why on its card and change nothing else.

#### Scenario: Apply then revert a set
- **WHEN** the owner presses Apply on a proposed set for Garchomp, then Revert
- **THEN** the set is saved, then Garchomp's ability, nature, item, EVs, IVs and moves are back as they were

#### Scenario: Add a candidate
- **WHEN** the team has an empty slot and the owner presses Add on a candidate
- **THEN** the candidate fills the first empty slot and the card offers Revert, which clears that slot

#### Scenario: Replace on a full team
- **WHEN** the team is full and the owner picks Replace…, a member, then Confirm
- **THEN** that member's slot holds the candidate, and Revert restores the member exactly

#### Scenario: Undo an explicit add
- **WHEN** the coach answered "add Garchomp" by adding it
- **THEN** the card says which slot it went to and Undo clears that slot

#### Scenario: Nothing saves without a click
- **WHEN** the coach proposes a set or candidates and the owner presses nothing
- **THEN** the team on the server is unchanged

### Requirement: The page follows team changes
After any change made from the coach (the coach's own add, or an Apply, Add, Replace, Revert or Undo), the team page's slots and report SHALL refresh to the saved team.

#### Scenario: Report refreshes
- **WHEN** the owner applies a set from the coach
- **THEN** the slot shows the new set and the report is recomputed without leaving the page

### Requirement: Coach cards
Besides the Ask cards, the coach thread SHALL draw set changes, candidates (name, types, role and reason), explicit adds, and duels (who wins, who moves first, each side's moves and the first turns of the log).

#### Scenario: Duel
- **WHEN** an answer includes a duel
- **THEN** the card shows both Pokémon, the outcome, who moves first, both move lists and the turn log
