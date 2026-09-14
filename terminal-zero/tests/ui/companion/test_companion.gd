## test_companion.gd
## Standalone visual harness + automated acceptance tests for CompanionWorkspace.
##
## Owned by: Companion Agent
## Milestone: 1
##
## Features:
##   - Runs standalone without main_ui.tscn
##   - Uses StubBackendAdapter to drive documents, capabilities, and telemetry
##   - Interactive Terminal simulation to verify primary keyboard focus is preserved
##   - Interactive document buttons for manual verification of all milestone behaviors
##   - Automated acceptance tests (B1–B6) runnable in headless CI or via GUI button

extends Control

const TEST_PASS := "[PASS]"
const TEST_FAIL := "[FAIL]"

# ── References ─────────────────────────────────────────────────────────────────

var _stub: StubBackendAdapter
var _workspace: CompanionWorkspace
var _terminal_output: RichTextLabel
var _terminal_input: LineEdit
var _log_label: RichTextLabel
var _status_label: Label
var _results: Array[String] = []

# ── Sample documents ───────────────────────────────────────────────────────────

var _doc_a: CompanionDocument
var _doc_b: CompanionDocument
var _doc_c: CompanionDocument
var _doc_d: CompanionDocument
var _guide_doc: CompanionDocument

var _mono_font: Font


func _ready() -> void:
	_mono_font = SystemFont.new()
	(_mono_font as SystemFont).font_names = PackedStringArray(["Monospace", "Courier New", "Courier"])

	_build_docs()
	_build_ui()
	_setup_adapter()

	# In headless mode, run tests automatically and quit.
	# In graphical mode, run tests to populate the log, then restore interactive state.
	call_deferred("_initialize_scene")


func _initialize_scene() -> void:
	_stub.unlock_capability("companion_workspace")
	_run_all_tests()
	# Restore initial documents for manual verification in graphical mode
	_stub.unlock_capability("companion_workspace")
	_stub.fire_open_document("guide.txt", "OSIRIS LOG GUIDE", _guide_content())
	_stub.fire_open_document("doc_a", "Morgan Notes", _doc_a.content)
	_stub.fire_open_document("doc_b", "Mission Dossier", _doc_b.content)
	_update_status_display()
	_terminal_input.grab_focus()

	if DisplayServer.get_name() == "headless":
		var passed := _results.filter(func(r): return r.begins_with(TEST_PASS)).size()
		var total := _results.size()
		if passed < total:
			push_error("Some acceptance tests failed!")


