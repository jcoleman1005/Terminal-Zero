# TERMINAL ZERO — UI Foundation Contract
## Lead Agent Deliverable · Milestone 0 Complete

This document is the authoritative reference for all parallel UI agents.
Read **CONTRACTS.md** for ownership rules and signal/method contracts.

---

## Directory ownership

| Directory | Owner | Notes |
|-----------|-------|-------|
| `scenes/ui/terminal/` | Terminal Agent | TerminalView scene and subscenes |
| `scenes/ui/companion/` | Companion Agent | CompanionWorkspace scene |
| `scenes/ui/status/` | Status Agent | StatusStrip scene |
| `scenes/ui/effects/` | Effects Agent | EffectsLayer scene (post-Milestone 3) |
| `scripts/ui/terminal/` | Terminal Agent | GDScript for terminal component |
| `scripts/ui/companion/` | Companion Agent | GDScript for companion component |
| `scripts/ui/status/` | Status Agent | GDScript for status component |
| `scripts/ui/effects/` | Effects Agent | GDScript for effects component |
| `tests/ui/terminal/` | Terminal Agent | Standalone test scene |
| `tests/ui/companion/` | Companion Agent | Standalone test scene |
| `tests/ui/status/` | Status Agent | Standalone test scene |
| `tests/ui/effects/` | Effects Agent | Standalone test scene |
| `scenes/ui/main_ui.tscn` | **Integration owner only** | |
| `scripts/ui/main_ui.gd` | **Integration owner only** | |
| `project.godot` | **Integration owner only** | |
| `scripts/ui/contracts/` | **Integration owner only** | |
| `theme/` | **Integration owner only** | |

---

## Shared contract files (do not edit)

| File | Purpose |
|------|---------|
| `scripts/ui/contracts/terminal_chunk.gd` | `TerminalChunk` type — styled output unit |
| `scripts/ui/contracts/shell_capabilities.gd` | `ShellCapabilities` type — ergonomic unlock flags |
| `scripts/ui/contracts/subsystem_status.gd` | `SubsystemStatus` type — telemetry snapshot |
| `scripts/ui/contracts/companion_document.gd` | `CompanionDocument` type — reader content packet |
| `scripts/ui/contracts/terminal_backend_adapter.gd` | `TerminalBackendAdapter` — abstract adapter (signals + stubs) |
| `scripts/ui/contracts/stub_backend_adapter.gd` | `StubBackendAdapter` — test double for parallel agents |

---

## Required method API per agent

### Terminal Agent — `TerminalView` node must expose:

```gdscript
func append_output(chunks: Array) -> void      # Array[TerminalChunk]
func on_command_finished() -> void
func set_prompt(prompt: String) -> void
func apply_capabilities(caps: ShellCapabilities) -> void
func show_completion(candidates: Array) -> void # Array[String]
func grab_input_focus() -> void
```

`TerminalView` calls MainUI via:
```gdscript
get_parent().get_parent().get_parent().get_parent()  # ← DO NOT USE
```
Instead: emit a signal or use a typed reference injected by MainUI.

**Recommended pattern:** expose a signal `command_submitted(command: String)` and `completion_requested(partial: String, cursor: int)`, which MainUI connects to the adapter.

### Companion Agent — `CompanionWorkspace` node must expose:

```gdscript
func open_document(doc: CompanionDocument) -> void
func apply_capabilities(caps: ShellCapabilities) -> void
```

### Status Agent — `StatusStrip` node must expose:

```gdscript
func update_statuses(statuses: Array) -> void  # Array[SubsystemStatus]
```

### Effects Agent — `EffectsLayer` node must expose:

```gdscript
func play_local_status_change(subsystem_id: StringName) -> void
func play_subsystem_restoration(subsystem_id: StringName) -> void
func play_major_restoration(event_id: StringName) -> void
func set_damage_state(state: StringName) -> void  # DEGRADED | PARTIAL | RESTORED
```

---

## Input action names (defined in project.godot)

Companion navigation (Alt-modified, never steal terminal focus):

| Action name | Keys |
|-------------|------|
| `ui_companion_scroll_up` | Alt+Up |
| `ui_companion_scroll_down` | Alt+Down |
| `ui_companion_page_up` | Alt+PgUp |
| `ui_companion_page_down` | Alt+PgDn |
| `ui_companion_doc_start` | Alt+Home |
| `ui_companion_doc_end` | Alt+End |
| `ui_companion_tab_1` | Alt+1 |
| `ui_companion_tab_2` | Alt+2 |
| `ui_companion_tab_3` | Alt+3 |
| `ui_companion_close_tab` | Alt+W |

Terminal:

| Action name | Keys |
|-------------|------|
| `terminal_interrupt` | Ctrl+C |

> [!IMPORTANT]
> `terminal_interrupt` must only be acted on when `ShellCapabilities.interrupt == true`.
> Check the capability before consuming the input event.

---

## Standalone test scene convention

Each agent creates a runnable scene at:

```
tests/ui/<component>/test_<component>.tscn
```

The scene must:
- Run without `main_ui.tscn`
- Use `StubBackendAdapter` to drive the component
- Connect signals directly (not via MainUI)
- Demonstrate core functionality visually

---

## Architecture mismatch notes

The following mismatches between the design bundle and the existing project were identified during the foundation pass:

1. **No Godot project existed** — the Godot project (`terminal-zero/`) was a blank Godot 4.7 init with only `project.godot` and `icon.svg`. All structure was created fresh. ✅ Resolved.

2. **Python simulation is not a Godot module** — the existing simulation (`terminal_zero/` Python package) runs as a standalone Python process. The `TerminalBackendAdapter` is currently a stub. A concrete bridge (GDExtension, subprocess IPC, or GDScript reimplementation) is **out of scope for Milestone 0** and must be planned as a separate integration task.

3. **`GODOT_terminal_zero/` directory** — this is a directory containing a copy of the Python simulation module, not a Godot project. It appears to be a worktree artifact or IDE copy. No action taken; it is not part of the Godot project.

4. **`unlocked_ergonomics` dict → `ShellCapabilities`** — the Python state uses string-keyed booleans (`history`, `autocomplete`, `sigint`, `tab_completion`, etc.). The `ShellCapabilities` contract maps four of these. If finer granularity is needed (e.g. `history_arrows` separately from `command_history`), file a contract change request.

5. **`system_flags` / telemetry** — Python state tracks flags like `BUFFER_REPAIRED`, `CPU_NORMAL`, etc. These do not map 1:1 to `SubsystemStatus` fields. The concrete `TerminalBackendAdapter` implementation will need to translate these to `SubsystemStatus` objects. This is an integration-owner task.

6. **No theme resource yet** — `theme/` directory created and placeholder added. Shared `Theme` resource (font, palette, sizing) is deferred to Milestone 6. Agents should use hard-coded placeholder styles for now.
