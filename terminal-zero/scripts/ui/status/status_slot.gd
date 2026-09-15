## StatusSlot
## Renders one of the six OSIRIS subsystem telemetry positions.
##
## Owned by: Status Strip Agent
## Contract version: 1.0
##
## ── Responsibilities ──────────────────────────────────────────────────────────
##
##   - Display label (long or compact), raw value, interpreted state, severity.
##   - Handle the no-data state gracefully.
##   - Switch to short_label when compact mode is active.
##   - Apply semantic color to the state token (never color alone — text carries
##     the same meaning).
##
## ── What this script does NOT do ─────────────────────────────────────────────
##
##   - Compute telemetry values.
##   - Read game state directly.
##   - Trigger effects or sounds.
##
class_name StatusSlot
extends HBoxContainer

# ── Color palette (ANSI-inspired semantic colors) ─────────────────────────────

const COLOR_NORMAL  := Color(0.2, 0.9,  0.2)   # green  — healthy
const COLOR_INFO    := Color(0.2, 0.85, 0.85)  # cyan   — informational
const COLOR_WARNING := Color(0.9, 0.85, 0.1)   # yellow — degraded / warning
const COLOR_ERROR   := Color(0.9, 0.2,  0.2)   # red    — fault
const COLOR_UNKNOWN := Color(0.55, 0.55, 0.55) # dim    — unavailable / unknown

# ── Minimum sizes for narrow-width behavior ───────────────────────────────────

## Strip pixel width below which compact labels activate.
const COMPACT_WIDTH_THRESHOLD_PX: float = 900.0

# ── Internal state ────────────────────────────────────────────────────────────

var _current_status: SubsystemStatus = null
var _compact: bool = false

# ── Child node references (built in _ready) ───────────────────────────────────

var _label_node: Label      # subsystem label or short_label
var _value_node: Label      # raw_value — hidden when empty / no data
var _state_node: Label      # interpreted_state token e.g. "[OK]"


func _ready() -> void:
	_build_nodes()


func _build_nodes() -> void:
	# Keep all children on a single baseline with minimal spacing.
	add_theme_constant_override("separation", 4)

	_label_node = _make_label("")
	_value_node = _make_label("")
	_state_node = _make_label("[NO DATA]")

	add_child(_label_node)
	add_child(_value_node)
	add_child(_state_node)


func _make_label(text: String) -> Label:
	var l := Label.new()
	l.text = text
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	# Prevent the slot from overflowing in narrow layouts.
	l.clip_text = true
	return l


# ── Public API ────────────────────────────────────────────────────────────────

## Apply a SubsystemStatus snapshot.  Calling this with null renders a blank
## placeholder (should not normally occur — prefer make_no_data()).
func apply_status(status: SubsystemStatus) -> void:
	_current_status = status
	_refresh()


## Switch between compact (short_label) and full (label) display.
func set_compact(compact: bool) -> void:
	if _compact == compact:
		return
	_compact = compact
	_refresh()


# ── Rendering ─────────────────────────────────────────────────────────────────

func _refresh() -> void:
	if _current_status == null:
		_label_node.text = "???"
		_value_node.text = ""
		_value_node.visible = false
		_state_node.text = "[NO DATA]"
		_state_node.modulate = COLOR_UNKNOWN
		return

	# Label — compact switches to short_label.
	_label_node.text = _current_status.short_label if _compact \
			else _current_status.label

	# Raw value — hidden when not available or empty.
	var show_value := _current_status.data_available \
			and _current_status.raw_value != ""
	_value_node.text = _current_status.raw_value if show_value else ""
	_value_node.visible = show_value

	# Interpreted state token.
	_state_node.text = _current_status.interpreted_state

	# Semantic color applied to the state token.
	# Text content also carries the meaning — color is enhancement only.
	_state_node.modulate = _severity_color(_current_status.severity)


func _severity_color(severity: StringName) -> Color:
	match severity:
		SubsystemStatus.SEV_NORMAL:
			return COLOR_NORMAL
		SubsystemStatus.SEV_INFO:
			return COLOR_INFO
		SubsystemStatus.SEV_WARNING:
			return COLOR_WARNING
		SubsystemStatus.SEV_ERROR:
			return COLOR_ERROR
		_:
			return COLOR_UNKNOWN
