## Why

The owner reviewed the app screen by screen against the website and found these
problems:

- **Type filters:** the Pokédex allowed only two types, and the faded type chips were
  hard to read.
- **Ask:** the answer didn't look like the website's; the send button sat against the
  text; the suggestions were spaced-out chips.
- **Catch rate:** the buttons were too big, and the situation was buried under twenty
  balls.
- **Type calculator and damage calculator:** both looked plain and heavy.
- **Team report:** it showed too much, in cramped type chips.
- **Forms:** a Pokémon with many forms (Pikachu has 20) shows a wall of chips.

## What Changes

- **BREAKING (API):** the catalog's `type` filter matches any of the requested types,
  not all of them. The website and app pick any number of types.
- Type pickers take the website's look: grey names, and a picked type in its colour
  with a soft glow of it.
- **Ask:** answers follow the website's layout:
  - the first sentence is the verdict;
  - list rows lead with artwork;
  - citations are small red chips;
  - "Note:" is an amber notice.

  Suggestions are one panel of rows, follow-ups come after the answer, and the send
  button has room around it.
- **Catch rate:** the inputs come first (status as one compact control, HP, then the
  situation with sliders and switches). The best six balls sit on a panel with
  "Show all"; the formula folds away.
- **Type calculator:** results are grouped by verdict (Takes more from, Resists, Immune
  to, Hits), each with a coloured multiplier, as on the website. The Pokémon page's
  matchups share the same layout.
- **Damage calculator:**
  - set fields are settings rows (label left, value right), not boxed dropdowns;
  - an icon button changes the Pokémon;
  - field and math fold away;
  - the roster cards are lighter.
- **Team report:**
  - type chips get more room, with counts inside the chip;
  - "Hits hard" names only the types it misses;
  - Defence lists the problem types first, with "Show the other N".
- **Forms:** one pill names the form shown and opens a sheet of forms.

## Capabilities

### New Capabilities
- `pokedex/catalog-types`: how the catalog's type filter combines several types.

### Modified Capabilities
- `mobile/pokedex-browsing`: any number of types; forms from a pill.
- `mobile/design-language`: type pickers in the website's style.
- `mobile/ask`: the website's answer layout and suggestion rows.
- `mobile/tools`: catch rate and type calculator layouts.
- `mobile/teams`: a report that reads at a glance.

## Impact

- **Backend:** `services/pokemon_query.py` (any-match) and the `/api/pokemon` docs.
- **Website:** `PokedexBrowser.tsx` (no two-type cap).
- **App:** theme, `widgets/ui.dart` (FilterPill, panels, rows, sliders, send button),
  type chip, filters, Ask, catch rate, type calculator, damage calculator, team report,
  detail forms.
- **Tests:** updated for the above.
