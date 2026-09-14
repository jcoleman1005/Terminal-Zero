# TERMINAL ZERO — Shared UI Contracts

This file is the coordination contract for parallel UI agents.

Agents may read this file but should not independently redesign it.

If a contract is insufficient, document the requested change and return it to the integration owner.

## 1. Ownership rule

The following files are integration-owner only unless explicitly assigned:

- `scenes/ui/main_ui.tscn`
- `scripts/ui/main_ui.gd`
- `project.godot`
- shared Theme resources
- shared contract/type files

Parallel agents must build components that can be instantiated independently.

## 2. Suggested project layout

```text
docs/ui/
scenes/ui/terminal/
scenes/ui/companion/
scenes/ui/status/
scenes/ui/effects/
scripts/ui/contracts/
scripts/ui/terminal/
scripts/ui/companion/
scripts/ui/status/
scripts/ui/effects/
tests/ui/terminal/
tests/ui/companion/
tests/ui/status/
tests/ui/effects/
```

## 3. Shared semantic types

### TerminalChunk

Fields:
- `text: String`
- `style_role: StringName`

Allowed initial roles:
- `DEFAULT`
- `SUCCESS`
- `INFO`
- `WARNING`
- `ERROR`
- `DIRECTORY`
- `EXECUTABLE`
- `SPECIAL`
- `DIM`

### ShellCapabilities

Initial fields:
- `command_history: bool`
- `tab_completion: bool`
- `interrupt: bool`
- `companion_workspace: bool`

### SubsystemStatus

Fields:
- `id: StringName`
- `label: String`
- `short_label: String`
- `raw_value: String`
- `interpreted_state: String`
- `severity: StringName`
- `data_available: bool`
- `activity_state: StringName`

Initial subsystem ids:
- `BUFFER`
- `SHELL`
- `LOGS`
- `CPU`
- `NETWORK`
- `GATEWAY`

Initial severity values:
- `NORMAL`
- `INFO`
- `WARNING`
- `ERROR`
- `UNKNOWN`

### CompanionDocument

Fields:
- `document_id: String`
- `title: String`
- `content: String`
- `source_path: String`
- `document_type: StringName`

## 4. Terminal backend adapter contract

The UI should depend on an adapter rather than on simulation internals.

Conceptual methods:

```text
execute_command(command: String)
request_completion(partial_input: String, cursor_index: int)
request_interrupt()
get_prompt()
```

Conceptual signals:

```text
output_emitted(chunks)
command_finished()
prompt_changed(prompt)
shell_capabilities_changed(capabilities)
completion_result_received(result)
document_requested(document)
telemetry_changed(status)
```

The exact implementation language may evolve, but these responsibilities should remain separated.

## 5. Terminal contract

TerminalView owns:
- prompt rendering
- command editing
- rendered scrollback
- visual cursor/focus
- shell-history presentation
- completion presentation
- `NEW OUTPUT` indicator

TerminalView does not:
- parse Linux commands
- inspect filesystem state directly
- compute telemetry
- own mission logic

## 6. Companion contract

CompanionWorkspace accepts `CompanionDocument` data.

Rules:
- maximum 3 open tabs
- opening already-open document activates it
- free slot opens document
- fourth document evicts oldest inactive tab
- active tab must never be evicted
- terminal remains home keyboard focus
- mouse can scroll/click tabs
- Alt shortcuts manage companion

CompanionWorkspace does not:
- read filesystem directly
- parse shell commands
- compute mission state

## 7. Status strip contract

StatusStrip accepts `SubsystemStatus` updates.

All six subsystem positions remain visible.

The strip does not compute the underlying state.

It renders state only.

## 8. Effects contract

EffectsLayer receives presentation requests such as:

```text
play_local_status_change(subsystem_id)
play_subsystem_restoration(subsystem_id)
play_major_restoration(event_id)
set_damage_state(state)
```

EffectsLayer never changes gameplay state.

## 9. Focus contract

Terminal is home keyboard focus.

Any temporary GUI interaction should return focus to terminal unless the user is actively manipulating a non-terminal control with the mouse.

Companion scrolling via Alt shortcuts must not transfer text-entry focus.

## 10. Integration rule

If a component requires another subsystem, use:
- typed data
- signals
- documented callable methods

Do not reach into another agent's scene tree using brittle node paths.

## 11. Contract-change protocol

If an agent encounters a blocker:

1. Do not edit shared contracts.
2. Write a short `CONTRACT_CHANGE_REQUEST.md` in that agent's owned test/docs area.
3. Include:
   - current contract
   - problem
   - minimal proposed change
   - affected components
4. Continue all work that does not depend on the change.
