---
name: pokérag
description: A Pokédex and grounded assistant that reads like a precision field instrument.
colors:
  pokeball-red: "#d8310c"
  pokeball-red-text: "#c42b08"
  brand-mark-red: "#e3350d"
  ember-red: "#ff5a34"
  verdict-green: "#2fae6a"
  verdict-green-text: "#1f7a47"
  caution-amber: "#f0b429"
  caution-amber-text: "#94600a"
  you-blue: "#2f6bff"
  you-blue-text: "#2a5fe0"
  instrument-ink: "#14171d"
  ink-dim: "#3f4650"
  muted-slate: "#5f6773"
  faint-slate: "#666e7b"
  panel-white: "#ffffff"
  inset-gray: "#f4f5f8"
  ground: "#eef0f4"
  hairline: "rgba(20,23,29,.10)"
  hairline-soft: "rgba(20,23,29,.055)"
  type-normal: "#a8a878"
  type-fire: "#f0803c"
  type-water: "#5aa0e6"
  type-electric: "#f4cf46"
  type-grass: "#6fc25a"
  type-ice: "#8fd4d4"
  type-fighting: "#d13b52"
  type-poison: "#b25ec4"
  type-ground: "#e0c068"
  type-flying: "#8aa0e6"
  type-psychic: "#f0619a"
  type-bug: "#9fc02f"
  type-rock: "#b8a038"
  type-ghost: "#7a5aa0"
  type-dragon: "#7a5cf0"
  type-dark: "#5a5366"
  type-steel: "#a8b0c0"
  type-fairy: "#f0a6d0"
  type-normal-on: "#ffffff"
  type-fire-on: "#ffffff"
  type-water-on: "#ffffff"
  type-electric-on: "#ffffff"
  type-grass-on: "#ffffff"
  type-ice-on: "#ffffff"
  type-fighting-on: "#ffffff"
  type-poison-on: "#ffffff"
  type-ground-on: "#ffffff"
  type-flying-on: "#ffffff"
  type-psychic-on: "#ffffff"
  type-bug-on: "#ffffff"
  type-rock-on: "#ffffff"
  type-ghost-on: "#ffffff"
  type-dragon-on: "#ffffff"
  type-dark-on: "#ffffff"
  type-steel-on: "#ffffff"
  type-fairy-on: "#ffffff"
  type-normal-text: "#787749"
  type-fire-text: "#bc570c"
  type-water-text: "#3178bb"
  type-electric-text: "#8a7102"
  type-grass-text: "#338618"
  type-ice-text: "#397e7e"
  type-fighting-text: "#d13b52"
  type-poison-text: "#a552b7"
  type-ground-text: "#8f7105"
  type-flying-text: "#5e72b5"
  type-psychic-text: "#cb3e7a"
  type-bug-text: "#667d08"
  type-rock-text: "#887306"
  type-ghost-text: "#7a5aa0"
  type-dragon-text: "#795aee"
  type-dark-text: "#5a5366"
  type-steel-text: "#6d7584"
  type-fairy-text: "#a25f87"
typography:
  display:
    fontFamily: "Chakra Petch, ui-sans-serif, sans-serif"
    fontSize: "2.2rem"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  body-small:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1.4
  readout:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "11.5px"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.02em"
rounded:
  chip: "6px"
  inset: "8px"
  control: "10px"
  card: "14px"
  pill: "99px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "14px"
  lg: "18px"
  gutter: "16px"
  page-x: "clamp(20px, 4vw, 56px)"
