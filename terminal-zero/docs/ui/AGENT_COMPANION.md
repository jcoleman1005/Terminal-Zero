# Agent Brief — Companion Workspace

## Mission

Build the side-by-side document reader for TERMINAL ZERO.

The terminal must remain the player's home keyboard focus.

## Read first

- `docs/ui/TERMINAL_ZERO_UI_SPEC.md`
- `docs/ui/CONTRACTS.md`

## Owned directories

```text
scenes/ui/companion/
scripts/ui/companion/
tests/ui/companion/
```

Do not modify:
- `scenes/ui/main_ui.tscn`
- `scripts/ui/main_ui.gd`
- `project.godot`
- shared Theme resources
- shared contract/type files
- terminal/status/effects directories

## First milestone

Create a standalone test scene that accepts fake `CompanionDocument` data.

Required behavior:
1. Open one document.
2. Render it using monospace terminal styling.
3. Mouse wheel scrolls the document.
4. Alt+Up/Down scrolls.
5. Alt+PgUp/PgDn pages.
6. Alt+Home/End move to bounds.
7. Up to three tabs can remain open.
8. Alt+1/2/3 switches tabs.
9. Alt+W closes the active tab.

## Tab eviction rules

When a fourth document opens:
- active tab survives
- oldest inactive tab is evicted
- opening an already-open document activates it rather than duplicating it

## Visual rules

- same character-grid language as terminal
- same monospace base size
- Unicode/ASCII borders
- no rounded cards
- no modern document-reader chrome
- header may contain tabs integrated into border

## Responsive behavior

Provide two component modes:
- side pane
- overlay

The integration owner will decide the final switch threshold.

## Acceptance tests

### B1 — Open
Open `guide.txt`.
Expected:
- one tab
- readable document
- independent scroll position

### B2 — Three tabs
Open A, B, C.
Expected:
- three tabs present

### B3 — Eviction
Activate C.
Ensure A is oldest inactive.
Open D.
Expected:
- C remains
- A is evicted
- B and D remain

### B4 — Existing document
Open B again.
Expected:
- no duplicate
- B becomes active

### B5 — Keyboard controls
Expected:
- Alt shortcuts operate companion
- normal unmodified typing is not captured by the companion

## Stop condition

Do not implement filesystem access or parse `less` commands.

The integration/backend layer decides when a document should open.
