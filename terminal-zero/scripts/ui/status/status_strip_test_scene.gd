## StatusStripTestScene
## Standalone acceptance-test scene for the Status Strip milestone.
##
## Owned by: Status Strip Agent
## This scene is NEVER instanced in main_ui.tscn — it is a self-contained
## harness used to validate milestone C1–C4.
##
## ── What this scene tests ─────────────────────────────────────────────────────
##
##   C1 — Six slots always present.
##   C2 — No-data state for a specific subsystem while others have data.
##   C3 — Severity colors: NORMAL, WARNING, ERROR visible simultaneously.
##   C4 — Compact labels activate when the window/strip is resized narrow.
##
## ── Controls ──────────────────────────────────────────────────────────────────
##
##   The scene cycles through preset datasets every few seconds so a human
##   reviewer can observe all states without interaction.
##   Pressing Space manually advances the dataset.
##
class_name StatusStripTestScene
extends Control

# ── Scene-graph references ────────────────────────────────────────────────────

var _strip: StatusStrip
var _info_label: Label
var _dataset_index: int = 0

# ── Fake datasets ─────────────────────────────────────────────────────────────

## _DATASETS is an Array of {label, statuses} dictionaries.
## Each entry represents one test scenario.
var _DATASETS: Array = []

const CYCLE_SECONDS := 4.0


func _ready() -> void:
	_build_datasets()
	_build_ui()
	_apply_dataset(_dataset_index)
	# Auto-cycle timer.
	var t := Timer.new()
	t.wait_time = CYCLE_SECONDS
	t.autostart = true
	t.timeout.connect(_auto_advance)
	add_child(t)


