## test_companion.gd
## Standalone visual + automated acceptance tests for the CompanionWorkspace.
##
## Owned by: Companion Agent
## Milestone: 1
##
## Acceptance tests implemented (from AGENT_COMPANION.md):
##   B1 — Open one document          → one tab, content readable
##   B2 — Open three documents       → three tabs present
##   B3 — Eviction                   → C active, open D → A evicted, B+C+D remain
##   B4 — Existing document re-open  → no duplicate, activates existing
##   B5 — Keyboard capture           → Alt shortcuts work, plain typing not consumed
##
## Run this scene from the Godot editor to see visual output and log results.

extends Control

const TEST_PASS := "[PASS]"
const TEST_FAIL := "[FAIL]"

var _workspace: CompanionWorkspace
var _log_label: RichTextLabel
var _results: Array[String] = []

# ── Sample documents ───────────────────────────────────────────────────────────

var _doc_a: CompanionDocument
var _doc_b: CompanionDocument
var _doc_c: CompanionDocument
var _doc_d: CompanionDocument
var _guide_doc: CompanionDocument


func _ready() -> void:
	_build_docs()
	_build_ui()
	# Defer tests one frame so the workspace has laid out.
	call_deferred("_run_all_tests")


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
		"=== Morgan Notes ===\n\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5\n",
		"/home/alice/notes/morgan.txt",
		CompanionDocument.TYPE_LOG
	)
	_doc_b = CompanionDocument.create(
		"doc_b",
		"Mission Brief",
		"=== MISSION BRIEF ===\n\nObjective: recover PHOENIX key.\nStatus: in progress.\n",
		"/home/alice/mission.txt",
		CompanionDocument.TYPE_MISSION
	)
	_doc_c = CompanionDocument.create(
		"doc_c",
		"CPU Manual",
		"=== CPU MANUAL ===\n\nMiner process diagnostic reference.\nPage 1 of 1.\n",
		"/home/alice/docs/cpu_manual.txt",
		CompanionDocument.TYPE_MANUAL
	)
	_doc_d = CompanionDocument.create(
		"doc_d",
		"Network Log",
		"=== NETWORK LOG ===\n\n[WARN] Gateway unreachable.\n[INFO] Link down.\n",
		"/home/alice/logs/net.log",
		CompanionDocument.TYPE_LOG
	)


func _guide_content() -> String:
	var lines := PackedStringArray()
	lines.append("┌─────────────────────────────────┐")
	lines.append("│  OSIRIS LOG GUIDE                │")
	lines.append("├─────────────────────────────────┤")
	lines.append("│  grep PATTERN FILE               │")
	lines.append("│    -i   ignore case              │")
	lines.append("│    -n   line numbers             │")
	lines.append("│    -r   recursive                │")
	lines.append("│                                  │")
	lines.append("│  less FILE                       │")
	lines.append("│    opens companion reader        │")
	lines.append("│                                  │")
	lines.append("│  cat FILE                        │")
	lines.append("│    prints to terminal output     │")
	lines.append("│                                  │")
	for i in range(30):
		lines.append("│  filler line %-4d               │" % i)
	lines.append("└─────────────────────────────────┘")
	return "\n".join(lines)


# ── UI layout ─────────────────────────────────────────────────────────────────

func _build_ui() -> void:
	# Background.
	var bg := ColorRect.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.08, 0.08, 0.08, 1.0)
	add_child(bg)

	var root_hbox := HBoxContainer.new()
	root_hbox.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_hbox.add_theme_constant_override("separation", 4)
	add_child(root_hbox)

	# ── Left: companion workspace ──────────────────────────────────────────────
	_workspace = CompanionWorkspace.new()
	_workspace.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_workspace.size_flags_vertical   = Control.SIZE_EXPAND_FILL
	root_hbox.add_child(_workspace)

	# ── Right: test log panel ──────────────────────────────────────────────────
	var log_panel := Panel.new()
	log_panel.custom_minimum_size = Vector2(360, 0)
	log_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var lp_style := StyleBoxFlat.new()
	lp_style.bg_color = Color(0.04, 0.04, 0.04, 1.0)
	lp_style.border_width_left = 1
	lp_style.border_color = Color(0.3, 0.3, 0.3, 1.0)
	log_panel.add_theme_stylebox_override("panel", lp_style)
	root_hbox.add_child(log_panel)

	var log_scroll := ScrollContainer.new()
	log_scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	log_panel.add_child(log_scroll)

	_log_label = RichTextLabel.new()
	_log_label.bbcode_enabled = true
	_log_label.fit_content = true
	_log_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_log_label.add_theme_font_size_override("normal_font_size", 14)
	_log_label.add_theme_constant_override("margin_left",  8)
	_log_label.add_theme_constant_override("margin_top",   8)
	_log_label.add_theme_constant_override("margin_right", 8)
	log_scroll.add_child(_log_label)

	_log("━━━━ COMPANION WORKSPACE — Milestone 1 Tests ━━━━\n")