func _build_docs() -> void:
	_guide_doc = CompanionDocument.create(
		"guide.txt",
		"LOG_GUIDE",
		_guide_content(),
		"/home/alice/docs/guide.txt",
		CompanionDocument.TYPE_GUIDE
	)
	_doc_a = CompanionDocument.create(
		"doc_a",
		"Morgan Notes",
		"=== Morgan Notes (Forensic Log) ===\n\n" +
		"[08:14:02] System integrity check initiated.\n" +
		"[08:14:15] Buffer subsystem reporting MINIMAL state.\n" +
		"[08:15:33] Suspected unauthorized daemon injecting faults into cluster.\n" +
		"[08:16:01] Key fragment stored in /home/alice/notes/phoenix_alpha.sig\n" +
		"[08:17:40] Recovery procedure: restore buffer, re-enable bashrc, unlock companion.\n\n" +
		"End of note.\n",
		"/home/alice/notes/morgan.txt",
		CompanionDocument.TYPE_LOG
	)
	_doc_b = CompanionDocument.create(
		"doc_b",
		"Mission Dossier",
		"=== MISSION DOSSIER: OPERATION PHOENIX ===\n\n" +
		"CLASSIFICATION: RESTRICTED // OSIRIS CORE\n" +
		"STATUS: ACTIVE INVESTIGATION\n\n" +
		"OBJECTIVES:\n" +
		"  1. Inspect corrupted logs using 'grep' and 'cat'.\n" +
		"  2. Use 'less' to examine forensic guides in companion workspace.\n" +
		"  3. Isolate the rogue miner process consuming 91% CPU.\n" +
		"  4. Re-establish network link to gateway node.\n\n" +
		"SECURITY NOTICE:\n" +
		"  Terminal keyboard focus must remain uninhibited at all times.\n" +
		"  Alt shortcuts govern the companion workspace exclusively.\n",
		"/home/alice/mission.txt",
		CompanionDocument.TYPE_MISSION
	)
	_doc_c = CompanionDocument.create(
		"doc_c",
		"CPU Manual",
		"=== OSIRIS CPU & MINER DIAGNOSTIC REFERENCE ===\n\n" +
		"DIAGNOSTIC CODE: 0x91F4\n" +
		"LOAD STATUS: CRITICAL [91%]\n\n" +
		"COMMANDS:\n" +
		"  top        - Display active system tasks and CPU usage\n" +
		"  ps aux     - List all running process identifiers\n" +
		"  kill -9    - Terminate offending task\n\n" +
		"NOTE: When telemetry is degraded, CPU readings may display [NO DATA].\n",
		"/home/alice/docs/cpu_manual.txt",
		CompanionDocument.TYPE_MANUAL
	)
	_doc_d = CompanionDocument.create(
		"doc_d",
		"Network Log",
		"=== CLUSTER GATEWAY LOG [net.log] ===\n\n" +
		"[WARN] Connection timeout to gateway node 192.168.1.1:8080\n" +
		"[INFO] Ethernet link status: DOWN\n" +
		"[WARN] Packet retry count exceeded (attempt 5/5)\n" +
		"[INFO] Cluster gateway status set to [???]\n" +
		"[ERROR] Handshake refused: remote node unresponsive\n",
		"/home/alice/logs/net.log",
		CompanionDocument.TYPE_LOG
	)


func _guide_content() -> String:
	var lines := PackedStringArray()
	lines.append("┌─────────────────────────────────────────┐")
	lines.append("│  OSIRIS WORKSTATION // COMPANION GUIDE   │")
	lines.append("├─────────────────────────────────────────┤")
	lines.append("│  Authentic Unix Commands:                │")
	lines.append("│    grep PATTERN FILE                     │")
	lines.append("│      -i   ignore case                    │")
	lines.append("│      -n   line numbers                   │")
	lines.append("│      -r   recursive directory search     │")
	lines.append("│                                          │")
	lines.append("│    less FILE                             │")
	lines.append("│      opens companion reader (split-view) │")
	lines.append("│                                          │")
	lines.append("│    cat FILE                              │")
	lines.append("│      prints output directly to terminal  │")
	lines.append("├─────────────────────────────────────────┤")
	lines.append("│  Companion Keyboard Controls:            │")
	lines.append("│    Alt+Up / Alt+Down   - Scroll 1 line   │")
	lines.append("│    Alt+PgUp / Alt+PgDn - Page scroll     │")
	lines.append("│    Alt+Home / Alt+End  - Jump to bounds  │")
	lines.append("│    Alt+1 / Alt+2 / 3   - Switch tabs     │")
	lines.append("│    Alt+W               - Close active tab│")
	lines.append("│    Mouse Wheel         - Scroll document │")
	lines.append("├─────────────────────────────────────────┤")
	for i in range(25):
		lines.append("│  [REF-00%02d] Diagnostic buffer row %-6d│" % [i, i * 4])
	lines.append("└─────────────────────────────────────────┘")
	return "\n".join(lines)


# ── UI Construction ───────────────────────────────────────────────────────────

