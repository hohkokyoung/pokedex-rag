# Mobile app (`mobile/`)

The Pokédex on your phone (iOS and Android), read from your own pokérag server on the
home network. It covers the Pokédex (and your favourites); Ask, Teams and the
calculators stay on the website for now.

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
only thing the app works out itself is the Hits ×2 list, looked up in the server's
type chart (fetched once per launch).

## Server

The **server** button (top right) sets where the app reads from. An address is saved
only after the server answers there. When the server can't be reached, the app says
so, shows the address, and offers **Retry** and **Change address** rather than an empty
list.

Code: `mobile/lib/` ([mobile manifest](../components/mobile.yaml)). How to run it on the
Simulator, the emulator or a phone: [guides/mobile.md](../guides/mobile.md).