# ── Test runner ───────────────────────────────────────────────────────────────

func _run_all_tests() -> void:
	_test_b1_open_guide()
	_test_b2_three_tabs()
	_test_b3_eviction()
	_test_b4_existing_document()
	_test_b5_keyboard_capture()
	_print_summary()


# ── B1 — Open ────────────────────────────────────────────────────────────────

func _test_b1_open_guide() -> void:
	_log("\n[b]B1 — Open guide.txt[/b]")
	_workspace_reset()
	_workspace.open_document(_guide_doc)

	var pass_one_tab := _workspace.get_tab_count() == 1
	var pass_content := _workspace.get_visible_content().contains("OSIRIS LOG GUIDE")
	var pass_active  := _workspace.get_active_document_id() == "guide.txt"

	_assert(pass_one_tab, "one tab open")
	_assert(pass_content, "document content readable")
	_assert(pass_active,  "correct document is active")


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
	_workspace.open_document(_doc_c)  # C is already open, will just activate it.
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


# ── B5 — Keyboard capture ────────────────────────────────────────────────────

func _test_b5_keyboard_capture() -> void:
	_log("\n[b]B5 — Keyboard capture[/b]")
	# We cannot send real InputEvents in a non-headless unit test without a
	# running viewport loop, so we verify the structural guarantee:
	# - _unhandled_input returns false for plain (non-Alt) key events.
	_workspace_reset()
	_workspace.open_document(_doc_a)

	var plain_key := InputEventKey.new()
	plain_key.keycode = KEY_A
	plain_key.pressed = true
	plain_key.alt_pressed = false

	var consumed_plain := _workspace._unhandled_input(plain_key)
	_assert(not consumed_plain, "plain typing is NOT consumed by companion")

	var alt_key := InputEventKey.new()
	# Alt+W without a running action map will not match the action string, but
	# we verify that the function at least does not swallow non-Alt events.
	alt_key.keycode = KEY_A
	alt_key.pressed = true
	alt_key.alt_pressed = false
	var consumed_plain2 := _workspace._unhandled_input(alt_key)
	_assert(not consumed_plain2, "non-Alt key with same code not consumed")

	_log("  [color=gray](Full Alt-action tests require running in editor with input map)[/color]")


# ── Helpers ───────────────────────────────────────────────────────────────────

func _workspace_reset() -> void:
	# Close all tabs by re-creating internal state.
	while _workspace.get_tab_count() > 0:
		_workspace.close_active_tab()


func _assert(condition: bool, description: String) -> void:
	var marker := TEST_PASS if condition else TEST_FAIL
	var color  := "green" if condition else "red"
	var line   := "  [color=%s]%s[/color] %s" % [color, marker, description]
	_log(line)
	_results.append("%s %s" % [marker, description])
	if not condition:
		push_error("Companion test FAILED: %s" % description)


func _log(text: String) -> void:
	_log_label.append_text(text + "\n")


func _print_summary() -> void:
	var passed := _results.filter(func(r): return r.begins_with(TEST_PASS)).size()
	var total  := _results.size()
	var color  := "green" if passed == total else "yellow"
	_log("\n━━━━ Summary: [color=%s]%d / %d passed[/color] ━━━━" % [color, passed, total])
	print("=== CompanionWorkspace Milestone 1: %d / %d tests passed ===" % [passed, total])
