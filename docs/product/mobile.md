# Mobile app (`mobile/`)

The Pokédex on your phone (iOS and Android), read from your own pokérag server on the
home network. It covers the Pokédex (and your favourites), Teams with their coach, Ask,
and the home page's tools, the damage calculator included; the calculator's coach stays
on the website for now. Tabs at the bottom switch between Pokédex, Teams, Ask and Tools; each
keeps its place.

## List

All species, loading more as you scroll.

- **Search** by name or dex number.
- **Filter** by up to two types (all must match) and by generation (any may match).
- **Sort** by dex number, name, base stat total or any stat, either way round. Each
  row leads with the number you sorted by (BST otherwise).

Rows show the dex number, name, type chips and artwork. No matches says so and offers
to clear the search and filters.

## Detail

| Section | Shows |
|---|---|
| Header | artwork, dex number, name, category, types; a form switcher (Base / Mega / regional…) when the species has forms |
| Base stats | the six stats as bars that draw in, plus the total |
| Abilities | regular and hidden abilities with effects |
| Type matchups | takes more from (×4, ×2), resists (×½, ×¼), immune to (×0), and **Hits ×2** |
| Evolution | each step with the server's chips (e.g. "Friendship" + "Day"); tap **?** for the full requirement |
| Spin guide | for Milcery and Alcremie: the steps, the topping per Sweet and the spin per cream |
| Facts & training | height, weight, habitat, capture rate, base experience, colour; gender ratio, egg groups, egg cycles (~steps), growth rate, EV yield, base friendship |
| Moveset | per game (newest by default): Level-up ("Evo" = learned on evolving), Egg, TM / HM with the TM number, Tutor, Other; filter by category and type. Tap a move for its details and who else learns it in that game |
| Dex entries | every game's entry, grouped by generation |
| Where to find | per game: location, method, levels, rate and conditions, raid dens included (data ends at Sword / Shield) |

The app bar has **♡ favourite** (the same server profile the website and Ask's "for you"
picks use) and **previous / next** through the dex. The list's ♡ button opens
**Favourites**.

Everything shown is computed by the server, so it always matches the website. The
only things the app works out itself are type multipliers (Hits ×2 here, and the Tools
type calculator), looked up in the server's type chart (fetched once per launch).

## Teams

The same saved teams as the website's `/teams`, rated by the server:

- **Team list:** each card shows grade and score, play style, the AI summary,
  weak to / resists / hits hard, the six letter grades and the top three fixes. **+**
  makes a new team; **⋯ → Delete** removes one (after you confirm; it's gone from the
  website too).
- **Team page:**
  - six slots (types, role, BST); ✎ renames the team;
  - an empty slot opens a Pokémon search (forms included);
  - a filled slot opens the **set editor**, which offers only legal choices:
    ability, held item, nature, EVs (≤ 252 each, ≤ 510 total), IVs and up to 4
    moves from its learnset. **Save** or **Remove**;
  - **Compare with…** another team shows the verdict, the scorecard, their threats,
    our pressure and advice;
  - the report: rating and AI summary (↻ Regenerate), the six grades with fixes, How it
    plays (strategy axes, now and with learnable moves), type profile, Sets with **Use
    suggested** (fills only the empty parts), and Defence per attacking type.
- **Coach** (on the team page, as on the website):
  - quick questions, a question box, and the thread for this visit; with an opponent
    picked, questions include it;
  - answers stream with citations and the How line;
  - set changes come as a was → now card that saves only on **Apply**, then
    **Revert**s exactly;
  - drafted candidates offer **Add** (first empty slot) or **Replace…** a member, each
    with **Revert**;
  - "add Garchomp" adds it straight away with **Undo**;
  - duels show the outcome and the turn log.
  - Any change refreshes the slots and report. Nothing else is saved.

## Ask

The same assistant as the website's Ask, streamed from the server:

- **Starters** (the website's suggestions) until you ask; a line says whether answers
  are narrated by the LLM or keyless.
- The answer streams in with tappable **[n]** citations. Tapping one shows that
  record's text and, for a Pokémon, **Open** its page. If the plan couldn't apply part
  of the question, that is said first.
- **How it was answered:** planner (or cached), time, LLM calls and lookups; tap it for
  each step and what it found.
- **Cards** for each result: rankings, Pokémon lists, type matchups, moves, learnsets,
  who learns a move, and learn checks (✓ / ✗ with how). Each lists its sources; tap a
  Pokémon to open it.
- **Ask next:** follow-ups about the Pokémon the answer cited (none when it abstains).
- The **profile** button sets your preferred types (shared with the website) for
  "for you" questions and lists your favourites.

Questions the server answers in code (rankings, learn checks, type charts, move info)
spend no LLM calls, as on the website.

## Tools

The website home page's tool tiles, one page each:

- **Damage calc:**
  - singles or doubles, Lv50 or Lv100;
  - your side and the opponent's, each with a Pokémon, move (and in doubles its
    target), ability, item, nature, preset (Offensive / Bulky / Custom), EVs, IVs and
    current HP;
  - the field (weather, terrain, screens, crit, burn, Friend Guard).
  - **This turn** is the battle log in move order, played by the server
    (`POST /api/calc/turn`, the same turn the website shows): ranges, HP bars, KO
    calls, Focus Sash, who faints.
  - **Math** shows the focused hit term by term.

- **Type calculator:** pick 1–2 types (a third replaces the older). It shows what the
  typing takes ×4/×2, resists ×½/×¼, is immune to, and hits ×2, all read from the
  served type chart.
- **Nature helper:** the 5×5 grid (+stat rows, −stat columns, neutral natures on the
  diagonal); tap one for its ±10%.
- **Catch rate:**
  - pick a Pokémon, set its status and HP, and the server ranks every ball with its
    chance per throw and throws for 90%;
  - **Situation** holds wild and your level, turn, species caught, night/cave,
    fishing, caught before, love match and the Catching Charm;
  - the formula for the picked ball is at the bottom.
- **Lookup:** one search over moves, abilities and items.
  - A move shows its details and who learns it.
  - An ability shows its effect and the Pokémon that have it (filterable).
  - An item shows its effect, category, cost and Fling power.

## Server

The **server** button (top right) sets where the app reads from. An address is saved
only after the server answers there. When the server can't be reached, the app says
so, shows the address, and offers **Retry** and **Change address** rather than an empty
list.

Code: `mobile/lib/` ([mobile manifest](../components/mobile.yaml)). How to run it on the
Simulator, the emulator or a phone: [guides/mobile.md](../guides/mobile.md).
