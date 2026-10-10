# Design

## Context

- The tokens (`tokens.g.dart` from DESIGN.md) already match the website: palette,
  6px chip radius, 10/14px radii, spacing, type scale.
- What's off is structure: Material defaults (NavigationBar, AppBar titles), long
  single-scroll pages, `Card`s holding `Section`s.

## Goals / Non-Goals

**Goals:** the approved mockup on every screen; no behaviour change; tests keep their
keys.

**Non-Goals:** new data, dark theme, website changes.

## Decisions

1. **Ground:** a `Ground` widget paints the website's vertical gradient
   (`#f4f2ef → #eae7f0 → #e6ecf2`). Scaffolds become transparent over it, via the
   shell and the top-level routes.
2. **Shell:**
   - `AppShell` drops `NavigationBar` for `TrayBar`: three tabs in an inset tray, the
     current one white with a 1px shadow, plus a red Ask button.
   - Keys stay `tab-pokedex`, `tab-teams`, `tab-ask` and `tab-tools`.
   - It's positioned over the content with safe-area padding; screens add bottom
     padding so the last item clears it.
3. **Shared widgets** (`lib/widgets/`):
   - `Panel`: white, 1px hairline, 14px corners. It replaces `Section`'s Card and
     keeps `Section(title:)` as a Panel with a headline.
   - `Segmented<T>`: an inset track with an ink active segment and an animated
     indicator (200 ms, easeOutExpo; instant under reduced motion).
   - `PageTitle`: Chakra Petch display.
   - `KeyValueRow`: a label column with a value row whose children are 8px apart.
4. **Pokédex:**
   - a `SliverGrid` (two columns, `childAspectRatio` tuned so 375pt fits) of
     `DexCard`;
   - the artwork sits in a `Hero(tag: 'art-$id')` that the detail hero matches;
   - the sort metric keeps its existing logic and label.
5. **Detail:**
   - a `CustomScrollView`: hero sliver, a pinned `Segmented` header, then the
     segment's existing cards (reused as they are, but without nesting);
   - segment state is local to the page.
6. **Team:** the same pattern. Header (grade badge, name, score, play style), then a
   3×2 slot grid, then pinned segments: Report (rating, grades worst first with
   fixes, sets, profile), Coach (the coach section), Compare (opponent picker and
   matchup).
7. **Ask and Tools:** restyled through `Panel`, `PageTitle` and the theme; no
   structural change beyond the search panel.
8. **Calc:** roster cards gain HP-left bars from the server turn's `hp` ranges; the
   focused set uses `KeyValueRow`s.

## LLM budget

None. UI only.

## Reused / removed

- Reused: every existing feature widget's content.
- Removed: Material `NavigationBar` styling and the long-scroll detail and team
  layouts.

## Docs affected

`docs/product/mobile.md`, `docs/components/mobile.yaml`.

## Risks / Trade-offs

- **Widget tests that scroll a long page** need to tap a segment first. They keep
  their keys, so the edit is mechanical.
- **The hero transition across shell branches:** the detail route is top-level, so
  `Hero` works across the push.
