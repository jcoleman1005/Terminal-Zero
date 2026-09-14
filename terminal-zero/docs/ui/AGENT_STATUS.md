# Agent Brief — Status Strip

## Mission

Build the persistent six-system OSIRIS status strip.

It renders telemetry; it does not compute telemetry.

## Read first

- `docs/ui/TERMINAL_ZERO_UI_SPEC.md`
- `docs/ui/CONTRACTS.md`

## Owned directories

```text
scenes/ui/status/
scripts/ui/status/
tests/ui/status/
```

Do not modify:
- `scenes/ui/main_ui.tscn`
- `scripts/ui/main_ui.gd`
- `project.godot`
- shared Theme resources
- shared contract/type files
- terminal/companion/effects directories

## Required subsystem order

1. Buffer
2. Shell Profile
3. Logs
4. CPU / Miner
5. Network Link
6. Cluster Gateway

All six positions must remain visible.

## First milestone

Create a standalone status-strip test scene with fake data.

Each slot must support:
- label
- short label
- raw value
- interpreted state
- severity
- data unavailable
- activity state

Examples:

```text
BUF 12K [LOW]
SHELL [MIN]
LOG [WARN]
CPU 91% [HIGH]
NET [DOWN]
GATE [NO DATA]
```

## Semantic color rules

- NORMAL → green where appropriate
- INFO → cyan
- WARNING → yellow
- ERROR → red
- UNKNOWN → dim/default

Never rely on color alone.

## Responsive behavior

At narrower widths:
- switch to predefined short labels
- reduce optional raw detail before hiding subsystem identity
- preserve all six slots

Do not shrink font dynamically to unreadable sizes.

## Acceptance tests

### C1 — Six slots
Expected:
- six subsystem slots always present

### C2 — No data
Feed CPU with `data_available = false`.
Expected:
- CPU identity remains
- rendered state indicates no data

### C3 — Severity
Feed warning/error/normal states.
Expected:
- semantic colors and text state both update

### C4 — Narrow width
Resize test scene narrower.
Expected:
- all six identities remain visible
- compact labels activate
- no overlap

## Stop condition

Do not implement game-state calculations or visual restoration effects beyond a minimal state-change indication.