func _build_datasets() -> void:
	# ── Dataset 0: C1 baseline — all six slots, all no-data ───────────────────
	var d0_statuses := SubsystemStatus.make_initial_set()
	_DATASETS.append({
		"label": "C1 — Six slots / all NO DATA (game-start state)",
		"statuses": d0_statuses,
	})

	# ── Dataset 1: C3 — mixed severities ─────────────────────────────────────
	var d1: Array[SubsystemStatus] = []
	d1.append(_make("BUFFER",  "Buffer",          "BUF",   "12K",  "[LOW]",     SubsystemStatus.SEV_WARNING, true))
	d1.append(_make("SHELL",   "Shell Profile",   "SHELL", "",     "[MIN]",     SubsystemStatus.SEV_INFO,    true))
	d1.append(_make("LOGS",    "Logs",            "LOG",   "",     "[WARN]",    SubsystemStatus.SEV_WARNING, true))
	d1.append(_make("CPU",     "CPU / Miner",     "CPU",   "91%",  "[HIGH]",    SubsystemStatus.SEV_ERROR,   true))
	d1.append(_make("NETWORK", "Network Link",    "NET",   "",     "[DOWN]",    SubsystemStatus.SEV_ERROR,   true))
	d1.append(_make("GATEWAY", "Cluster Gateway", "GATE",  "",     "[NO DATA]", SubsystemStatus.SEV_UNKNOWN, false))
	_DATASETS.append({
		"label": "C3 — Mixed severities: WARNING / INFO / ERROR / UNKNOWN",
		"statuses": d1,
	})

	# ── Dataset 2: C2 — CPU no-data, others have data ─────────────────────────
	var d2: Array[SubsystemStatus] = []
	d2.append(_make("BUFFER",  "Buffer",          "BUF",   "8K",   "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d2.append(_make("SHELL",   "Shell Profile",   "SHELL", "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d2.append(_make("LOGS",    "Logs",            "LOG",   "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d2.append(SubsystemStatus.make_no_data(&"CPU", "CPU / Miner", "CPU"))  # C2: no data
	d2.append(_make("NETWORK", "Network Link",    "NET",   "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d2.append(_make("GATEWAY", "Cluster Gateway", "GATE",  "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	_DATASETS.append({
		"label": "C2 — CPU data_available=false; identity retained; [NO DATA] shown",
		"statuses": d2,
	})

	# ── Dataset 3: C3 — all NORMAL (healthy OSIRIS) ───────────────────────────
	var d3: Array[SubsystemStatus] = []
	d3.append(_make("BUFFER",  "Buffer",          "BUF",   "32K",  "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d3.append(_make("SHELL",   "Shell Profile",   "SHELL", "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d3.append(_make("LOGS",    "Logs",            "LOG",   "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d3.append(_make("CPU",     "CPU / Miner",     "CPU",   "14%",  "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d3.append(_make("NETWORK", "Network Link",    "NET",   "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	d3.append(_make("GATEWAY", "Cluster Gateway", "GATE",  "",     "[OK]",      SubsystemStatus.SEV_NORMAL,  true))
	_DATASETS.append({
		"label": "C3 — All NORMAL (fully-repaired OSIRIS)",
		"statuses": d3,
	})

	# ── Dataset 4: C3 — all ERROR (damaged OSIRIS) ────────────────────────────
	var d4: Array[SubsystemStatus] = []
	d4.append(_make("BUFFER",  "Buffer",          "BUF",   "",     "[FAULT]",   SubsystemStatus.SEV_ERROR,   true))
	d4.append(_make("SHELL",   "Shell Profile",   "SHELL", "",     "[FAULT]",   SubsystemStatus.SEV_ERROR,   true))
	d4.append(_make("LOGS",    "Logs",            "LOG",   "",     "[FAULT]",   SubsystemStatus.SEV_ERROR,   true))
	d4.append(_make("CPU",     "CPU / Miner",     "CPU",   "---",  "[FAULT]",   SubsystemStatus.SEV_ERROR,   true))
	d4.append(_make("NETWORK", "Network Link",    "NET",   "",     "[FAULT]",   SubsystemStatus.SEV_ERROR,   true))
	d4.append(_make("GATEWAY", "Cluster Gateway", "GATE",  "",     "[FAULT]",   SubsystemStatus.SEV_ERROR,   true))
	_DATASETS.append({
		"label": "C3 — All ERROR (critical OSIRIS degradation)",
		"statuses": d4,
	})


func _build_ui() -> void:
	# Root fills viewport.
	layout_mode = 3
	anchors_preset = 15
	anchor_right = 1.0
	anchor_bottom = 1.0

	var root_vbox := VBoxContainer.new()
	root_vbox.layout_mode = 1
	root_vbox.anchors_preset = 15
	root_vbox.anchor_right = 1.0
	root_vbox.anchor_bottom = 1.0
	add_child(root_vbox)

	# ── Top area — info labels ────────────────────────────────────────────────
	var top_area := VBoxContainer.new()
	top_area.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root_vbox.add_child(top_area)

	var title := Label.new()
	title.text = "TERMINAL ZERO — Status Strip Acceptance Tests"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	top_area.add_child(title)

	var hint := Label.new()
	hint.text = "Press [Space] to advance dataset manually. Auto-cycles every %ds." % int(CYCLE_SECONDS)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.modulate = Color(0.6, 0.6, 0.6)
	top_area.add_child(hint)

	var note_c4 := Label.new()
	note_c4.text = "C4 — Resize this window narrower than 900 px to trigger compact labels."
	note_c4.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note_c4.modulate = Color(0.6, 0.75, 0.6)
	top_area.add_child(note_c4)

	_info_label = Label.new()
	_info_label.text = ""
	_info_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_info_label.modulate = Color(0.9, 0.85, 0.2)
	top_area.add_child(_info_label)

	# ── Bottom — the actual StatusStrip ──────────────────────────────────────
	_strip = StatusStrip.new()
	root_vbox.add_child(_strip)


# ── Dataset cycling ───────────────────────────────────────────────────────────

func _apply_dataset(index: int) -> void:
	var dataset: Dictionary = _DATASETS[index]
	_strip.update_statuses(dataset["statuses"])
	_info_label.text = "Dataset %d / %d — %s" % [
		index + 1,
		_DATASETS.size(),
		dataset["label"],
	]


func _auto_advance() -> void:
	_dataset_index = (_dataset_index + 1) % _DATASETS.size()
	_apply_dataset(_dataset_index)


func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE:
			_auto_advance()
			get_viewport().set_input_as_handled()


# ── Helper ────────────────────────────────────────────────────────────────────

func _make(
		p_id: String,
		p_label: String,
		p_short: String,
		p_raw: String,
		p_state: String,
		p_sev: StringName,
		p_data: bool
) -> SubsystemStatus:
	var s := SubsystemStatus.new()
	s.id               = StringName(p_id)
	s.label            = p_label
	s.short_label      = p_short
	s.raw_value        = p_raw
	s.interpreted_state = p_state
	s.severity         = p_sev
	s.data_available   = p_data
	s.activity_state   = &"IDLE"
	return s