func _build_ui() -> void:
	# Root background
	var bg := ColorRect.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.04, 0.04, 0.04, 1.0)
	add_child(bg)

	var root_vbox := VBoxContainer.new()
	root_vbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_vbox.add_theme_constant_override("separation", 2)
	add_child(root_vbox)

	# ── Top Bar ───────────────────────────────────────────────────────────────
	var top_bar := Panel.new()
	top_bar.custom_minimum_size = Vector2(0, 32)
	var top_style := StyleBoxFlat.new()
	top_style.bg_color = Color(0.08, 0.08, 0.08, 1.0)
	top_style.border_width_bottom = 1
	top_style.border_color = Color(0.3, 0.3, 0.3, 1.0)
	top_bar.add_theme_stylebox_override("panel", top_style)
	root_vbox.add_child(top_bar)

	var top_hbox := HBoxContainer.new()
	top_hbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	top_hbox.add_theme_constant_override("margin_left", 12)
	top_hbox.add_theme_constant_override("margin_right", 12)
	top_bar.add_child(top_hbox)

	var title_lbl := Label.new()
	title_lbl.text = " OSIRIS // COMPANION WORKSPACE STANDALONE HARNESS (MILESTONE 1) "
	title_lbl.add_theme_font_override("font", _mono_font)
	title_lbl.add_theme_font_size_override("font_size", 14)
	title_lbl.add_theme_color_override("font_color", Color(0.9, 0.8, 0.4, 1.0))
	top_hbox.add_child(title_lbl)

	var top_spacer := Control.new()
	top_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_hbox.add_child(top_spacer)

	_status_label = Label.new()
	_status_label.text = "Tabs: 0/3 | Mode: SIDE_PANE | Cap: ON"
	_status_label.add_theme_font_override("font", _mono_font)
	_status_label.add_theme_font_size_override("font_size", 13)
	_status_label.add_theme_color_override("font_color", Color(0.6, 0.8, 1.0, 1.0))
	top_hbox.add_child(_status_label)

	# ── Main Workspace Area (Columns: Terminal | Companion | Control Panel) ───
	var main_hbox := HBoxContainer.new()
	main_hbox.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_hbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_hbox.add_theme_constant_override("separation", 4)
	root_vbox.add_child(main_hbox)

	# Column 1: Mock Terminal
	var term_panel := _build_terminal_column()
	term_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	term_panel.size_flags_stretch_ratio = 1.1
	main_hbox.add_child(term_panel)

	# Column 2: CompanionWorkspace
	_workspace = CompanionWorkspace.new()
	_workspace.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_workspace.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_workspace.size_flags_stretch_ratio = 1.0
	main_hbox.add_child(_workspace)

	# Column 3: Manual Verification & Test Control Sidebar
	var side_panel := _build_sidebar_column()
	side_panel.custom_minimum_size = Vector2(360, 0)
	side_panel.size_flags_horizontal = Control.SIZE_SHRINK_END
	main_hbox.add_child(side_panel)


