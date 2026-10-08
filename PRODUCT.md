# Product

## Register

product

## Users

Two audiences, weighted equally:

- **The owner, as a player.** Uses pokérag while playing or planning: looking up a
  species or move, checking a matchup, building and grading a team of six, running a
  damage or catch-rate calc mid-session. Wants the answer fast and correct, often on a
  phone beside a console.
- **People it is shown to.** Recruiters and peers seeing it as a portfolio piece. They
  judge craft in the first minute: does it feel considered, does the motion feel
  premium, does the assistant visibly ground its answers.

Single-user and local. No accounts, no onboarding funnel.

## Product Purpose

A Pokédex plus an assistant that answers only from ingested PokéAPI data. Every page is
a tool: the home bento (teams, type calculator, Ask, damage calc, lookups, nature and
catch-rate helpers), the Pokédex catalog and detail pages, Teams (build, grade, compare,
coach) and Ask.

Success: a player gets a trustworthy answer in seconds, with the record it came from;
and anyone watching thinks "this is unusually well made".

## Brand Personality

**Precise, premium, playful.**

- *Precise*: numbers, ranges and citations lead. Closed-form results read like an
  instrument readout, and the UI says plainly when the data can't answer.
- *Premium*: restrained surfaces, legible type, a few signature motion moments that
  feel expensive (drawn charts, spring reveals, artwork), not decoration everywhere.
- *Playful*: the warmth comes from Pokémon itself: type colours, artwork, and battle
  text written the way the games write it ("The opposing X lost 38–45%…").

## Anti-references

- **Generic SaaS dashboard**: gray card grids, hero-metric tiles, icon + heading +
  text feature cards.
- **Dark neon "AI" look**: phosphor green, scanlines, glow, terminal HUD (the app's
  retired first theme).
- **Childish / cartoony**: bubbly kid-app styling, mascots everywhere.
- Already rejected in this project: elaborate nav concepts, heatmaps and grids for
  comparisons, symbol chips, coloured top-border bars, repeated spaced-caps eyebrow
  labels, and empty whitespace inside or between tiles.

## Design Principles

1. **Answer first.** Lead with the verdict or the number; evidence and detail follow.
   Nothing on screen exists only to fill space.
2. **Show the source.** Grounding is the product. Citations and "From …" lines are
   part of the design, not footnotes to hide.
3. **The games are the reference voice.** Borrow the games' language (battle text, type
   colours, artwork) for warmth instead of inventing decoration.
4. **One language everywhere.** Extend the home page's components and tokens before
   inventing new ones; new forms are welcome, new vocabularies aren't.
5. **Motion earns its moment.** A few high-impact animations done exceptionally well
   beat ambient motion on everything.

## Accessibility & Inclusion

WCAG 2.2 AA: 4.5:1 body text contrast (3:1 large text), full keyboard paths with
visible focus, `prefers-reduced-motion` fallbacks for every animation, and type
information never carried by colour alone (chips always show the type name). One deliberate
exception: type chips keep the bright game-style type colours with white labels,
which is below 4.5:1 on the light types. The owner chose
this look over darker fills; every other text meets AA. Layouts
must hold at 375px phone width.
