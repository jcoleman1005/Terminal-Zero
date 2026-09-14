## SubsystemStatus
## A single snapshot of one of the six OSIRIS telemetry subsystems.
##
## Owned by: Lead / Foundation (read-only for parallel agents)
## Contract version: 1.0
class_name SubsystemStatus
extends RefCounted

## ── Subsystem ID constants ────────────────────────────────────────────────────
const ID_BUFFER  := &"BUFFER"
const ID_SHELL   := &"SHELL"
const ID_LOGS    := &"LOGS"
const ID_CPU     := &"CPU"
const ID_NETWORK := &"NETWORK"
const ID_GATEWAY := &"GATEWAY"

## Ordered list used by StatusStrip to preserve slot positions.
const ORDERED_IDS: Array[StringName] = [
	&"BUFFER", &"SHELL", &"LOGS", &"CPU", &"NETWORK", &"GATEWAY"
]

## ── Severity constants ────────────────────────────────────────────────────────
const SEV_NORMAL  := &"NORMAL"
const SEV_INFO    := &"INFO"
const SEV_WARNING := &"WARNING"
const SEV_ERROR   := &"ERROR"
const SEV_UNKNOWN := &"UNKNOWN"

## ── Fields ───────────────────────────────────────────────────────────────────

## One of the ID_* constants.
var id: StringName = &""

## Long display name (e.g. "Cluster Gateway").
var label: String = ""

## Short display name for compact strip (e.g. "GATE").
var short_label: String = ""

## Raw value string, may be empty when data_available is false.
var raw_value: String = ""

## Human-readable state token, e.g. "[OK]", "[WARN]", "[NO DATA]".
var interpreted_state: String = "[NO DATA]"

## One of the SEV_* constants.
var severity: StringName = SEV_UNKNOWN

## Whether telemetry data is currently readable for this subsystem.
var data_available: bool = false

## Optional activity state token, e.g. "IDLE", "ACTIVE", "FAULT".
var activity_state: StringName = &"IDLE"


## Returns a pre-filled SubsystemStatus for a slot with no data yet.
static func make_no_data(p_id: StringName, p_label: String, p_short: String) -> SubsystemStatus:
	var s := SubsystemStatus.new()
	s.id = p_id
	s.label = p_label
	s.short_label = p_short
	s.data_available = false
	s.interpreted_state = "[NO DATA]"
	s.severity = SEV_UNKNOWN
	return s


## Builds the default set of six degraded subsystem statuses.
## This represents OSIRIS at game start.
static func make_initial_set() -> Array[SubsystemStatus]:
	return [
		make_no_data(ID_BUFFER,  "Buffer",          "BUF"),
		make_no_data(ID_SHELL,   "Shell Profile",   "SHELL"),
		make_no_data(ID_LOGS,    "Logs",            "LOG"),
		make_no_data(ID_CPU,     "CPU / Miner",     "CPU"),
		make_no_data(ID_NETWORK, "Network Link",    "NET"),
		make_no_data(ID_GATEWAY, "Cluster Gateway", "GATE"),
	]