func _build_terminal_column() -> Panel:
	var panel := Panel.new()
	var p_style := StyleBoxFlat.new()
	p_style.bg_color = Color(0.05, 0.05, 0.05, 1.0)
	p_style.border_width_left = 1
	p_style.border_width_top = 1
	p_style.border_width_right = 1
	p_style.border_width_bottom = 1
	p_style.border_color = Color(0.25, 0.25, 0.25, 1.0)
	panel.add_theme_stylebox_override("panel", p_style)

	var vbox := VBoxContainer.new()
	vbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vbox.add_theme_constant_override("separation", 2)
	panel.add_child(vbox)

	# Terminal Header
	var header := Label.new()
	header.text = " [TERMINAL - Primary Keyboard Focus (Home)]"
	header.add_theme_font_override("font", _mono_font)
	header.add_theme_font_size_override("font_size", 13)
	header.add_theme_color_override("font_color", Color(0.5, 0.7, 0.5, 1.0))
	vbox.add_child(header)

	var sep := HSeparator.new()
	vbox.add_child(sep)

	# Scrollback Output
	var out_scroll := ScrollContainer.new()
	out_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	out_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_child(out_scroll)

	_terminal_output = RichTextLabel.new()
	_terminal_output.bbcode_enabled = true
	_terminal_output.fit_content = true
	_terminal_output.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_terminal_output.add_theme_font_override("normal_font", _mono_font)
	_terminal_output.add_theme_font_size_override("normal_font_size", 14)
	_terminal_output.add_theme_color_override("default_color", Color(0.85, 0.85, 0.75, 1.0))
	_terminal_output.text = (
		"[color=#66aa66]OSIRIS Workstation [Rev 4.7.2][/color]\n" +
		"Session active for user alice@osiris.\n" +
		"Type commands below. Try: [color=cyan]less guide.txt[/color], [color=cyan]ls[/color], [color=cyan]whoami[/color], [color=cyan]help[/color].\n" +
		"[color=yellow]Notice:[/color] Terminal remains keyboard home. Alt shortcuts operate companion without focus loss.\n\n"
	)
	out_scroll.add_child(_terminal_output)

	# Input Row
	var input_hbox := HBoxContainer.new()
	input_hbox.custom_minimum_size = Vector2(0, 28)
	vbox.add_child(input_hbox)

	var prompt_lbl := Label.new()
	prompt_lbl.text = " alice@osiris:~$ "
	prompt_lbl.add_theme_font_override("font", _mono_font)
	prompt_lbl.add_theme_font_size_override("font_size", 14)
	prompt_lbl.add_theme_color_override("font_color", Color(0.4, 0.9, 0.4, 1.0))
	input_hbox.add_child(prompt_lbl)

	_terminal_input = LineEdit.new()
	_terminal_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_terminal_input.add_theme_font_override("font", _mono_font)
	_terminal_input.add_theme_font_size_override("font_size", 14)
	_terminal_input.placeholder_text = "Type shell commands here (e.g. less guide.txt)..."
	_terminal_input.text_submitted.connect(_on_terminal_command_submitted)
	input_hbox.add_child(_terminal_input)

	return panel


func _build_sidebar_column() -> Panel:
	var panel := Panel.new()
	var p_style := StyleBoxFlat.new()
	p_style.bg_color = Color(0.04, 0.04, 0.04, 1.0)
	p_style.border_width_left = 1
	p_style.border_color = Color(0.3, 0.3, 0.3, 1.0)
	panel.add_theme_stylebox_override("panel", p_style)

	var scroll := ScrollContainer.new()
	scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.add_child(scroll)

	var vbox := VBoxContainer.new()
	vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vbox.add_theme_constant_override("separation", 6)
	scroll.add_child(vbox)

	# Sidebar Title
	var title := Label.new()
	title.text = " MANUAL VERIFICATION PANEL"
	title.add_theme_font_override("font", _mono_font)
	title.add_theme_font_size_override("font_size", 13)
	title.add_theme_color_override("font_color", Color(0.9, 0.8, 0.4, 1.0))
	vbox.add_child(title)

	vbox.add_child(HSeparator.new())

	# Document Launchers
	var doc_hdr := Label.new()
	doc_hdr.text = "── 1. Open Document (StubAdapter) ──"
	doc_hdr.add_theme_font_override("font", _mono_font)
	doc_hdr.add_theme_font_size_override("font_size", 12)
	doc_hdr.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7, 1.0))
	vbox.add_child(doc_hdr)

	vbox.add_child(_make_btn("Open guide.txt (Log Guide)", func(): _stub.fire_open_document("guide.txt", "OSIRIS LOG GUIDE", _guide_content())))
	vbox.add_child(_make_btn("Open Doc A (Morgan Notes)", func(): _stub.fire_open_document("doc_a", "Morgan Notes", _doc_a.content)))
	vbox.add_child(_make_btn("Open Doc B (Mission Dossier)", func(): _stub.fire_open_document("doc_b", "Mission Dossier", _doc_b.content)))
	vbox.add_child(_make_btn("Open Doc C (CPU Manual)", func(): _stub.fire_open_document("doc_c", "CPU Manual", _doc_c.content)))
	vbox.add_child(_make_btn("Open Doc D (Network Log)", func(): _stub.fire_open_document("doc_d", "Network Log", _doc_d.content)))

	vbox.add_child(HSeparator.new())

	# Layout & Capabilities
	var ctrl_hdr := Label.new()
	ctrl_hdr.text = "── 2. Component Controls ──"
	ctrl_hdr.add_theme_font_override("font", _mono_font)
	ctrl_hdr.add_theme_font_size_override("font_size", 12)
	ctrl_hdr.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7, 1.0))
	vbox.add_child(ctrl_hdr)

	vbox.add_child(_make_btn("Toggle Mode (Side Pane / Overlay)", _toggle_mode))
	vbox.add_child(_make_btn("Toggle Capability (ON / OFF)", _toggle_capability))
	vbox.add_child(_make_btn("Close Active Tab (Alt+W)", func(): _workspace.close_active_tab()))
	vbox.add_child(_make_btn("Run Acceptance Tests (B1-B6)", _run_all_tests))

	vbox.add_child(HSeparator.new())

	# Keyboard Shortcut Reference
	var ref_hdr := Label.new()
	ref_hdr.text = "── 3. Manual Key Verification ──\n" + \
		" • Alt+1 / 2 / 3 : Switch tabs\n" + \
		" • Alt+W        : Close active tab\n" + \
		" • Alt+Up/Down  : Scroll 1 line\n" + \
		" • Alt+PgUp/Dn  : Scroll 1 page\n" + \
		" • Alt+Home/End : Document bounds\n" + \
		" • Mouse Wheel  : Scroll active doc\n" + \
		" • 4th Tab      : Evicts oldest inactive\n" + \
		" • Type in input: Normal keys uncaptured"
	ref_hdr.add_theme_font_override("font", _mono_font)
	ref_hdr.add_theme_font_size_override("font_size", 11)
	ref_hdr.add_theme_color_override("font_color", Color(0.65, 0.65, 0.65, 1.0))
	vbox.add_child(ref_hdr)

	vbox.add_child(HSeparator.new())

	# Log Output
	var log_hdr := Label.new()
	log_hdr.text = "── 4. Test & Event Log ──"
	log_hdr.add_theme_font_override("font", _mono_font)
	log_hdr.add_theme_font_size_override("font_size", 12)
	log_hdr.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7, 1.0))
	vbox.add_child(log_hdr)

	_log_label = RichTextLabel.new()
	_log_label.bbcode_enabled = true
	_log_label.fit_content = true
	_log_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_log_label.add_theme_font_override("normal_font", _mono_font)
	_log_label.add_theme_font_size_override("normal_font_size", 12)
	vbox.add_child(_log_label)

	return panel


