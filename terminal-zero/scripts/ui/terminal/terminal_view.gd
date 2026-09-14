## TerminalView
## Shell presentation layer for Terminal Zero — Milestone 1.
##
## Owned by: Terminal Agent
## Milestone: 1 — Functional terminal
##
## ── Responsibilities ──────────────────────────────────────────────────────────
##
##   - Render the shell prompt.
##   - Capture command input via a transparent LineEdit.
##   - Commit prompt + command into immutable scrollback on Enter.
##   - Display output chunks from the backend adapter.
##   - Support basic mouse-wheel scrollback.
##   - Forward commands and completion requests via signals (not node paths).
##
## ── What this script does NOT do ─────────────────────────────────────────────
##
##   - Parse commands.
##   - Inspect the filesystem.
##   - Compute telemetry.
##   - Own mission logic.
##
## ── Public API (required by FOUNDATION_CONTRACT.md) ──────────────────────────
##
##   func append_output(chunks: Array) -> void
##   func on_command_finished() -> void
##   func set_prompt(prompt: String) -> void
##   func apply_capabilities(caps: ShellCapabilities) -> void
##   func show_completion(candidates: Array) -> void
##   func grab_input_focus() -> void
##
class_name TerminalView
extends Control

# ── Signals (wired by MainUI or test harness, never by node paths) ─────────────

## Emitted when the player presses Enter on a non-empty command.
signal command_submitted(command: String)

## Emitted when the player presses Tab requesting completion.
signal completion_requested(partial: String, cursor: int)

## Emitted when the player presses Ctrl+C and capability is active.
signal interrupt_requested()


# ── Internal state ─────────────────────────────────────────────────────────────

## Current prompt string (e.g. "alice@osiris:~$ ").
var _prompt: String = "guest@osiris:~$ "

## Live capabilities — updated via apply_capabilities().
var _caps: ShellCapabilities = ShellCapabilities.create_default()

## Whether a command is currently executing (blocks new input).
var _busy: bool = false

## Command history buffer (capability-gated).
var _history: Array[String] = []
var _history_index: int = -1       # -1 = not browsing

## Saved draft command while browsing history.
var _history_draft: String = ""

## Whether the viewport is pinned to the bottom (auto-scroll).
var _at_bottom: bool = true


# ── Scene node references ──────────────────────────────────────────────────────

## Scrollback container — RichTextLabel inside a ScrollContainer.
@onready var _scroll: ScrollContainer = $VBox/ScrollContainer
@onready var _output: RichTextLabel   = $VBox/ScrollContainer/OutputLabel

## NEW OUTPUT indicator (hidden when at bottom).
@onready var _new_output_bar: Label   = $VBox/NewOutputBar

## Input row — sits below the scrollback.
@onready var _input_row:    HBoxContainer = $VBox/InputRow
@onready var _prompt_label: Label         = $VBox/InputRow/PromptLabel
@onready var _line_edit:    LineEdit      = $VBox/InputRow/CommandLineEdit


# ── Godot lifecycle ────────────────────────────────────────────────────────────

func _ready() -> void:
	_apply_terminal_style()
	_prompt_label.text = _prompt
	_new_output_bar.visible = false
	_line_edit.grab_focus()
	_line_edit.text_submitted.connect(_on_text_submitted)
	_scroll.get_v_scroll_bar().value_changed.connect(_on_scroll_changed)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		_handle_key(event)


# ── Style helpers ─────────────────────────────────────────────────────────────

## Monospace colour palette (phosphor green on near-black).
const COLOR_DEFAULT    := Color("c8c8c8")
const COLOR_SUCCESS    := Color("4caf50")
const COLOR_INFO       := Color("29b6f6")
const COLOR_WARNING    := Color("ffb300")
const COLOR_ERROR      := Color("ef5350")
const COLOR_DIRECTORY  := Color("42a5f5")
const COLOR_EXECUTABLE := Color("66bb6a")
const COLOR_SPECIAL    := Color("ab47bc")
const COLOR_DIM        := Color("757575")
const COLOR_BG         := Color("0d0d0d")