components:
  button-primary:
    backgroundColor: "{colors.pokeball-red}"
    textColor: "{colors.panel-white}"
    rounded: "{rounded.control}"
    padding: "8px 14px"
  button-ghost:
    backgroundColor: "{colors.inset-gray}"
    textColor: "{colors.instrument-ink}"
    rounded: "{rounded.control}"
    padding: "8px 14px"
  input-search:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.instrument-ink}"
    rounded: "{rounded.control}"
    height: "48px"
    padding: "0 16px 0 42px"
  card:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.instrument-ink}"
    rounded: "{rounded.card}"
    padding: "14px"
  type-tag:
    backgroundColor: "{colors.type-fire}"
    textColor: "{colors.type-fire-on}"
    typography: "{typography.label}"
    rounded: "{rounded.chip}"
    padding: "4px 9px"
  type-chip:
    textColor: "{colors.muted-slate}"
    rounded: "{rounded.control}"
    padding: "7px 12px"
  type-chip-on:
    backgroundColor: "{colors.type-fire}"
    textColor: "{colors.type-fire-on}"
    rounded: "{rounded.control}"
    padding: "7px 12px"
  nav-tray-link:
    textColor: "{colors.muted-slate}"
    rounded: "{rounded.inset}"
    padding: "6px 12px"
  nav-tray-link-active:
    backgroundColor: "{colors.panel-white}"
    textColor: "{colors.instrument-ink}"
    rounded: "{rounded.inset}"
    padding: "6px 12px"
  nav-cta:
    backgroundColor: "{colors.pokeball-red}"
    textColor: "{colors.panel-white}"
    rounded: "{rounded.control}"
    padding: "8px 14px"
---

# Design System: pokérag

## 1. Overview

**Creative North Star: "The Field Instrument"**

pokérag is a precision device you carry into a game. Its surfaces are white instrument
panels set on a cool, faintly tinted ground; its numbers read out in mono like a gauge;
and it has exactly one live signal, Pokéball red, which marks the action you can take or
the thing currently selected. All the warmth comes from Pokémon itself: the eighteen type
colours, the artwork, and battle text written the way the games write it. The instrument
stays calibrated and quiet so that the data and the creatures can be loud.