func _make_btn(label: String, callback: Callable) -> Button:
	var btn := Button.new()
	btn.text = label
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	btn.focus_mode = Control.FOCUS_NONE
	btn.add_theme_font_override("font", _mono_font)
	btn.add_theme_font_size_override("font_size", 12)
	btn.pressed.connect(callback)
	btn.pressed.connect(func(): _terminal_input.grab_focus())
	return btn


# ── Adapter Setup ─────────────────────────────────────────────────────────────

func _setup_adapter() -> void:
	_stub = StubBackendAdapter.new()
	add_child(_stub)

	# Direct signal connections between Stub and Companion (Foundation Contract)
	_stub.document_requested.connect(_on_document_requested)
	_stub.shell_capabilities_changed.connect(_workspace.apply_capabilities)
	_stub.output_emitted.connect(_on_terminal_output)
	_stub.command_finished.connect(func(): _terminal_input.grab_focus())

	# When workspace requests focus return, refocus terminal input
	_workspace.focus_return_requested.connect(func(): _terminal_input.grab_focus())


func _on_document_requested(doc: CompanionDocument) -> void:
	_workspace.open_document(doc)
	_update_status_display()
	_terminal_input.grab_focus()


func _on_terminal_output(chunks: Array) -> void:
	for chunk in chunks:
		if chunk is TerminalChunk:
			var color_str := "#d0d0c0"
			match chunk.style_role:
				TerminalChunk.ROLE_SUCCESS: color_str = "green"
				TerminalChunk.ROLE_INFO: color_str = "cyan"
				TerminalChunk.ROLE_WARNING: color_str = "yellow"
				TerminalChunk.ROLE_ERROR: color_str = "red"
				TerminalChunk.ROLE_DIRECTORY: color_str = "cornflower_blue"
				TerminalChunk.ROLE_DIM: color_str = "gray"
			_terminal_output.append_text("[color=%s]%s[/color]" % [color_str, chunk.text])
		elif chunk is String:
			_terminal_output.append_text(chunk)


