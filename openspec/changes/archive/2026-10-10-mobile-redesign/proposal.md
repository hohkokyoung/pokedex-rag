# Proposal

## Why

The app works, but it looks like a first pass: plain Material rows, a default tab bar,
and long single-scroll pages. The owner wants it to look like the website (the light
Instrument language, home's components as the source of truth), only cleaner, with
modern mobile UI. They approved a mockup (`/impeccable`) built from the website's own
parts.

## What Changes

- **Shell:**
  - the website's tinted gradient ground behind every screen;
  - the bottom bar becomes the website's Tray: a grey tray where the current tab
    (Pokédex, Teams, Tools) sits raised in white, plus Ask as a separate red button.
- **Shared parts:** a hairline `Panel` (no nested panels), a `Segmented` control
  (inset track, ink active), a large page title (Chakra Petch), and type chips with
  spacing next to text.
- **Pokédex:** the website's two-column catalog cards (dex number, the sorted number
  top-right, artwork on a soft type glow, name, genus, chips). Filters are one row of
  controls and a type strip.
- **Detail:**
  - the website hero (type glow, ghosted dex number, artwork, name, genus, chips,
    heart);
  - the long page splits into **Overview** (stats, abilities, matchups, facts),
    **Moves**, **Evolution** and **Where** (dex entries and encounters).
- **Team:**
  - grade, name and score first, then the six slots as a 3×2 grid;
  - the page splits into **Report**, **Coach** and **Compare**, with grades worst
    first and the fix inline.
- **Ask:** one search panel, the answer first, and ranked rows / cards as panels.
- **Damage calc:** roster cards with HP-left bars, the battle log panel, and the
  focused set as a key/value panel.
- **Motion:**
  - the artwork carries over from list to detail (a hero transition);
  - stat bars fill in the Pokémon's type colour;
  - segments switch in 200 ms;
  - every animation is instant under reduced motion.

## Capabilities

### New Capabilities
- `mobile/design-language`: the app's shared visual language and screen structure.

### Modified Capabilities
(none. What each screen shows and does is unchanged; this changes how it's laid out)

## Out of scope

- New features or data.
- The website itself.
- A dark theme.

## Impact

- App only: `lib/theme/`, `lib/widgets/` (new shared parts), `lib/app.dart` (shell),
  and each feature screen's layout.
- Widget tests that find widgets by text or key keep their keys; tests that depend on
  the old long-scroll layout open the right segment first.
- Docs: `docs/product/mobile.md` (layout notes), `docs/components/mobile.yaml`.