func _apply_terminal_style() -> void:
	# Background
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_BG
	add_theme_stylebox_override("panel", style)

	# OutputLabel — transparent background, scrollback text
	_output.bbcode_enabled = true
	_output.scroll_active = false   # ScrollContainer owns scrolling
	_output.fit_content = true
	_output.selection_enabled = true
	_output.add_theme_color_override("default_color", COLOR_DEFAULT)

	# Prompt label
	_prompt_label.add_theme_color_override("font_color", COLOR_DEFAULT)

	# LineEdit — visually invisible inside the terminal
	_line_edit.add_theme_color_override("font_color", COLOR_DEFAULT)
	_line_edit.add_theme_color_override("font_placeholder_color", COLOR_DIM)
	var le_style := StyleBoxEmpty.new()
	_line_edit.add_theme_stylebox_override("normal", le_style)
	_line_edit.add_theme_stylebox_override("focus", le_style)
	_line_edit.add_theme_stylebox_override("read_only", le_style)

	# NEW OUTPUT bar
	_new_output_bar.add_theme_color_override("font_color", COLOR_WARNING)
	_new_output_bar.text = "▼ NEW OUTPUT"
	_new_output_bar.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER


# ── Role → BBCode colour helper ───────────────────────────────────────────────

func _role_to_color(role: StringName) -> Color:
	match role:
		TerminalChunk.ROLE_SUCCESS:    return COLOR_SUCCESS
		TerminalChunk.ROLE_INFO:       return COLOR_INFO
		TerminalChunk.ROLE_WARNING:    return COLOR_WARNING
		TerminalChunk.ROLE_ERROR:      return COLOR_ERROR
		TerminalChunk.ROLE_DIRECTORY:  return COLOR_DIRECTORY
		TerminalChunk.ROLE_EXECUTABLE: return COLOR_EXECUTABLE
		TerminalChunk.ROLE_SPECIAL:    return COLOR_SPECIAL
		TerminalChunk.ROLE_DIM:        return COLOR_DIM
		_:                             return COLOR_DEFAULT


func _chunks_to_bbcode(chunks: Array) -> String:
	var out := ""
	for ch in chunks:
		if ch is TerminalChunk:
			var col := _role_to_color(ch.style_role)
			var hex := "#%02x%02x%02x" % [
				int(col.r * 255), int(col.g * 255), int(col.b * 255)
			]
			# Escape [ and ] so they don't confuse BBCode parser.
			var safe = ch.text.replace("[", "[lb]")
			out += "[color=%s]%s[/color]" % [hex, safe]
	return out


# ── Scrollback management ─────────────────────────────────────────────────────

## Append a line of BBCode text to the scrollback output.
func _append_bbcode(bbcode: String) -> void:
	_output.append_text(bbcode)
	if _at_bottom:
		_scroll_to_bottom()
	else:
		_new_output_bar.visible = true


func _scroll_to_bottom() -> void:
	if not is_inside_tree():
		return
	await get_tree().process_frame
	if not is_inside_tree():
		return
	_scroll.scroll_vertical = int(_scroll.get_v_scroll_bar().max_value)
	_new_output_bar.visible = false


func _on_scroll_changed(value: float) -> void:
	var bar := _scroll.get_v_scroll_bar()
	var at_max := value >= bar.max_value - bar.page
	if at_max != _at_bottom:
		_at_bottom = at_max
		if _at_bottom:
			_new_output_bar.visible = false


# ── Key handling ──────────────────────────────────────────────────────────────

func _handle_key(event: InputEventKey) -> void:
	# Ctrl+C — interrupt (capability-gated, consumes event)
	if InputMap.has_action("terminal_interrupt") and \
	   Input.is_action_just_pressed("terminal_interrupt"):
		if _caps.interrupt:
			get_viewport().set_input_as_handled()
			interrupt_requested.emit()
		return

	# Tab — completion request (capability-gated)
	if event.keycode == KEY_TAB:
		get_viewport().set_input_as_handled()
		if _caps.tab_completion and not _busy:
			completion_requested.emit(_line_edit.text, _line_edit.caret_column)
		return

	# Up — history navigate backward (capability-gated)
	if event.keycode == KEY_UP:
		if _caps.command_history and _history.size() > 0 and not _busy:
			get_viewport().set_input_as_handled()
			_history_navigate(1)
		return

	# Down — history navigate forward (capability-gated)
	if event.keycode == KEY_DOWN:
		if _caps.command_history and not _busy:
			get_viewport().set_input_as_handled()
			_history_navigate(-1)
		return