func _on_terminal_command_submitted(cmd: String) -> void:
	var text := cmd.strip_edges()
	if text.is_empty():
		return
	_terminal_input.clear()
	_terminal_output.append_text("alice@osiris:~$ " + text + "\n")

	if text.begins_with("less "):
		var filename := text.substr(5).strip_edges()
		_open_by_filename(filename)
	elif text == "clear":
		_terminal_output.text = ""
	else:
		_stub.execute_command(text)

	_terminal_input.grab_focus()


func _open_by_filename(filename: String) -> void:
	match filename:
		"guide.txt", "docs/guide.txt":
			_stub.fire_open_document("guide.txt", "OSIRIS LOG GUIDE", _guide_content())
		"morgan.txt", "notes/morgan.txt", "doc_a":
			_stub.fire_open_document("doc_a", "Morgan Notes", _doc_a.content)
		"mission.txt", "doc_b":
			_stub.fire_open_document("doc_b", "Mission Dossier", _doc_b.content)
		"cpu_manual.txt", "doc_c":
			_stub.fire_open_document("doc_c", "CPU Manual", _doc_c.content)
		"net.log", "logs/net.log", "doc_d":
			_stub.fire_open_document("doc_d", "Network Log", _doc_d.content)
		_:
			_terminal_output.append_text("[color=red]less: %s: No such file or directory[/color]\n" % filename)


func _toggle_mode() -> void:
	var current := _workspace.get_layout_mode()
	var new_mode := CompanionWorkspace.MODE_OVERLAY if current == CompanionWorkspace.MODE_SIDE_PANE else CompanionWorkspace.MODE_SIDE_PANE
	_workspace.set_layout_mode(new_mode)
	_update_status_display()
	_log("Layout mode set to: %s" % new_mode)
	_terminal_input.grab_focus()


func _toggle_capability() -> void:
	var caps := ShellCapabilities.create_default()
	caps.companion_workspace = not _workspace.visible
	_stub.shell_capabilities_changed.emit(caps)
	_update_status_display()
	_log("Companion capability toggled: %s" % ("ENABLED" if caps.companion_workspace else "DISABLED"))
	_terminal_input.grab_focus()


func _update_status_display() -> void:
	var mode_str := "SIDE_PANE" if _workspace.get_layout_mode() == CompanionWorkspace.MODE_SIDE_PANE else "OVERLAY"
	var cap_str := "ON" if _workspace.visible else "OFF"
	_status_label.text = "Tabs: %d/3 | Active: [%s] | Mode: %s | Cap: %s" % [
		_workspace.get_tab_count(),
		_workspace.get_active_document_id(),
		mode_str,
		cap_str
	]


# ── Acceptance Test Suite ─────────────────────────────────────────────────────

func _run_all_tests() -> void:
	_results.clear()
	_log_label.text = ""
	_log("━━━━ COMPANION ACCEPTANCE TESTS ━━━━\n")

	_test_b1_open_guide()
	_test_b2_three_tabs()
	_test_b3_eviction()
	_test_b4_existing_document()
	_test_b5_keyboard_controls()
	_test_b6_responsive_and_capabilities()
	_print_summary()


# ── B1 — Open ────────────────────────────────────────────────────────────────

func _test_b1_open_guide() -> void:
	_log("\n[b]B1 — Open guide.txt[/b]")
	_workspace_reset()
	_workspace.open_document(_guide_doc)

	var pass_one_tab := _workspace.get_tab_count() == 1
	var pass_content := _workspace.get_visible_content().contains("OSIRIS WORKSTATION")
	var pass_active  := _workspace.get_active_document_id() == "guide.txt"

	_assert(pass_one_tab, "one tab open")
	_assert(pass_content, "document content readable")
	_assert(pass_active,  "correct document is active")

	# Test independent scroll position
	_workspace.set_scroll_position(100.0)
	_workspace.open_document(_doc_b)
	_workspace.set_scroll_position(20.0)
	_workspace.open_document(_guide_doc)
	var scroll_restored := is_equal_approx(_workspace.get_scroll_position(), 100.0)
	_assert(scroll_restored, "independent scroll position preserved across tab switches")