Density is high and deliberate. Tiles hug their content, grids pack without dead space,
and every panel must earn its place by being useful. The system is light everywhere
(the "Instrument" theme on every route, with home's components as the source of truth).
It explicitly rejects the **generic SaaS dashboard** (gray card grids, hero-metric tiles,
icon + heading + text feature cards), the **dark neon "AI" look** (phosphor green,
scanlines, glow, terminal HUD, the app's own retired first theme), and anything
**childish or cartoony**.

Motion follows the instrument too: state changes are quick (150 to 250ms, ease-out-expo
`cubic-bezier(0.16, 1, 0.3, 1)`), and the expensive moments are saved for a few places
where motion carries information (stat bars filling, artwork arriving, charts drawing).
Entrance reveals use IntersectionObserver plus CSS on already-visible content; GSAP is
reserved for those high-impact moments. Every animation has a `prefers-reduced-motion`
fallback. Layouts reflow from a three-column bento at ≥1440px down to one column at
620px and must hold at 375px. On touch screens (`pointer: coarse`) controls grow to
36–40px; for every pointer, small controls get an invisible hit area (`::after`) and
inputs fill the bar they sit in, so no target is under 24px while mouse layouts keep
their density. Fluid type (`clamp`/`vw`) still obeys the 12px / 11px floor. Grids use `minmax(0, 1fr)` so a long
name or stat row can never widen the page.

**Key Characteristics:**
- One red signal; type colours carry all other chroma.
- White panels on a tinted ground, separated by hairlines, not shadows.
- Three typefaces with fixed jobs: Chakra Petch titles the page, Space Grotesk does the
  work, JetBrains Mono reads out numbers.
- Uniform 10px controls; pills only for type and status tags.
- Answer first, source line last, no filler between.

## 2. Colors: The Calibrated Palette

A cool, near-neutral instrument body with one red signal, a small verdict vocabulary,
and the eighteen type colours as the only decorative chroma.

### Primary
- **Pokéball Red** (pokeball-red): the single action and selection colour as a fill.
  Primary buttons, the nav's Ask CTA, focus borders on inputs (with a 3px 12% red
  halo), the current item in pickers. Also the opponent's colour in team comparisons.
  Tuned a shade below the brand mark so white labels on it pass AA (4.8:1).
- **Pokéball Red Text** (pokeball-red-text): red used for words: "go" links, minus
  stats, weaknesses, the opponent's name. Passes on white, inset gray and red tints.
- **Brand Mark Red** (brand-mark-red): the Dex Lens favicon and nav mark only.
- **Ember Red** (ember-red): the hover/second stop of the red signal only. Never on its
  own.

### Secondary
- **You Blue** (you-blue): your side in comparisons and duels. Blue is you, red is the
  opponent; never swap or reuse them for anything else on the same screen.

### Tertiary
- **Verdict Green** (verdict-green / verdict-green-text): good outcomes (resists,
  boosted stats, survives, grade up). Fill for bars and dots; text variant for words.
- **Caution Amber** (caution-amber / caution-amber-text): borderline outcomes (rolls
  that may KO, mid HP). Fill for bars; text variant for words.
- **The type colours**: each Pokémon type's identity and the system's "playful"
  register. One palette (`TYPE_HEX` in `lib/pokeTypes.ts`, mirrored by the CSS
  `--type-*` variables) in three roles:
  - **Fill** (type-X): tags, chips, dots, bars, accents.
  - **On** (type-X-on): the label on a fill: plain white for every type. This is
    the one accepted contrast exception (see PRODUCT.md): the bright fills are the
    brand's playful register, chosen over darker fills, tonal labels and shadows.
  - **Text** (type-X-text): the type used as words on a light panel.
  Components get these through `typeChip(t)` (fill + label) or `typeVars(t)`
  (sets `--tc`/`--c`, `--on`, `--tx` for CSS).

### Neutral
- **Instrument Ink** (instrument-ink): all primary text, the inverted fill of active
  segmented controls, dark badges.
- **Ink Dim** (ink-dim): secondary body text inside panels.
- **Muted Slate** (muted-slate): labels, captions, inactive nav links, "From …" source
  lines (5.7:1 on white).
- **Faint Slate** (faint-slate): tertiary text: "/ 100" suffixes, counts, inactive
  type chips. The lightest readable gray (4.5:1 even on the ground).
- **Panel White** (panel-white): every card, input, dropdown and modal surface.
- **Inset Gray** (inset-gray): recessed areas inside a panel (segmented-control tracks,
  hover rows, ghost buttons).
- **Ground** (ground): the page behind the panels, washed by a faint vertical gradient
  from `#f4f2ef` through `#eae7f0` to `#e6ecf2`.
- **Hairline / Hairline Soft** (hairline, hairline-soft): 1px panel borders and inner
  dividers. Ink at 10% and 5.5%, never a gray hex.

### Named Rules
**The One Home Rule.** Every colour token is defined once, in the shared
`html[data-home], html[data-lab]` block at the top of the light theme in
`app/globals.css`, and every route and portaled modal inherits it. New code uses
the canonical names (`--accent`, `--accent-text`, `--muted`, `--surface`,
`--surface-2`, `--line`, `--line-soft`, `--ok`/`--ok-text`, `--warn`/`--warn-text`,
`--blue`/`--blue-text`). `--red`, `--red2`, `--red-text`, `--dim`, `--panel` and
`--line2` are aliases kept for existing rules; never add new uses or re-declare
tokens inside a component.

**The One Signal Rule.** Pokéball red marks what you can do or what is selected, and
nothing else. If red appears on a decorative element, a heading, or an inactive state,
remove it.

**The Types Are the Colour Rule.** Any extra chroma on a screen must come from a
Pokémon type, a verdict, or you/opponent. Invented accent colours (violet gradients,
brand teals) are forbidden.

**The Name Always Shows Rule.** A type is never identified by colour alone; every type
chip and tag prints the type name.

**The Fill Is Not Text Rule.** A fill colour is never used for words. Every signal has
a fill and a text shade (red, green, amber, blue, each type); words always take the
text shade, and labels on a fill take its "on" shade.

## 3. Typography

**Display Font:** Chakra Petch (with ui-sans-serif)
**Body Font:** Space Grotesk (with ui-sans-serif, system-ui)
**Label/Mono Font:** JetBrains Mono (with ui-monospace)

**Character:** Chakra Petch's squared, chamfered letterforms echo the Dex device and
appear only where the instrument names itself: page titles and the wordmark. Space
Grotesk does every working job. JetBrains Mono is the readout: numbers, ranges,
percentages, stat values and the few compact data keys.

### Hierarchy
- **Display** (600, 2.2rem, 1.02): page titles only ("Pokédex", "Teams"). One per page.
  Balanced wrap.
- **Headline** (600, 18px, 1.2): detail-page panel headings, sentence case.
- **Tile title** (600, 15px): home tile headings (h2), one line, sentence case; the
  meta beside them is Label-sized muted text.
- **Title** (700, 16px, 1.2): Pokémon names on cards, row titles in lists.
- **Body** (400, 15px, 1.55): answers, descriptions, dex entries. Cap prose at 70ch.
- **Body Small** (400, 13px, 1.5): sub-lines under titles, source lines.
- **Label** (500–600, 12.5px): field names, group labels, counts ("1,025 specimens"),
  status pills, nav links. Sentence case; never spaced caps.
- **Action** (600, 13px): text links and small buttons ("Open team →", "Show all",
  tabs). Sentence case.
- **Readout** (700, 11.5px, mono): numeric values, damage ranges, multipliers (×2, ×¼),
  dex numbers. Tabular.
- **Code** (mono caps, ≥11px): data codes only: HP / SPA, BST, #0001, table heads,
  VS, nature +Atk / −Def. Never words.

### Named Rules
**The Three Jobs Rule.** Exactly three families, each with one job: Chakra Petch names
the page, Space Grotesk does the work, JetBrains Mono reads out numbers. A fourth family
is forbidden; mono is forbidden for sentences.

**The No Eyebrow Rule.** Spaced-caps mono kickers (the old red-dot eyebrow) appear at
most once per page region, and preferably never. Give a panel a real sentence-case
heading instead.

**The Legible Floor Rule.** Words are never below 12px. All-caps mono data codes may
go to 11px (caps read a size larger); nothing goes below that.

## 4. Elevation

Flat by default. Panels sit on the ground separated by a 1px hairline and the contrast
between panel white and the tinted ground; they carry no shadow at rest. Shadows exist
only for things that physically float above the page or need to signal state.

### Shadow Vocabulary
- **Float** (`box-shadow: 0 20px 40px -20px rgba(20,23,29,.35)`): dropdowns, pickers,
  autocomplete menus, popovers.
- **Panel lift** (`box-shadow: 0 14px 40px -26px rgba(20,23,29,.5)`): legacy `.panel`
  surfaces on lab pages only; do not extend to new cards.
- **Focus halo** (`box-shadow: 0 0 0 3px rgba(227,53,13,.12)`): inputs and pills on
  focus, paired with a red border.
- **Raised tab** (`box-shadow: 0 1px 2px` ink at 12%): the current link in the nav tray
  and the selected option in a segmented control.
- **Type glow** (`box-shadow: 0 3px 10px` type colour at 40%): an active type chip.

### Named Rules
**The Hairline Rule.** Depth at rest comes from hairlines and tone, never shadows. If a
card needs a shadow to separate from the page, the ground is wrong, not the card.

## 5. Components

### Buttons
Calibrated and quiet: one shape, one signal.
- **Shape:** soft rectangle (10px) for every button, input, toggle and select. No
  circle buttons.
- **Primary:** Pokéball red fill, white text, 8px 14px. Used for the one action that
  matters on a surface (Ask, Apply, Add).
- **Hover / Focus:** hover brightens slightly (`filter: brightness(1.06)`) or adds a red
  under-glow; focus shows the 2px focus-visible outline with a 2px offset.
- **Ghost:** inset gray fill, ink text; hover turns border and text red.
- **Text action ("go"):** red text link at the foot of a tile pointing to the full page.

### Chips
- **Type tag (static):** filled with the type colour, bold white label, 6px radius, 4px 9px. Capitalized type name always printed.
- **Type chip (filter):** "ghost to fill". Transparent with faint text at rest, inset
  gray on hover, fills with the type colour (white label) plus a soft type glow when on.
- **Segmented control:** an inset-gray track holding options; the selected option is
  raised in white with the raised-tab shadow, or inverted to ink for compact toggles.

### Cards / Containers
- **Corner Style:** 14px.
- **Background:** panel white on the ground.
- **Shadow Strategy:** none at rest (see The Hairline Rule).
- **Border:** 1px hairline.
- **Internal Padding:** 14px on bento tiles, 12px on Pokédex cards, 18px on roomy
  panels. Tiles hug content; a tile never stretches to fill a row with dead space.
- **Nesting:** forbidden. Sub-areas inside a card use inset gray or hairline dividers,
  never another bordered card.

### Inputs / Fields
- **Style:** white fill, 1.5px hairline stroke, 10px radius; search is 48px tall with a
  leading 18px icon.
- **Focus:** border turns Pokéball red with the 3px focus halo.
- **Pickers:** autocomplete menus float below with the Float shadow; rows show the
  sprite, name and type tags; the keyboard-highlighted row mirrors hover.

### Navigation
- **The Tray:** wordmark (Dex Lens mark + Chakra Petch "pokérag") on the left; on the
  right a faint ink-5% tray of sentence-case links (14px, 500), the current page raised
  in white, and a red "Ask" CTA outside the tray. At ≤560px links collapse to icons in
  the same tray. Simple on purpose; elaborate nav concepts are rejected.

### Server Notice
`components/ServerNote.tsx`: shown in place of data when a request fails. White
panel, hairline, a sentence-case title ("Can't reach the pokérag server"), one line
saying what didn't load and what to do, and a ghost "Try again" button (`compact`
drops the panel inside a home tile). Pages classify failures with `failureKind()` from
`lib/api.ts`: "offline" or "server" get this notice; only a real 404 gets a
not-found page. An outage must never render as "no results", "no teams" or "not found".

