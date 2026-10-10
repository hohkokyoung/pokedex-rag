# Audit checklist

Run it against the Simulator screenshots, with the website at phone width beside them.
Every item below came from a real complaint. Each "✗" is a fix to propose.

## Same as the website?

- [ ] The same jobs are possible (nothing the website does is missing). Missing pieces
      are listed, not silently dropped.
- [ ] The same data, from the same endpoint. No rule computed only in Dart that the
      website gets from the server (ADR-009).
- [ ] The same visual vocabulary:
  - type pickers look like `.lc-tg`;
  - matchups look like `TypeMatchups`;
  - answers look like `AskConsole` (verdict, artwork rows, citation chips).
- [ ] The same words for the same things (labels, empty states, error lines).

## Not stock Material

- [ ] No ripple, no Material spinner, no Material dropdown menu, no checkbox list, no
      `AlertDialog`, no `ExpansionTile`, no `ActionChip` / `ChoiceChip` as buttons.
- [ ] Pages slide in and swipe back. New routes go through `_go(...)`.
- [ ] Sheets and dialogs are white, with no Material tint.

## Consistent

- [ ] Corners only from `Radii`: no stadium (`StadiumBorder`, radius ≥ 17) or circle
      on a control.
- [ ] Text only from `AppText`; no stray `fontSize` above body except titles and the
      verdict.
- [ ] Red only on actions and the current selection; muted text is `mutedSlate` /
      `inkDim` with AA contrast.
- [ ] The same thing looks the same everywhere. Examples:
  - suggestion lists use `SuggestionRows` (Ask, team coach, calc coach);
  - question boxes use `SendButton`;
  - fact rows use `KeyValueRow`.
- [ ] Spacing from `Space`; related items close and groups apart. No big empty gaps
      between list items (a complaint), no chip touching its text (a complaint).

## Reads well on a phone

- [ ] Text isn't too big (the phone scale) and chips aren't cramped (8–10pt side padding).
- [ ] Shows less by default: long lists are capped with "Show all", detail is folded,
      and redundant numbers are dropped (e.g. "17/18" plus 17 chips → "misses: Normal").
- [ ] Nothing runs off the screen at 375pt; long names ellipsize; no horizontal strip
      that hides options off the edge.
- [ ] Many options (forms, moves, items) live in a sheet, with search when long, not as
      a wall of chips.
- [ ] Every tappable is ≥ 44pt tall, and the whole row is the target.
- [ ] Loading, empty, error and can't-reach states all exist and look intentional.
- [ ] Reduced motion: animations use `MediaQuery.disableAnimations`.

## Report format

```
| # | Where | What differs | Fix |
|---|-------|--------------|-----|
```

Lead with what the user will notice most. Then ask which to fix, unless they already
said "fix everything".
