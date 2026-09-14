# Agent Brief — Terminal Core

## Mission

Build the shell presentation layer for TERMINAL ZERO.

You own terminal rendering and interaction, not command execution or game logic.

## Read first

- `docs/ui/TERMINAL_ZERO_UI_SPEC.md`
- `docs/ui/CONTRACTS.md`

## Owned directories

```text
scenes/ui/terminal/
scripts/ui/terminal/
tests/ui/terminal/
```

Do not modify:
- `scenes/ui/main_ui.tscn`
- `scripts/ui/main_ui.gd`
- `project.godot`
- shared Theme resources
- shared contract/type files
- companion/status/effects directories

## First milestone

Create a standalone terminal test scene with a fake backend.

Required behavior:
1. Display an authentic shell-style prompt.
2. Capture command input.
3. Enter submits the command.
4. Submitted prompt + command become immutable scrollback.
5. Fake backend emits test output.
6. A fresh prompt appears.
7. Mouse wheel scrolls older output.
8. Terminal input remains visually indistinguishable from terminal text.

Do not implement CRT effects yet.

## Second milestone

Add:
- modern scrollback behavior
- `NEW OUTPUT` indicator
- command history capability gate
- shell completion presentation
- Ctrl+C / interrupt hook
- cursor/focus behavior

## Completion behavior

Traditional shell behavior:
- unique match completes
- ambiguous match completes common prefix
- subsequent Tab prints candidates into terminal output

Do not create a graphical completion popup.

The backend/completion provider decides which paths are eligible.

## Acceptance tests

### A1 — Submit
Type:
```text
pwd
```
Expected:
- `prompt + pwd` moves into scrollback
- fake backend output appears
- fresh prompt appears

### A2 — Scrollback
Generate enough fake lines to overflow.
Expected:
- mouse wheel moves through history
- user can continue typing after returning to bottom

### A3 — New output
Scroll upward.
Emit backend output.
Expected:
- viewport does not jump to bottom
- `NEW OUTPUT` appears

### A4 — History gate
History disabled:
- Up does not retrieve prior command

History enabled:
- Up retrieves prior command
- Down moves forward

### A5 — Completion
Completion enabled:
- unique candidate completes
- ambiguous candidates are printed in terminal style

## Stop condition

Do not redesign backend contracts or build unrelated UI.

If a contract is insufficient, write a contract-change request instead of changing shared files.