### Dialogs
Modals (Finder, move learners, ability holders, variants, the slot editor) are
`role="dialog"` + `aria-modal` with an accessible name, close on Escape and backdrop
click, and use `hooks/useDialogFocus.ts`: focus moves in, Tab stays inside, and focus
returns to the control that opened it. Every new modal uses the same hook.

### Answer Tiles (signature)
The Ask page and the home Ask tile answer verdict-first: one direct sentence, then at
most four bullets with "Show N more", each claim cited `[n]`, and a muted "From …" source
line under every tile. Visual evidence (matchups, learners as real Pokédex cards) sits
in its own tile beside the answer, levelled so no gap opens between them.

### Battle Log (signature)
Damage results read like the games' battle text ("The opposing X lost 38–45%…") in move
order, with ranges and KO chances in mono readout and HP bars where solid is the worst
roll and faded is the best.

## 6. Do's and Don'ts

### Do:
- **Do** extend home's components (type tags, ghost-to-fill type chips, picker rows,
  white cards) before inventing new ones; "same as home" means home's exact styling.
- **Do** keep red to the one action or selection per surface (The One Signal Rule).
- **Do** use blue for you and red for the opponent in every comparison.
- **Do** print the type name on every type chip and tag.
- **Do** put numbers, ranges and multipliers in JetBrains Mono readout; sentences in
  Space Grotesk.
