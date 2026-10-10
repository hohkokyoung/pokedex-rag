## Why

On the phone the app felt like stock Android. Pages cut in with a flash and couldn't be
swiped back, because go_router fell back to pages with no transition. Every tap drew a
Material ripple, and pickers, spinners, checkboxes and alerts were Material's. The tab
tray was boxy, and Lookup opened on an empty search with the full list one screen
deeper.

## What Changes

- Every page slides in the iOS way, with swipe-back, on a background of its own.
- No ink ripples: pressed things dim. Spinners, choice sheets (checkmark rows instead of
  dropdown menus and checkboxes), alerts, sliders and focused fields follow iOS.
- **BREAKING (UI):** the tab bar becomes one white capsule of four equal tabs. Ask is
  the red tab, and a soft capsule slides to the current tab. It replaces the tray and
  the separate Ask button.
- Lookup opens on every move, ability and item with the filters (the former Advanced
  search). With a search, each tab counts its matches.

## Capabilities

### New Capabilities

### Modified Capabilities
- `mobile/design-language`: the tab bar, and iOS behaviour on every screen.
- `mobile/tools`: Lookup lists everything, with filters.
- `mobile/finder`: the finder is Lookup itself, not a page behind it.

## Impact

App only: `mobile/lib/app.dart` (explicit pages), `theme/theme.dart`, `widgets/ui.dart`
(NavBar, Pressable, Spinner, choice sheets, PickerButton), the finder and Lookup files,
dialogs and dropdowns across screens, and tests. No backend or API change.
