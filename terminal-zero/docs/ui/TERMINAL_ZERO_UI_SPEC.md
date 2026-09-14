# TERMINAL ZERO — Godot UI Implementation Specification

## 1. Design directive

TERMINAL ZERO should feel like a damaged Unix workstation that happens to contain a game, not a conventional game HUD wrapped around a terminal.

The terminal is the primary interaction surface. Godot should enhance the workstation around the shell without turning the shell itself into a game widget.

Godot exists to provide:
- stable scrollback
- adaptive split-screen reference material
- subsystem telemetry
- visual system restoration
- CRT/workstation atmosphere
- animation and sound feedback
- responsive PC layouts
- progressive UI repair

## 2. Final UI concept

Normal play is overwhelmingly terminal-first.

Example:

```text
alice@osiris:~/logs$ grep -i "gateway" network.log
...

alice@osiris:~/logs$ █







───────────────────────────────────────────────────────────────────────────────
BUF [OK] │ SHELL [MIN] │ LOG [WARN] │ CPU [NO DATA] │ NET [DOWN] │ GATE [???]
```

There is no conventional quest HUD, minimap, or game-style command bar.

Large OSIRIS ASCII branding is reserved for boot, login, major restoration sequences, chapter transitions, and PHOENIX-level events. During ordinary play, only a small unobtrusive OSIRIS identifier remains.

## 3. Companion workspace

When the player uses `less` or another appropriate pager/manual command after the companion capability has been repaired, the screen becomes an adaptive split:

```text
                                    │ ┌─[LOG_GUIDE]─[MISSION]─────────────┐
terminal output                     │ │                                   │
                                    │ │ grep PATTERN FILE                 │
alice@osiris:~/logs$ █              │ │ -i   ignore case                  │
                                    │ │ -n   line numbers                 │
                                    │ └───────────────────────────────────┘
────────────────────────────────────┴──────────────────────────────────────────
BUF [OK] │ SHELL [MIN] │ LOG [WARN] │ CPU [NO DATA] │ NET [DOWN] │ GATE [???]
```

The terminal remains interactive while the reference remains visible.

Maximum companion tabs: 3.

When opening a fourth:
- never evict the active tab
- evict the oldest inactive tab

## 4. Authentic Linux behavior

Preserve authentic command semantics whenever possible.

- `cat file` prints to terminal output.
- `less file` opens the companion reader when the capability is available.
- `man command` may later use the same companion region.
- Tab completion behaves traditionally.
- No graphical completion popup.
- Mouse interactions must not replace learning Linux commands.

The mouse may:
- scroll terminal history
- select/copy text
- scroll companion documents
- drag companion scrollbars
- click companion tabs

The mouse may not:
- click paths to `cd`
- click commands to execute them
- click objectives to solve them
- bypass terminal interaction

## 5. Shell capability progression

OSIRIS begins functionally degraded but usable.

Examples of unlockable capabilities:
- command history
- tab completion
- Ctrl+C / interrupt
- companion workspace
- improved telemetry
- improved visual presentation

Shell capabilities should be explicit state, not scattered booleans in many scripts.

Tab completion should only include paths the player has previously visited/discovered. This limitation belongs in the completion provider/backend, not the UI.

## 6. Visual language

Use a strict monospace character-grid philosophy.

All primary OSIRIS UI should use:
- one monospace family
- one base character size
- aligned box drawing
- ANSI-inspired semantic colors
- whitespace, brightness, weight, capitalization, and borders for hierarchy

Avoid:
- rounded cards
- modern glass panels
- large proportional headings
- conventional HUD frames
- decorative subsystem colors

Semantic colors:
- default: neutral phosphor/off-white
- green: success / healthy
- blue: directories
- red: error / fault
- yellow: warning / degraded / transition
- cyan: informational / network/system
- magenta: special OSIRIS/PHOENIX content
- dim: unavailable / inactive / secondary

Never rely on color alone. Text states such as `[OK]`, `[WARN]`, `[FAULT]`, `[NO DATA]` must carry the same meaning.

## 7. Status strip

Persistent at the bottom.

