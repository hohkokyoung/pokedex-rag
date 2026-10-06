# Home (`/`)

A dashboard of tools ("Live Console" bento). The top nav links to Home, Pokédex,
Teams and Ask on every page. On wide screens the tiles sit in three columns; below
1440px they reflow onto a grid, and down to phone width.

## Search

"Search any of 1,025 species…" — type 2+ characters for up to 6 matches by name or dex
number (alternate forms included); pick one to open its detail page.

## Team builder & coach tile

Your saved teams, one at a time (arrows to switch; most complete first, empty drafts
hidden): grade and score, the AI summary, strategy axes, type facts, and the one thing
to fix first. Links to the team page, or "Start a team" if you have none.

## Type calculator

Pick 1–2 types to see what the type combination **takes more damage from** (×2, ×4),
**resists** (×½, ×¼), is **immune to** (×0), and which types it **hits** ×2.

## Ask tile

The same assistant as [`/ask`](ask.md), in compact form, with example questions
(rank, lore, multi-part, matchup, for you) and a link to the full page.

## Damage calculator

A singles/doubles calculator at level 50 or 100.

- **Roster:** your side and the opponent's (two each in doubles). Tap a slot to pick
  a Pokémon; each has an ability, item, nature, EVs/IVs, HP and a chosen move. A
  newly picked Pokémon on the offensive preset gets a spread matching its category.
- **Both sides pick moves.** In doubles each Pokémon aims single-target moves at an
  opposing slot.
- **This turn:** a battle-log readout in move order (priority, then speed, with speed
  ties called out) — damage ranges, % of HP, KO chances, HP left after the hit (solid
  = worst roll, faded = best), and "if it's still standing" follow-ups.
- **Field:** weather, terrain, Reflect / Light Screen, crit, burn, Friend Guard.
- **Math:** the full formula breakdown for the current hit.
- **Details panel:** the focused Pokémon's set, editable inline.
- **Coach:** "Ask the coach about <Pokémon>" — ask whether it OHKOs, how much bulk it
  needs to survive, or for a build ("a bulky set for doubles"), then follow up ("swap
  X for a priority move", "no Choice item"). Damage and survival answers come with
  cards you can **Apply** into the calculator and **Revert**; builds show an **Apply
  build** card. Nothing is saved outside the calculator. See
  [../architecture/damage-calc.md](../architecture/damage-calc.md).

## Move · ability · item lookup

One search over 3,000+ moves, abilities and items ("Earthquake", "Intimidate",
"Leftovers"). Opening an entry shows its details:

- **Move:** type, category, power, accuracy, PP, effect, and every Pokémon that learns
  it — per game, in a table you can filter. Moves nobody learns (Struggle, Z-Moves,
  Max Moves) explain why.
- **Ability:** its effect and the species that have it, with a filter.
- **Item:** its effect, plus Fling power where relevant.

"Advanced search" opens a finder over everything with filters and sorting.

## Nature helper

The 5×5 nature grid (+stat rows, −stat columns; neutral natures on the diagonal). Tap
one to see its ±10% effect.

## Catch rate

Pick a wild Pokémon and set the situation — wild level, your level, HP left, status
(sleep, freeze, paralysis, burn, poison), turn, species caught, caught before,
Catching Charm. It ranks the **best balls here** by catch chance per throw (Gen 5+
multipliers). "Math" shows the formula.

## Code

All tiles are composed in `frontend/app/page.tsx` (the damage calculator and its coach
live there too, with the formula in `lib/damageCalc.ts` — [damage-calc.md](../architecture/damage-calc.md)).
Other tiles: `Finder.tsx` (search), `AskTile.tsx`, `TypeMatchups.tsx` (`lib/typeChart.ts`),
`CatchRateTile.tsx` (`lib/catchRate.ts`).