# ── History navigation ─────────────────────────────────────────────────────────

func _history_navigate(direction: int) -> void:
	if not _caps.command_history or _history.is_empty() or _busy:
		return

	# Save draft when starting to browse.
	if _history_index == -1:
		_history_draft = _line_edit.text

	_history_index = clampi(_history_index + direction, -1, _history.size() - 1)

	if _history_index == -1:
		_line_edit.text = _history_draft
	else:
		# Index 0 = most recent command, last = oldest command.
		var pos := (_history.size() - 1) - _history_index
		_line_edit.text = _history[pos]

	_line_edit.caret_column = _line_edit.text.length()


# ── Submit handler ─────────────────────────────────────────────────────────────

func _on_text_submitted(command: String) -> void:
	if _busy:
		return

	# Clear input.
	_line_edit.text = ""
	_line_edit.grab_focus()

	# Record history (skip blank commands, skip duplicates at top).
	if command.strip_edges() != "":
		if _history.is_empty() or _history.back() != command:
			_history.append(command)
	_history_index = -1
	_history_draft = ""

	# Lock input while backend processes.
	_busy = true
	_input_row.visible = false

	# Forward to backend.
	command_submitted.emit(command)


# ── Public API ────────────────────────────────────────────────────────────────

## Append structured output from the backend.
## chunks: Array[TerminalChunk]
func append_output(chunks: Array) -> void:
	var bbcode := _chunks_to_bbcode(chunks)
	_append_bbcode(bbcode)


## Called when the backend signals the command is complete.
func on_command_finished() -> void:
	_busy = false
	_input_row.visible = true
	_line_edit.grab_focus()
	_scroll_to_bottom()


## Update the displayed prompt string.
func set_prompt(prompt: String) -> void:
	_prompt = prompt
	_prompt_label.text = prompt


## Update capability flags — gates history, completion, interrupt.
func apply_capabilities(caps: ShellCapabilities) -> void:
	_caps = caps


## Handle completion candidates from the backend.
## Follows traditional shell semantics:
##   - unique candidate: complete in-place
##   - multiple candidates: print into terminal output (no popup)
func show_completion(candidates: Array) -> void:
	if candidates.is_empty():
		return

	if candidates.size() == 1:
		# Complete the last word in the input.
		var current := _line_edit.text
		var parts := current.split(" ")
		parts[-1] = candidates[0]
		_line_edit.text = " ".join(parts)
		_line_edit.caret_column = _line_edit.text.length()
		return

	# Ambiguous: find common prefix and print candidates.
	var prefix := _common_prefix(candidates)
	if prefix.length() > 0:
		var current := _line_edit.text
		var parts := current.split(" ")
		parts[-1] = prefix
		_line_edit.text = " ".join(parts)
		_line_edit.caret_column = _line_edit.text.length()

	var listing := "  ".join(candidates) + "\n"
	_append_bbcode("[color=#c8c8c8]%s[/color]" % listing.replace("[", "[lb]"))
	# Re-emit the prompt line so the player sees where they were.
	_append_bbcode("[color=#c8c8c8]%s%s[/color]" % [
		_prompt.replace("[", "[lb]"),
		_line_edit.text.replace("[", "[lb]")
	])


## Return keyboard focus to the terminal command input.
func grab_input_focus() -> void:
	_line_edit.grab_focus()


# ── Helpers ───────────────────────────────────────────────────────────────────

func _common_prefix(words: Array) -> String:
	if words.is_empty():
		return ""
	var prefix: String = words[0]
	for w in words.slice(1):
		while not w.begins_with(prefix):
			prefix = prefix.left(prefix.length() - 1)
			if prefix.is_empty():
				return ""
	return prefix
