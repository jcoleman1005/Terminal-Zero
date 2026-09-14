## CompanionWorkspace
## Side-by-side document reader for TERMINAL ZERO.
##
## Agent B — Companion Workspace
## Owned by: Companion Agent
## Milestone: 1 — Standalone functional companion
##
## Contract:
##   open_document(doc: CompanionDocument) -> void
##   apply_capabilities(caps: ShellCapabilities) -> void
##
## Focus model:
##   Terminal is the home keyboard focus.
##   All companion keyboard interaction is Alt-modified.
##   Unmodified keystrokes are never consumed here.
##
## Tab eviction rule:
##   Max 3 tabs. On opening a 4th document:
##   - active tab is protected
##   - oldest inactive tab is evicted
##   - opening an already-open document activates it (no duplicate)
##
## Layout modes (set by integration owner or responsive logic):
##   MODE_SIDE_PANE  — anchored beside terminal, always visible
##   MODE_OVERLAY    — floating overlay on top of terminal

class_name CompanionWorkspace
extends Control

# ── Layout mode constants ──────────────────────────────────────────────────────

const MODE_SIDE_PANE := &"SIDE_PANE"
const MODE_OVERLAY   := &"OVERLAY"

const MAX_TABS := 3

# ── Scroll constants ───────────────────────────────────────────────────────────

const SCROLL_LINE_PX  := 24
const SCROLL_PAGE_FACTOR := 0.85   # fraction of visible height

# ── Visual constants ───────────────────────────────────────────────────────────

const COLOR_BG         := Color(0.06, 0.06, 0.06, 1.0)
const COLOR_BORDER     := Color(0.35, 0.35, 0.35, 1.0)
const COLOR_TAB_ACTIVE := Color(0.12, 0.12, 0.12, 1.0)
const COLOR_TAB_IDLE   := Color(0.06, 0.06, 0.06, 1.0)
const COLOR_TEXT       := Color(0.85, 0.85, 0.75, 1.0)
const COLOR_TEXT_DIM   := Color(0.45, 0.45, 0.40, 1.0)
const COLOR_HEADER_BG  := Color(0.05, 0.05, 0.05, 1.0)

# ── Internal data ──────────────────────────────────────────────────────────────

## A slot tracks one open document together with its scroll state and age.
class TabSlot:
	var doc: CompanionDocument
	var scroll_px: float = 0.0
	var open_order: int = 0     # monotonically increasing; lower = older

var _tabs: Array[TabSlot] = []       # up to MAX_TABS entries
var _active_index: int = -1          # index into _tabs (-1 = none)
var _tab_counter: int = 0            # increments on every open
var _layout_mode: StringName = MODE_SIDE_PANE
var _companion_enabled: bool = true  # can be disabled by capabilities

# ── Child nodes (built procedurally) ──────────────────────────────────────────

var _header_bar: Control
var _tab_buttons: Array[Button] = []
var _close_button: Button
var _scroll_container: ScrollContainer
var _content_label: RichTextLabel
var _border_panel: Panel
var _overlay_close_btn: Button       # visible only in overlay mode

# ── Fonts ─────────────────────────────────────────────────────────────────────

var _mono_font: Font

# ── Signals ───────────────────────────────────────────────────────────────────

## Emitted when the companion wants to return focus to the terminal.
signal focus_return_requested()


# ── Lifecycle ─────────────────────────────────────────────────────────────────

func _ready() -> void:
	_build_ui()
	_refresh_display()


