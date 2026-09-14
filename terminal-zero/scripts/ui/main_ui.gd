## MainUI
## Root UI controller for Terminal Zero.
##
## Owned by: Lead / Foundation (integration owner only)
## Contract version: 1.0
##
## ── Responsibilities ─────────────────────────────────────────────────────────
##
##   - Hold a reference to the backend adapter.
##   - Wire adapter signals to child scenes (TerminalView, CompanionWorkspace,
##     StatusStrip, EffectsLayer) via typed connections.
##   - Manage responsive layout mode.
##   - Ensure terminal retains keyboard focus.
##
## ── What this script does NOT do ────────────────────────────────────────────
##
##   - Parse shell commands.
##   - Compute telemetry.
##   - Own document content.
##   - Own mission logic.
##
## ── Parallel agent note ──────────────────────────────────────────────────────
##
##   Parallel agents may NOT edit this file.
##   If a wiring change is needed, document it in a CONTRACT_CHANGE_REQUEST.md.
##
class_name MainUI
extends Control

# ── Scene references (assigned in main_ui.tscn) ───────────────────────────────

## The backend adapter node (concrete implementation added by integration owner).
@onready var backend: TerminalBackendAdapter = $BackendAdapter

## Terminal core — owns prompt, input, scrollback.
## Populated once TerminalView scene is built (Milestone 1).
@onready var terminal_view: Control = $RootVBox/Workspace/WorkspaceLayout/TerminalView

## Companion workspace — owns tab management, document display.
## Populated once CompanionWorkspace scene is built (Milestone 4).
@onready var companion_workspace: Control = $RootVBox/Workspace/WorkspaceLayout/CompanionWorkspace

## Status strip — owns the six telemetry slots.
## Populated once StatusStrip scene is built (Milestone 3).
@onready var status_strip: Control = $RootVBox/StatusStrip

## Effects layer — owns CRT, damage, milestone effects.
## Populated once EffectsLayer scene is built (Milestone 8).
@onready var effects_layer: Control = $RootVBox/Workspace/EffectsLayer


# ── Layout ────────────────────────────────────────────────────────────────────

## Minimum pixel width below which the companion becomes an overlay.
const COMPANION_OVERLAY_THRESHOLD_PX: int = 1200

## Minimum pixel width below which companion narrows instead of collapsing.
const COMPANION_NARROW_THRESHOLD_PX: int = 1500


func _ready() -> void:
	_connect_backend()
	_apply_initial_layout()


# ── Backend wiring ────────────────────────────────────────────────────────────

func _connect_backend() -> void:
	if not backend:
		push_error("MainUI: BackendAdapter node not found — check main_ui.tscn")
		return

	backend.output_emitted.connect(_on_output_emitted)
	backend.command_finished.connect(_on_command_finished)
	backend.prompt_changed.connect(_on_prompt_changed)
	backend.shell_capabilities_changed.connect(_on_shell_capabilities_changed)
	backend.completion_result_received.connect(_on_completion_result_received)
	backend.document_requested.connect(_on_document_requested)
	backend.telemetry_changed.connect(_on_telemetry_changed)


# ── Backend signal handlers ───────────────────────────────────────────────────

func _on_output_emitted(chunks: Array) -> void:
	if terminal_view and terminal_view.has_method("append_output"):
		terminal_view.append_output(chunks)


func _on_command_finished() -> void:
	if terminal_view and terminal_view.has_method("on_command_finished"):
		terminal_view.on_command_finished()


func _on_prompt_changed(prompt: String) -> void:
	if terminal_view and terminal_view.has_method("set_prompt"):
		terminal_view.set_prompt(prompt)


func _on_shell_capabilities_changed(capabilities: ShellCapabilities) -> void:
	if terminal_view and terminal_view.has_method("apply_capabilities"):
		terminal_view.apply_capabilities(capabilities)
	if companion_workspace and companion_workspace.has_method("apply_capabilities"):
		companion_workspace.apply_capabilities(capabilities)


func _on_completion_result_received(result: Array) -> void:
	if terminal_view and terminal_view.has_method("show_completion"):
		terminal_view.show_completion(result)


func _on_document_requested(document: CompanionDocument) -> void:
	if companion_workspace and companion_workspace.has_method("open_document"):
		companion_workspace.open_document(document)


func _on_telemetry_changed(statuses: Array) -> void:
	if status_strip and status_strip.has_method("update_statuses"):
		status_strip.update_statuses(statuses)


# ── Terminal command forwarding ───────────────────────────────────────────────

## Called by TerminalView when the player submits a command.
func submit_command(command: String) -> void:
	if backend:
		backend.execute_command(command)


## Called by TerminalView when the player requests tab completion.
func request_completion(partial: String, cursor: int) -> void:
	if backend:
		backend.request_completion(partial, cursor)


## Called by TerminalView when Ctrl+C is pressed and capability is unlocked.
func request_interrupt() -> void:
	if backend:
		backend.request_interrupt()


# ── Layout ────────────────────────────────────────────────────────────────────

func _apply_initial_layout() -> void:
	_update_layout(get_viewport().get_visible_rect().size.x)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_update_layout(size.x)


func _update_layout(width: float) -> void:
	# Responsive layout handled here once child scenes exist.
	# Stub: full implementation deferred to Milestone 5.
	pass


# ── Focus management ─────────────────────────────────────────────────────────

## Return keyboard focus to the terminal input.
## Called after any non-terminal GUI interaction completes.
func return_focus_to_terminal() -> void:
	if terminal_view and terminal_view.has_method("grab_input_focus"):
		terminal_view.grab_input_focus()
