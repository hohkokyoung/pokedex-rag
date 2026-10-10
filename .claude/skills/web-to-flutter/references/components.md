# The app's shared parts

Check this list before writing any widget. If something here is close but not quite
right, extend it in place (and keep every caller working) rather than forking a copy.
Verify names still exist (`grep -n "class Name" mobile/lib`) since this list can drift.

## `mobile/lib/widgets/ui.dart`

| Widget | Use |
|---|---|
| `Ground` | The tinted gradient behind every page (applied by the theme's page transitions) |
| `pageBar(title, {root, actions})` | Every screen's top bar |
| `PageTitle` | A Chakra Petch title outside an app bar |
| `NavBar` | The tab bar (`lib/app.dart` only) |
| `Pressable` | iOS-style press: dims and settles. Wrap any custom tappable |
| `Spinner` | Loading indicator |
| `SquareButton` | Square icon button (10 corners, hairline) |
| `FilterPill` | A filter that opens its sheet |
| `Segmented<T>` | Segmented control; `compact` for dense rows |
| `PickerRow<T>` | Settings row with a check sheet (inside a panel) |
| `PickerButton<T>` | Boxed one-of-many control (standalone) |
| `showChoices<T>(...)` | Check-row sheet; `many: true` for multi-select; search past 12 options; `keyOf` for test keys |
| `ChoiceRow` | One row of such a sheet |
| `showPanelSheet(context, title:, builder:)` | A sheet with free content (type grid, sort list) |
| `FoldPanel` | A panel whose header folds its body (title + muted summary) |
| `FoldRow` | A folding row inside a panel |
| `SwitchRow` | Label + Cupertino switch |
| `LabeledSlider` | Label/value line over a full-width slider |
| `KeyValueRow`, `note()` | Fact rows |
| `SendButton` | The red send square in question boxes |
| `SuggestionRows` | Suggested questions as rows in one panel |
| `QuestionBubble` | The user's question in a conversation |
| `BrandMark` | The pokérag mark (Pokédex header) |

## Elsewhere

| Widget | File | Use |
|---|---|---|
| `Section` | `features/pokedex/detail_sections.dart` | Titled white panel |
| `MatchupGroups`, `matchGroups()` | same | Type matchup groups |
| `TypeChip` | `widgets/type_chip.dart` | Type badge (`dense`, `count`) |
| `TypeToggle`, `TypeGrid` | `features/pokedex/filters_sheet.dart` | Type pickers (`max:` caps picks) |
| `Artwork`, `thumbUrl` | `widgets/artwork.dart`, `data/sprites.dart` | Pokémon images (tests override `artworkProvider`) |
| `GradeBadge`, `gradeTextColor` | `widgets/grade.dart` | Team grades |
| `CantReach` | `widgets/cant_reach.dart` | Server unreachable |
| `AnswerText` | `features/ask/answer_text.dart` | Any LLM or code-written answer |
| `HowAnswered`, `ViewCard`, `showSourceSheet` | `features/ask/ask_parts.dart`, `ask_cards.dart` | How an answer was made, Ask result cards, a citation's record |
| `showLookupSheet`, `openMove`, `AbilitySheet`, `ItemSheet` | `features/tools/lookup_sheets.dart` | Move / ability / item details |
| `pickPokemon` | `features/teams/pokemon_picker.dart` | Pick a Pokémon (forms included) |

## Theme and tokens

- `lib/theme/tokens.g.dart` is generated from `DESIGN.md` (`make mobile-tokens`).
  Never edit it by hand. It holds `Palette`, `Radii` (chip 6, inset 8, control 10,
  card 14), `Space`, `TypeColors.fill/on/text`, and the website `TypeScale`.
- `lib/theme/theme.dart` holds `AppText`, the **phone** type scale (body 14, small
  12.5, label 12, headline 16.5). Use it, not `TypeScale`. It also holds the theme:
  - no splash;
  - Cupertino transitions on every page via `_GroundedPages`;
  - Material buttons, chips, sheets, sliders, snack bars and inputs themed to the
    corner scale.