func _build_ui() -> void:
	# Use a simple system monospace font.  The shared theme (Milestone 6) will
	# replace this with the project-wide font resource.
	_mono_font = SystemFont.new()
	(_mono_font as SystemFont).font_names = PackedStringArray(["Monospace", "Courier New", "Courier"])

	# Root StyleBox — border panel fills our Control rect.
	_border_panel = Panel.new()
	_border_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = COLOR_BG
	panel_style.border_width_left   = 1
	panel_style.border_width_right  = 1
	panel_style.border_width_top    = 1
	panel_style.border_width_bottom = 1
	panel_style.border_color = COLOR_BORDER
	panel_style.corner_radius_top_left     = 0
	panel_style.corner_radius_top_right    = 0
	panel_style.corner_radius_bottom_left  = 0
	panel_style.corner_radius_bottom_right = 0
	_border_panel.add_theme_stylebox_override("panel", panel_style)
	add_child(_border_panel)

	# Outer VBox.
	var vbox := VBoxContainer.new()
	vbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vbox.add_theme_constant_override("separation", 0)
	_border_panel.add_child(vbox)

	# ── Header bar ────────────────────────────────────────────────────────────
	_header_bar = Control.new()
	_header_bar.custom_minimum_size = Vector2(0, 28)
	_header_bar.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	vbox.add_child(_header_bar)

	var header_hbox := HBoxContainer.new()
	header_hbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	header_hbox.add_theme_constant_override("separation", 0)
	_header_bar.add_child(header_hbox)

	# Placeholder tab buttons (filled in _refresh_tabs).
	for i in range(MAX_TABS):
		var btn := _make_tab_button(i)
		header_hbox.add_child(btn)
		_tab_buttons.append(btn)

	# Spacer.
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_hbox.add_child(spacer)

	# Close-tab button on the right edge of header.
	_close_button = _make_close_button()
	header_hbox.add_child(_close_button)

	# ── Separator line below header ───────────────────────────────────────────
	var sep := HSeparator.new()
	var sep_style := StyleBoxFlat.new()
	sep_style.bg_color = COLOR_BORDER
	sep_style.content_margin_top = 0
	sep_style.content_margin_bottom = 0
	sep.add_theme_stylebox_override("separator", sep_style)
	vbox.add_child(sep)

	# ── Document viewport ─────────────────────────────────────────────────────
	_scroll_container = ScrollContainer.new()
	_scroll_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll_container.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll_container.vertical_scroll_mode   = ScrollContainer.SCROLL_MODE_AUTO
	vbox.add_child(_scroll_container)

	_content_label = RichTextLabel.new()
	_content_label.bbcode_enabled = false
	_content_label.fit_content = true
	_content_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_content_label.size_flags_vertical   = Control.SIZE_SHRINK_BEGIN
	_content_label.autowrap_mode = TextServer.AUTOWRAP_OFF
	_content_label.add_theme_font_override("normal_font", _mono_font)
	_content_label.add_theme_font_size_override("normal_font_size", 16)
	_content_label.add_theme_color_override("default_color", COLOR_TEXT)
	_content_label.add_theme_color_override("background_color", COLOR_BG)
	_content_label.add_theme_constant_override("margin_left",  8)
	_content_label.add_theme_constant_override("margin_right", 8)
	_content_label.add_theme_constant_override("margin_top",   6)
	_content_label.add_theme_constant_override("margin_bottom",6)
	# Remove the built-in background so our panel shows through.
	var label_bg := StyleBoxEmpty.new()
	_content_label.add_theme_stylebox_override("normal", label_bg)
	_scroll_container.add_child(_content_label)

	# ── Overlay close button (hidden in side-pane mode) ───────────────────────
	_overlay_close_btn = Button.new()
	_overlay_close_btn.text = "[X]"
	_overlay_close_btn.flat = true
	_overlay_close_btn.focus_mode = Control.FOCUS_NONE
	_overlay_close_btn.add_theme_color_override("font_color", COLOR_TEXT_DIM)
	_overlay_close_btn.add_theme_font_override("font", _mono_font)
	_overlay_close_btn.pressed.connect(_on_overlay_close_pressed)
	_overlay_close_btn.visible = false
	header_hbox.add_child(_overlay_close_btn)

	# Connect mouse-wheel scrolling.
	_scroll_container.focus_mode = Control.FOCUS_NONE
	_scroll_container.get_v_scroll_bar().focus_mode = Control.FOCUS_NONE
	_scroll_container.get_v_scroll_bar().scrolling.connect(_on_scrollbar_scrolled)


