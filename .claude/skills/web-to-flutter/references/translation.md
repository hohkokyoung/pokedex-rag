# Web → phone translation

Each row is a decision the user has already made or approved. Follow it; if a web
pattern isn't here, pick the closest row and tell the user what you chose.

## Layout

| On the website | In the app | Notes |
|---|---|---|
| Multi-column page | One column; long pages split into `Segmented` parts (e.g. Overview / Moves / Evolution / Where) | Segments keep their state (`Visibility(maintainState)`) |
| A white card (`.card`, `.d-panel`) | `Section` (title + white panel, 14 corners, hairline) | Never a panel inside a panel |
| Card grid (catalog) | Two-column cards (`DexCard`) | Paging from the grid's last items |
| Sticky header / filter bar | Header in a `Column` above an `Expanded` list; the list cuts off cleanly under it | No fade or shadow at the cut (rejected) |
| Collapsible section, "advanced" | `FoldPanel` (its own panel) or `FoldRow` (inside a panel) with a muted summary | |
| Long list (20 balls, 18 defence rows) | The first few that matter, then "Show all N" / "Show the other N" | |
| Hover tooltip / title text | A visible note line, or a tap that opens a sheet | Phones don't hover |
| Modal / popover | `showModalBottomSheet` via `showChoices`, `showPanelSheet`, `showLookupSheet` | Use `useRootNavigator: true` so it covers the tab bar |

## Controls

| On the website | In the app |
|---|---|
| `<select>` / dropdown | `PickerRow` inside a panel (label left, value right) or `PickerButton` standalone; both open `showChoices`, which adds a search box past 12 options |
| A row of filter buttons / chips | `FilterPill`s in a `Wrap`, each opening its own sheet; a set pill turns ink and names its choice |
| Type toggles (`.lc-tg`, `.pk-types`) | `TypeGrid` / `TypeToggle`: grey names; a picked type is its colour with a soft glow |
| Segmented / tab buttons | `Segmented<T>` (ink pill slides) |
| Checkbox / toggle | `SwitchRow` (Cupertino switch) |
| Range input | `LabeledSlider` (label and value above a full-width track) |
| Radio group | `Segmented` when ≤ 5 short options, else `showChoices` |
| Icon button | `SquareButton` |
| Primary button | `FilledButton` (red); secondary `OutlinedButton`; text link `TextButton`. The theme gives them the 10-corner shape |
| Search box | `TextField` with a search prefix icon; the theme supplies the 15pt text and the focus hairline |
| Question box + "Send" | `TextField` with `SendButton` as `suffixIcon` |
| Suggested questions (chips) | `SuggestionRows`: one panel, a row each, an arrow |
| Confirm dialog | `showCupertinoDialog` + `CupertinoAlertDialog`; destructive action `isDestructiveAction` |
| Toast | `SnackBar` (floating, ink; themed) |
| Loading skeleton / spinner | `Spinner` (Cupertino); a section loading in place may use a thin `LinearProgressIndicator` |

## Content

| On the website | In the app |
|---|---|
| Ask / coach answer (markdown, `[n]`) | `AnswerText`: the first sentence is the verdict in the display face, bullets become rows with artwork when a source names the Pokémon, and `[n]` becomes small red chips. Pass `sources` |
| Coach conversation | `QuestionBubble` (the question), then `AnswerText`, then its cards |
| Type matchups (`TypeMatchups`) | `MatchupGroups(groups: matchGroups(...))`: the label above, a coloured multiplier, chips |
| Type badge | `TypeChip` (pass `count:` for "×2" inside the chip) |
| Grade letter | `GradeBadge` |
| Key/value facts | `KeyValueRow` + `note()` for the muted "· …" part |
| Stat numbers | `AppText.readout` (JetBrains Mono) |
| Page title | `pageBar(title)` (`root: true` on a tab's first page) |
| Pokémon artwork | `Artwork(thumbUrl(base, path), size: …)` |
| Can't reach the server | `CantReach` (scrolls when short) |

## UX changes that are always right on a phone

- Hover-revealed detail → shown inline or behind a tap.
- Tables wider than the screen → a row per item: the name, then a line of the key
  values, the rest in a sheet.
- Many small toggles → one sheet per group.
- Inline editors (sliders for six stats) → keep them, but full width with the value on
  the right; the rarely used ones (IVs) fold away.
- Hit targets: ≥ 44pt. A whole row is the target, not just its text.
