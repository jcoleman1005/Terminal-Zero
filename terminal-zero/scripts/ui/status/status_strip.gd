## StatusStrip
## Persistent bottom bar showing six OSIRIS subsystem telemetry slots.
##
## Owned by: Status Strip Agent
## Contract version: 1.0
##
## ── Responsibilities ──────────────────────────────────────────────────────────
##
##   - Maintain exactly six StatusSlot children in ORDERED_IDS order.
##   - Expose update_statuses(Array[SubsystemStatus]) as the single inbound API.
##   - Detect strip width changes and toggle compact mode on all slots.
##   - Never compute telemetry values.
##
## ── What this script does NOT do ─────────────────────────────────────────────
##
##   - Parse game state.
##   - Modify shared contracts.
##   - Trigger EffectsLayer.
##
class_name StatusStrip
extends PanelContainer

# ── Layout ────────────────────────────────────────────────────────────────────

## Width below which slots switch to short_label.
## Must match StatusSlot.COMPACT_WIDTH_THRESHOLD_PX or be set here centrally.
const COMPACT_WIDTH_THRESHOLD_PX: float = 900.0

## Separator glyph between slots.
const SEPARATOR_GLYPH := " │ "

# ── Internal state ────────────────────────────────────────────────────────────

# Maps StringName id → StatusSlot node.
var _slots: Dictionary = {}

# Maps StringName id → most-recent SubsystemStatus.
var _statuses: Dictionary = {}

# Cached compact state to avoid unnecessary refreshes.
var _compact: bool = false

# ── Child layout references ───────────────────────────────────────────────────

var _slot_row: HBoxContainer


func _ready() -> void:
	_build_layout()
	_seed_initial_statuses()


func _build_layout() -> void:
	# Outer PanelContainer provides a flat background to distinguish the strip.
	custom_minimum_size = Vector2(0, 24)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL

	_slot_row = HBoxContainer.new()
	_slot_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_slot_row.alignment = BoxContainer.ALIGNMENT_CENTER
	add_child(_slot_row)

	# Build the six slots in canonical order, separated by dividers.
	for i in SubsystemStatus.ORDERED_IDS.size():
		var sys_id: StringName = SubsystemStatus.ORDERED_IDS[i]

		var slot := StatusSlot.new()
		slot.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_slot_row.add_child(slot)
		_slots[sys_id] = slot

		# Add separator between slots (not after the last one).
		if i < SubsystemStatus.ORDERED_IDS.size() - 1:
			var sep := Label.new()
			sep.text = SEPARATOR_GLYPH
			sep.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			sep.modulate = Color(0.4, 0.4, 0.4)
			_slot_row.add_child(sep)


func _seed_initial_statuses() -> void:
	# Start every slot in the no-data state — matches OSIRIS boot condition.
	var initial := SubsystemStatus.make_initial_set()
	update_statuses(initial)


# ── Public API ────────────────────────────────────────────────────────────────

## Receive a batch of SubsystemStatus snapshots.
## Only the subsystems present in the array are updated; others are unchanged.
func update_statuses(statuses: Array) -> void:
	for status in statuses:
		if status is SubsystemStatus and _slots.has(status.id):
			_statuses[status.id] = status
			(_slots[status.id] as StatusSlot).apply_status(status)


## Force-update a single subsystem slot.
func update_status(status: SubsystemStatus) -> void:
	update_statuses([status])


# ── Responsive behavior ───────────────────────────────────────────────────────

func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_check_compact()


func _check_compact() -> void:
	var now_compact := size.x < COMPACT_WIDTH_THRESHOLD_PX
	if now_compact == _compact:
		return
	_compact = now_compact
	for slot in _slots.values():
		(slot as StatusSlot).set_compact(_compact)