func _make_tab_button(slot_index: int) -> Button:
	var btn := Button.new()
	btn.text = "──────"
	btn.flat = true
	btn.focus_mode = Control.FOCUS_NONE
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	btn.add_theme_font_override("font", _mono_font)
	btn.add_theme_font_size_override("font_size", 14)
	btn.add_theme_color_override("font_color", COLOR_TEXT_DIM)
	btn.visible = false
	btn.pressed.connect(_on_tab_button_pressed.bind(slot_index))
	return btn


func _make_close_button() -> Button:
	var btn := Button.new()
	btn.text = " ✕ "
	btn.flat = true
	btn.focus_mode = Control.FOCUS_NONE
	btn.add_theme_color_override("font_color", COLOR_TEXT_DIM)
	btn.add_theme_font_override("font", _mono_font)
	btn.pressed.connect(func(): close_active_tab())
	return btn


# ── Public API (contract) ──────────────────────────────────────────────────────

## Open a document in the companion reader.
## If already open: activates it.
## If a free slot exists: opens in that slot.
## If all three slots are full: evicts the oldest inactive tab.
func open_document(doc: CompanionDocument) -> void:
	# Deduplication — activate if already open.
	for i in range(_tabs.size()):
		if _tabs[i].doc.document_id == doc.document_id:
			_activate_tab(i)
			return

	# Determine where to place the new tab.
	var target_slot: int = -1
	if _tabs.size() < MAX_TABS:
		# Free slot available.
		var slot := TabSlot.new()
		slot.doc = doc
		slot.open_order = _tab_counter
		_tab_counter += 1
		_tabs.append(slot)
		target_slot = _tabs.size() - 1
	else:
		# Evict oldest inactive.
		var evict_idx := _find_oldest_inactive()
		if evict_idx == -1:
			# All tabs are "active" — shouldn't happen with MAX_TABS=3, but guard.
			return
		_tabs[evict_idx].doc = doc
		_tabs[evict_idx].scroll_px = 0.0
		_tabs[evict_idx].open_order = _tab_counter
		_tab_counter += 1
		target_slot = evict_idx

	_activate_tab(target_slot)


## Called by the integration owner when shell capabilities change.
func apply_capabilities(caps: ShellCapabilities) -> void:
	_companion_enabled = caps.companion_workspace
	visible = _companion_enabled
	if not _companion_enabled:
		return
	_refresh_display()


# ── Layout mode ───────────────────────────────────────────────────────────────

## Switch between SIDE_PANE and OVERLAY presentation.
## Call this from the integration owner / responsive controller.
func set_layout_mode(mode: StringName) -> void:
	_layout_mode = mode
	_overlay_close_btn.visible = (mode == MODE_OVERLAY)
	_refresh_display()


## Current layout mode.
func get_layout_mode() -> StringName:
	return _layout_mode


# ── Tab operations ────────────────────────────────────────────────────────────

## Close the currently active tab.
func close_active_tab() -> void:
	if _active_index < 0 or _active_index >= _tabs.size():
		return
	_tabs.remove_at(_active_index)
	# Adjust active_index after removal.
	if _tabs.is_empty():
		_active_index = -1
	elif _active_index >= _tabs.size():
		_active_index = _tabs.size() - 1
	_refresh_display()
	focus_return_requested.emit()


# ── Internal helpers ──────────────────────────────────────────────────────────

func _activate_tab(index: int) -> void:
	# Save current scroll position before switching.
	if _active_index >= 0 and _active_index < _tabs.size():
		if _scroll_container != null and is_instance_valid(_scroll_container):
			var bar := _scroll_container.get_v_scroll_bar()
			if bar.max_value > bar.min_value:
				_tabs[_active_index].scroll_px = bar.value
	_active_index = index
	_refresh_display()
	if _scroll_container != null and is_instance_valid(_scroll_container) and _active_index >= 0 and _active_index < _tabs.size():
		_scroll_container.get_v_scroll_bar().value = _tabs[_active_index].scroll_px


func _find_oldest_inactive() -> int:
	var oldest_order := INF
	var oldest_idx := -1
	for i in range(_tabs.size()):
		if i == _active_index:
			continue
		if _tabs[i].open_order < oldest_order:
			oldest_order = _tabs[i].open_order
			oldest_idx = i
	return oldest_idx


