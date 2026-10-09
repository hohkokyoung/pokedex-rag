# Proposal

## Why

Teams is the website's most-used tool mid-game: build six with legal sets, see the
grade, test against another team. The backend already computes everything the page
shows, including grades, profile, strategy axes, the matchup and the summary
(ADR-007/009). So the app can bring Teams over as screens, with no new rules.

## What Changes

- **Navigation:** a bottom bar, Pokédex | Teams. Later phases add Ask and Tools.
- **Team list:** every saved team as a card, matching the website's:
  - grade badge and score /100, play style and the AI summary;
  - weak to / resists / hits-hard facts, the six letter grades and the top fixes;
  - **New team** (named) and **Delete** (confirmed).
- **Team page:**
  - Rename, plus six slots showing types, role and BST.
  - An empty slot opens a Pokémon picker (search by name or number, forms included).
  - A filled slot opens the **set editor**:
    - only legal choices: ability (hidden marked), item (searchable held items),
      nature (+/− stats), EVs (0–252 each, 510 total), IVs (0–31) and up to 4 moves
      from the species' learnset;
    - **Save** writes the slot and **Remove** clears it.
- **Compare with…** another saved team (kept as the page's opponent):
  - the matchup verdict and scorecard;
  - their threats, our pressure and the engine's advice.
- **The report:**
  - grade, score, style, lean, biggest gap and the AI summary, with ↻ Regenerate;
  - the six grades with headline and fix;
  - How it plays (strategy axes, now vs with learnable moves) and the type profile;
  - Sets per member, with **Use suggested** (the engine's suggestion, filling only the
    empty parts);
  - Defence per attacking type.

No backend change. All of it uses existing team, analysis, strategy, summary and
builder endpoints.

## Out of scope

- The team coach (phase 5) and duels.
- Team notes and the opponent "kind" flag (website-only fields).

## Capabilities

### New Capabilities
- `mobile/teams`: building, grading and comparing saved teams in the app, from the
  backend's teams API.

### Modified Capabilities
<!-- None -->

## Impact

- **Mobile:** a shell route with a NavigationBar, `features/teams/` (list, team page,
  picker, set editor, report sections), repository methods, and many more paths in
  the OpenAPI slice (teams CRUD, slots, build, analysis, strategy, summary/refresh;
  builder moves/abilities/items/natures).
- **Backend:** none.
- **Docs:** `docs/product/mobile.md`, the mobile manifest.
- **LLM:** 0 calls, except ↻ Regenerate, which is the website's same single background
  summary call (keyless → rules summary).
