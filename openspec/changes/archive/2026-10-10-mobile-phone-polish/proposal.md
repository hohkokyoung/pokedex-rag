## Why

On the phone, text read too big. Space Grotesk is wide, and the website's scale was
used unchanged. Type filters were coloured text on white outlines, unlike the solid
type chips everywhere else. The type strip ran off the edge of the screen. The Ask box
held a large red "Ask" block, and the dex entries were a long wall of text with game
names in spaced-out mono.

## What Changes

- A phone type scale: every step a little smaller (body 14, small 12.5, label 12),
  tighter body leading, page titles 28/22, text fields at 15.
- Type filters are solid type chips: the picked ones carry a check, and the rest fade
  while any is picked. Types are picked in a three-column grid.
- Filters are a row of pills that each open a focused sheet: Pokédex Type, Generation
  and Sort; Lookup Type, Category, Kind and Game. Nothing runs off the screen.
- Question boxes send with a small round red arrow.
- Dex entries show one generation at a time, picked from a segmented control. Each
  entry is plain text with its games in muted text.

## Capabilities

### New Capabilities

### Modified Capabilities
- `mobile/design-language`: the phone scale, type filters as type chips, and filters as pills.
- `mobile/pokedex-browsing`: dex entries one generation at a time.

## Impact

App only: theme, `widgets/ui.dart` (FilterPill, panel sheet, SendButton),
`filters_sheet.dart` (ListFilterBar, TypeToggle, TypeGrid), list, finder, profile, type
calculator, dex entries, can't-reach (scrolls when short), tests.