func _refresh_display() -> void:
	_refresh_tabs()
	_refresh_content()


func _refresh_tabs() -> void:
	for i in range(MAX_TABS):
		var btn := _tab_buttons[i]
		if i < _tabs.size():
			var tab := _tabs[i]
			var label := _truncate(tab.doc.title, 18)
			if i == _active_index:
				btn.text = " [%s] " % label
				btn.add_theme_color_override("font_color", COLOR_TEXT)
				btn.add_theme_stylebox_override("normal", _make_tab_style(true))
				btn.add_theme_stylebox_override("hover",  _make_tab_style(true))
			else:
				btn.text = "  %s  " % label
				btn.add_theme_color_override("font_color", COLOR_TEXT_DIM)
				btn.add_theme_stylebox_override("normal", _make_tab_style(false))
				btn.add_theme_stylebox_override("hover",  _make_tab_style(false))
			btn.visible = true
		else:
			btn.text = ""
			btn.visible = false

	_close_button.visible = _active_index >= 0


func _refresh_content() -> void:
	if _active_index < 0 or _active_index >= _tabs.size():
		_content_label.text = ""
		return
	_content_label.text = _tabs[_active_index].doc.content


func _make_tab_style(active: bool) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = COLOR_TAB_ACTIVE if active else COLOR_TAB_IDLE
	s.border_width_bottom = 2 if active else 0
	s.border_color = COLOR_TEXT if active else COLOR_BORDER
	s.corner_radius_top_left     = 0
	s.corner_radius_top_right    = 0
	s.corner_radius_bottom_left  = 0
	s.corner_radius_bottom_right = 0
	return s


func _truncate(s: String, max_len: int) -> String:
	if s.length() <= max_len:
		return s
	return s.left(max_len - 1) + "…"


# ── Scrolling ─────────────────────────────────────────────────────────────────

## Scroll the active document by pixel_delta (positive = down).
## Called by Alt+Up/Down handlers; does NOT transfer keyboard focus.
func _scroll_by(pixel_delta: float) -> void:
	if _active_index >= 0 and _active_index < _tabs.size():
		_tabs[_active_index].scroll_px = maxf(0.0, _tabs[_active_index].scroll_px + pixel_delta)
	if _scroll_container == null or not is_instance_valid(_scroll_container):
		return
	var bar := _scroll_container.get_v_scroll_bar()
	bar.value = clampf(bar.value + pixel_delta, bar.min_value, bar.max_value)


func _scroll_page(direction: int) -> void:
	if _scroll_container == null or not is_instance_valid(_scroll_container):
		return
	var page_px := _scroll_container.size.y * SCROLL_PAGE_FACTOR
	_scroll_by(direction * page_px)


func _scroll_to_start() -> void:
	if _active_index >= 0 and _active_index < _tabs.size():
		_tabs[_active_index].scroll_px = 0.0
	if _scroll_container == null or not is_instance_valid(_scroll_container):
		return
	var bar := _scroll_container.get_v_scroll_bar()
	bar.value = bar.min_value


func _scroll_to_end() -> void:
	if _scroll_container == null or not is_instance_valid(_scroll_container):
		return
	var bar := _scroll_container.get_v_scroll_bar()
	bar.value = bar.max_value
	if _active_index >= 0 and _active_index < _tabs.size():
		_tabs[_active_index].scroll_px = bar.value


## Get current scroll position in pixels.
func get_scroll_position() -> float:
	if _active_index >= 0 and _active_index < _tabs.size():
		return _tabs[_active_index].scroll_px
	if _scroll_container != null and is_instance_valid(_scroll_container):
		return _scroll_container.get_v_scroll_bar().value
	return 0.0


## Set current scroll position in pixels.
func set_scroll_position(pos: float) -> void:
	if _active_index >= 0 and _active_index < _tabs.size():
		_tabs[_active_index].scroll_px = pos
	if _scroll_container != null and is_instance_valid(_scroll_container):
		var bar := _scroll_container.get_v_scroll_bar()
		bar.value = pos


