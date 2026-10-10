## REMOVED Requirements

### Requirement: Tray navigation with a separate Ask
**Reason**: Replaced by a cleaner tab bar with Ask as one of its tabs.
**Migration**: See "Tab bar".

## ADDED Requirements

### Requirement: Tab bar
The bottom bar SHALL be one white capsule with four equal tabs: Pokédex, Teams, Tools and Ask. The current tab SHALL sit on a soft capsule that slides between tabs, and Ask SHALL be the red tab. A whole tab cell SHALL be its tap target, a pressed tab SHALL dim, and switching SHALL give a selection haptic. Each tab SHALL keep its place when switching.

#### Scenario: Switch tabs
- **WHEN** the owner taps near the edge of Teams, then Tools, Ask and Pokédex
- **THEN** each opens, and the Pokédex is where they left it

### Requirement: iOS behaviour
Pages SHALL slide in the iOS way and can be swiped back, each on its own background, so the page underneath never shows through. Taps SHALL NOT draw ink ripples. Choices SHALL open a sheet of rows with a red check rather than a dropdown menu or checkboxes. Loading SHALL use the iOS activity indicator, and confirmations SHALL use iOS alerts.

#### Scenario: Open a tool
- **WHEN** the owner opens a tool from the Tools tab
- **THEN** it slides in over an opaque background instead of cutting in