- **Do** keep readable text at Faint Slate (`#666e7b`) or darker and at least 12px.
- **Do** keep transitions at 150 to 250ms with ease-out-expo, and give every animation a
  `prefers-reduced-motion` fallback.
- **Do** check every layout at desktop and at 375px.

### Don't:
- **Don't** build a **generic SaaS dashboard**: no gray card grids, no hero-metric tiles
  (big number, small label, gradient accent), no icon + heading + text feature cards.
- **Don't** bring back the **dark neon "AI" look**: no phosphor green, scanlines, glow,
  grid overlays or terminal HUD styling.
- **Don't** go **childish or cartoony**: no bubbly oversized radii, no mascots
  decorating panels.
- **Don't** use heatmaps, grids, damage charts or symbol chips (✕ ≈ ⚔) for team
  comparisons; write them in plain text with the existing card language.
- **Don't** add coloured top-border bars, coloured dots as decoration, or `border-left`
  / inset side stripes thicker than 1px as accents.
- **Don't** repeat spaced-caps eyebrow labels; one per region at most.
- **Don't** leave empty whitespace inside a tile or between uneven side-by-side tiles.
- **Don't** use gradient text, glassmorphism or a fourth typeface.
- **Don't** use circle buttons, bottom sheets for primary flows, or an elaborate nav.
- **Don't** put white text on a light type fill, or use a fill colour (red, green,
  amber, a type) for words; use its text or "on" shade.
- **Don't** introduce a text gray lighter than Faint Slate (`#666e7b`).