# ── B2 — Three tabs ───────────────────────────────────────────────────────────

func _test_b2_three_tabs() -> void:
	_log("\n[b]B2 — Open A, B, C[/b]")
	_workspace_reset()
	_workspace.open_document(_doc_a)
	_workspace.open_document(_doc_b)
	_workspace.open_document(_doc_c)

	_assert(_workspace.get_tab_count() == 3, "three tabs present")


# ── B3 — Eviction ────────────────────────────────────────────────────────────

func _test_b3_eviction() -> void:
	_log("\n[b]B3 — Eviction[/b]")
	_workspace_reset()

	# Open A (oldest), B, C in that order.
	_workspace.open_document(_doc_a)
	_workspace.open_document(_doc_b)
	_workspace.open_document(_doc_c)

	# Activate C so A is oldest inactive.
	_workspace.open_document(_doc_c)
	_assert(_workspace.get_active_document_id() == "doc_c", "C is active before D opens")

	# Open D — A (oldest inactive) must be evicted.
	_workspace.open_document(_doc_d)

	_assert(_workspace.get_tab_count() == 3, "still exactly 3 tabs after eviction")

	var ids: Array[String] = []
	for i in range(_workspace.get_tab_count()):
		ids.append(_workspace.get_document_id_at(i))

	var c_remains := ids.has("doc_c")
	var a_evicted := not ids.has("doc_a")
	var b_remains := ids.has("doc_b")
	var d_present := ids.has("doc_d")

	_assert(c_remains, "C (active) survived eviction")
	_assert(a_evicted, "A (oldest inactive) was evicted")
	_assert(b_remains, "B remains")
	_assert(d_present, "D was opened")


# ── B4 — Existing document ───────────────────────────────────────────────────

func _test_b4_existing_document() -> void:
	_log("\n[b]B4 — Re-open existing document[/b]")
	_workspace_reset()
	_workspace.open_document(_doc_a)
	_workspace.open_document(_doc_b)
	# Activate A, then re-open B.
	_workspace.open_document(_doc_a)
	_workspace.open_document(_doc_b)

	_assert(_workspace.get_tab_count() == 2, "no duplicate — still 2 tabs")
	_assert(_workspace.get_active_document_id() == "doc_b", "B became active")


# ── B5 — Keyboard controls ───────────────────────────────────────────────────