# ── Input handling ────────────────────────────────────────────────────────────

## Handle Alt-modified shortcuts without stealing terminal text-entry focus.
## Returns true only when the event was consumed.
func handle_companion_input(event: InputEvent) -> bool:
	if not visible or not _companion_enabled:
		return false
	if not (event is InputEventKey):
		return false
	var key_event := event as InputEventKey
	if not key_event.pressed or key_event.is_echo():
		return false
	if not key_event.alt_pressed:
		return false
	if key_event.ctrl_pressed or key_event.shift_pressed or key_event.meta_pressed:
		return false

	var kc := key_event.keycode
	if kc == KEY_NONE:
		kc = key_event.physical_keycode

	if event.is_action_pressed(&"ui_companion_scroll_up") or kc == KEY_UP:
		_scroll_by(-SCROLL_LINE_PX)
		return true
	if event.is_action_pressed(&"ui_companion_scroll_down") or kc == KEY_DOWN:
		_scroll_by(SCROLL_LINE_PX)
		return true
	if event.is_action_pressed(&"ui_companion_page_up") or kc == KEY_PAGEUP:
		_scroll_page(-1)
		return true
	if event.is_action_pressed(&"ui_companion_page_down") or kc == KEY_PAGEDOWN:
		_scroll_page(1)
		return true
	if event.is_action_pressed(&"ui_companion_doc_start") or kc == KEY_HOME:
		_scroll_to_start()
		return true
	if event.is_action_pressed(&"ui_companion_doc_end") or kc == KEY_END:
		_scroll_to_end()
		return true
	if event.is_action_pressed(&"ui_companion_tab_1") or kc == KEY_1:
		if _tabs.size() >= 1:
			_activate_tab(0)
		return true
	if event.is_action_pressed(&"ui_companion_tab_2") or kc == KEY_2:
		if _tabs.size() >= 2:
			_activate_tab(1)
		return true
	if event.is_action_pressed(&"ui_companion_tab_3") or kc == KEY_3:
		if _tabs.size() >= 3:
			_activate_tab(2)
		return true
	if event.is_action_pressed(&"ui_companion_close_tab") or kc == KEY_W:
		close_active_tab()
		return true

	return false


func _unhandled_key_input(event: InputEvent) -> void:
	if handle_companion_input(event):
		get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	if handle_companion_input(event):
		get_viewport().set_input_as_handled()


# ── Mouse wheel on the scroll container ──────────────────────────────────────

func _on_scrollbar_scrolled() -> void:
	# Save scroll state when the user drags the scrollbar.
	if _active_index >= 0 and _active_index < _tabs.size():
		_tabs[_active_index].scroll_px = _scroll_container.get_v_scroll_bar().value


func _gui_input(event: InputEvent) -> void:
	# Allow mouse-wheel scroll to operate without altering keyboard focus.
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				_scroll_by(-SCROLL_LINE_PX * 3)
				accept_event()
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_scroll_by(SCROLL_LINE_PX * 3)
				accept_event()


# ── Button callbacks ──────────────────────────────────────────────────────────

func _on_tab_button_pressed(slot_index: int) -> void:
	if slot_index < _tabs.size():
		_activate_tab(slot_index)
	focus_return_requested.emit()


func _on_overlay_close_pressed() -> void:
	visible = false
	focus_return_requested.emit()


# ── Test / introspection helpers ──────────────────────────────────────────────

## Returns the number of currently open tabs.
func get_tab_count() -> int:
	return _tabs.size()


## Returns the document_id of the active tab, or "" if none.
func get_active_document_id() -> String:
	if _active_index < 0 or _active_index >= _tabs.size():
		return ""
	return _tabs[_active_index].doc.document_id


## Returns the document_id at slot [i], or "" if that slot is empty.
func get_document_id_at(i: int) -> String:
	if i < 0 or i >= _tabs.size():
		return ""
	return _tabs[i].doc.document_id


## Returns the content currently shown in the viewport.
func get_visible_content() -> String:
	return _content_label.text