All six subsystem identities remain visible at all times:

1. Buffer
2. Shell Profile
3. Logs
4. CPU / Miner
5. Network Link
6. Cluster Gateway

Example:

```text
BUF 12K [LOW] │ SHELL [MIN] │ LOG [WARN] │ CPU 91% [HIGH] │ NET [DOWN] │ GATE [???]
```

Telemetry quality can improve as OSIRIS is repaired. The identity remains visible even when the value is not:

```text
CPU [NO DATA]
```

Routine UI state changes should not inject fake shell output.

## 8. Animation philosophy

Idle OSIRIS is quiet.
Active OSIRIS moves.
Damaged OSIRIS misbehaves.
Repairing OSIRIS performs.

Resting state should be mostly static aside from:
- cursor blink
- activity indicators with actual meaning
- very subtle CRT texture

Routine state changes:
- local pulse
- semantic color change
- restrained sound

Subsystem restoration:
- stronger localized animation
- phosphor bloom
- short ASCII diagnostic sequence
- satisfying audio

Major milestones:
- temporary full-screen ASCII / boot sequence
- stronger sound
- brief controlled distortion
- immediate return to readable workstation state

## 9. Damage presentation

Target balance:
- 80% structural degradation
- 20% corruption effects

Structural degradation examples:
- missing telemetry values
- disabled companion workspace
- limited colors
- incomplete borders
- fallback formatting
- incomplete branding

Corruption examples:
- malformed border glyph
- brief character substitution
- short flicker
- telemetry glitch
- transient scan distortion

Hard rule: damage may never hide information required to solve the game.

## 10. Audio

Subtle typing feedback is allowed by default.

Keep categories independently configurable:
- typing
- terminal feedback
- status events
- faults
- restoration
- major events
- ambient

Typing audio must be presentation-only.

## 11. Responsive behavior

PC-only design.

Primary target: 1920×1080.
Comfortable target: 1600×900.
Minimum useful laptop target: 1366×768.

Behavior:
- wide screen: terminal + companion side by side
- moderate width: companion narrows first
- narrow width: companion becomes overlay
- terminal should preserve roughly 80 usable columns whenever possible
- do not dynamically shrink fonts to force everything to fit

## 12. Focus model

The terminal is the home keyboard focus.

Opening or interacting with the companion workspace must not unexpectedly steal shell input.

Companion controls use Alt-modified shortcuts plus mouse controls.

Recommended:
- Alt+Up / Alt+Down: scroll
- Alt+PgUp / Alt+PgDn: page
- Alt+Home / Alt+End: document bounds
- Alt+1 / Alt+2 / Alt+3: switch tabs
- Alt+W: close active tab

## 13. Scrollback

Use modern terminal-style scrollback:
- large history buffer
- mouse wheel support
- user scrolling upward disables automatic snap-to-bottom
- incoming output does not yank the viewport
- subtle `NEW OUTPUT` indicator appears
- returning to bottom clears the indicator

## 14. High-level Godot scene architecture

Recommended:

```text
MainUI : Control
└── RootVBox : VBoxContainer
    ├── Workspace : Control
    │   ├── WorkspaceLayout : HSplitContainer
    │   │   ├── TerminalView
    │   │   └── CompanionWorkspace
    │   └── EffectsLayer
    └── StatusStrip
```

Detailed conceptual structure:

```text
MainUI
├── RootVBox
├── Workspace
│   ├── WorkspaceLayout
│   │   ├── TerminalView
│   │   │   ├── Scrollback
│   │   │   ├── NewOutputIndicator
│   │   │   └── InputRow
│   │   │       ├── PromptLabel
│   │   │       └── CommandLineEdit
│   │   └── CompanionWorkspace
│   │       ├── CompanionHeader
│   │       ├── DocumentViewport
│   │       └── CompanionFooter
│   └── EffectsLayer
│       ├── CRTOverlay
│       ├── DamageOverlay
│       └── MilestoneEffects
└── StatusStrip
    ├── OsirisMark
    ├── BufferStatus
    ├── ShellStatus
    ├── LogStatus
    ├── CpuStatus
    ├── NetworkStatus
    └── GatewayStatus
```