func _test_b5_keyboard_controls() -> void:
	_log("\n[b]B5 — Keyboard controls[/b]")
	_workspace_reset()
	_workspace.open_document(_doc_a)
	_workspace.open_document(_doc_b)
	_workspace.open_document(_doc_c)

	# 1. Plain typing must not be consumed
	var plain_key := InputEventKey.new()
	plain_key.keycode = KEY_A
	plain_key.pressed = true
	plain_key.alt_pressed = false
	var consumed_plain := _workspace.handle_companion_input(plain_key)
	_assert(not consumed_plain, "plain typing (no Alt) is NOT consumed by companion")

	# 2. Ctrl-modified key must not be consumed by companion
	var ctrl_key := InputEventKey.new()
	ctrl_key.keycode = KEY_C
	ctrl_key.pressed = true
	ctrl_key.alt_pressed = true
	ctrl_key.ctrl_pressed = true
	var consumed_ctrl := _workspace.handle_companion_input(ctrl_key)
	_assert(not consumed_ctrl, "Ctrl+Alt key is NOT consumed by companion")

	# 3. Alt+1 switches to Tab 1 (doc_a)
	var alt1 := InputEventKey.new()
	alt1.keycode = KEY_1
	alt1.pressed = true
	alt1.alt_pressed = true
	var handled_alt1 := _workspace.handle_companion_input(alt1)
	_assert(handled_alt1, "Alt+1 was handled")
	_assert(_workspace.get_active_document_id() == "doc_a", "Alt+1 activated tab 1 (doc_a)")

	# 4. Alt+2 switches to Tab 2 (doc_b)
	var alt2 := InputEventKey.new()
	alt2.keycode = KEY_2
	alt2.pressed = true
	alt2.alt_pressed = true
	var handled_alt2 := _workspace.handle_companion_input(alt2)
	_assert(handled_alt2, "Alt+2 was handled")
	_assert(_workspace.get_active_document_id() == "doc_b", "Alt+2 activated tab 2 (doc_b)")

	# 5. Alt+Down scrolls down
	var alt_down := InputEventKey.new()
	alt_down.keycode = KEY_DOWN
	alt_down.pressed = true
	alt_down.alt_pressed = true
	var handled_down := _workspace.handle_companion_input(alt_down)
	_assert(handled_down, "Alt+Down was handled")

	# 6. Alt+Up scrolls up
	var alt_up := InputEventKey.new()
	alt_up.keycode = KEY_UP
	alt_up.pressed = true
	alt_up.alt_pressed = true
	var handled_up := _workspace.handle_companion_input(alt_up)
	_assert(handled_up, "Alt+Up was handled")

	# 7. Alt+W closes active tab
	var alt_w := InputEventKey.new()
	alt_w.keycode = KEY_W
	alt_w.pressed = true
	alt_w.alt_pressed = true
	var handled_w := _workspace.handle_companion_input(alt_w)
	_assert(handled_w, "Alt+W was handled")
	_assert(_workspace.get_tab_count() == 2, "active tab closed (2 tabs remain)")


# ── B6 — Responsive modes & Capabilities ──────────────────────────────────────

func _test_b6_responsive_and_capabilities() -> void:
	_log("\n[b]B6 — Responsive modes & Capabilities[/b]")
	_workspace.set_layout_mode(CompanionWorkspace.MODE_OVERLAY)
	_assert(_workspace.get_layout_mode() == CompanionWorkspace.MODE_OVERLAY, "OVERLAY mode set")

	_workspace.set_layout_mode(CompanionWorkspace.MODE_SIDE_PANE)
	_assert(_workspace.get_layout_mode() == CompanionWorkspace.MODE_SIDE_PANE, "SIDE_PANE mode set")

	var caps := ShellCapabilities.create_default()
	caps.companion_workspace = false
	_workspace.apply_capabilities(caps)
	_assert(not _workspace.visible, "workspace hidden when companion_workspace capability is false")

	caps.companion_workspace = true
	_workspace.apply_capabilities(caps)
	_assert(_workspace.visible, "workspace visible when companion_workspace capability is true")


# ── Helpers ───────────────────────────────────────────────────────────────────

func _workspace_reset() -> void:
	var caps := ShellCapabilities.create_default()
	caps.companion_workspace = true
	_workspace.apply_capabilities(caps)
	while _workspace.get_tab_count() > 0:
		_workspace.close_active_tab()


func _assert(condition: bool, description: String) -> void:
	var marker := TEST_PASS if condition else TEST_FAIL
	var color  := "green" if condition else "red"
	var line   := "  [color=%s]%s[/color] %s" % [color, marker, description]
	_log(line)
	_results.append("%s %s" % [marker, description])
	print("  %s %s" % [marker, description])
	if not condition:
		push_error("Companion test FAILED: %s" % description)


func _log(text: String) -> void:
	_log_label.append_text(text + "\n")


func _print_summary() -> void:
	var passed := _results.filter(func(r): return r.begins_with(TEST_PASS)).size()
	var total  := _results.size()
	var color  := "green" if passed == total else "yellow"
	_log("\n━━━━ Summary: [color=%s]%d / %d passed[/color] ━━━━" % [color, passed, total])
	print("\n=== CompanionWorkspace Milestone 1: %d / %d tests passed ===" % [passed, total])