## 15. Architecture rules

Do not build a low-level PTY/VT100 emulator unless future requirements force it.

The current game already has a simulated Linux environment. Godot should become the presentation/input layer over that simulation.

Flow:

```text
player input
    ↓
TerminalView
    ↓
TerminalBackendAdapter
    ↓
simulated Linux environment
    ↓
structured output
    ↓
TerminalView
```

Do not parse commands in the UI.

Bad:
```text
if input.begins_with("cd"):
```

TerminalView should forward command strings to the backend.

## 16. Terminal data model

Keep logical output separate from rendered UI.

Suggested semantic records:

```text
TerminalChunk
- text
- style_role
```

Possible style roles:
- DEFAULT
- SUCCESS
- INFO
- WARNING
- ERROR
- DIRECTORY
- EXECUTABLE
- SPECIAL
- DIM

Avoid storing BBCode as canonical game state.

## 17. Input row

Implementation may internally use a `LineEdit`, but it must visually disappear into the terminal.

Concept:

```text
InputRow
├── PromptLabel
└── CommandLineEdit
```

Requirements:
- same font
- same size
- same baseline
- no GUI box
- no rounded border
- no conventional field padding

Executed commands should be committed into scrollback as prompt + submitted input.

## 18. Companion workspace data behavior

Companion is content-agnostic.

It should display:
- Morgan notes
- Maya notes
- LL_GUIDE
- LOG_FORENSICS_GUIDE
- mission files
- logs
- manuals
- future dossier content

It does not own filesystem contents.

## 19. State separation

Keep conceptually separate:

```text
SimulationState
    filesystem
    processes
    networking
    commands
    world state

ShellState
    cwd
    history
    capabilities
    completion index

TelemetryState
    six subsystem readings

InvestigationState
    objectives/discoveries

UIState
    scroll positions
    open tabs
    active tab
    pane visibility
    responsive layout mode

PresentationState
    damage level
    animation state
    accessibility/effects settings
```

Do not place everything into one giant `GameManager.gd`.

## 20. Autoload policy

Do not create a global manager for every UI subsystem.

Avoid:
- TerminalManager
- CompanionManager
- StatusManager
- EffectsManager
- UIManager

Prefer scene-owned nodes and signals.

One existing session/game-state autoload may be used if the project already has one.

## 21. Implementation sequence

### Milestone 0 — Foundation
Freeze shared contracts, directory ownership, data types, and signals.

### Milestone 1 — Functional terminal
Prompt, input, fake backend, output, basic scrollback.

### Milestone 2 — Shell ergonomics
History, completion, capability gates, interrupt hook, cursor, `NEW OUTPUT`.

### Milestone 3 — Status strip
Six permanent telemetry slots.

### Milestone 4 — Companion workspace
Three tabs, scrolling, Alt controls, side-pane layout.

### Milestone 5 — Responsive behavior
Terminal minimum width and overlay fallback.

### Milestone 6 — Unified theme
Font, palette, spacing, borders, small OSIRIS identifier.

### Milestone 7 — Damage states
DEGRADED / PARTIAL / RESTORED presentation modes.

### Milestone 8 — Juice
Boot sequence, repair effects, subtle CRT, sound.

## 22. Vertical-slice definition of done

Before additional polish:

1. Godot build launches into OSIRIS terminal.
2. Existing simulated Linux commands can be driven through the UI.
3. Scrollback is comfortable.
4. Six telemetry systems remain visible.
5. Shell capabilities can be enabled/disabled at runtime.
6. History behaves as an unlock.
7. Completion behaves traditionally.
8. Completion respects discovered paths.
9. `cat` prints normally.
10. `less` opens companion reader when available.
11. Terminal stays interactive while reader is visible.
12. Three documents remain open.
13. Fourth document evicts oldest inactive document.
14. Mouse manages UI but does not bypass Linux gameplay.
15. UI works at common PC resolutions.
16. Major state changes can animate without polluting shell output.
17. All effects can be disabled without breaking gameplay.
