## StubBackendAdapter
## A minimal concrete implementation of TerminalBackendAdapter for test scenes.
##
## Owned by: Lead / Foundation
## Contract version: 1.0
##
## Parallel agents use this in their standalone test scenes to avoid needing
## a real simulation bridge. It emits fake output so UI can be tested in isolation.
##
## Usage in a test scene:
##   var stub := StubBackendAdapter.new()
##   add_child(stub)
##   stub.output_emitted.connect(terminal_view.append_output)
##   stub.prompt_changed.connect(terminal_view.set_prompt)
##   stub.fire_fake_boot_sequence()
##
class_name StubBackendAdapter
extends TerminalBackendAdapter

## Fake prompt used by the stub.
var _prompt: String = "alice@osiris:~$ "


func _ready() -> void:
	# Emit initial prompt on next frame so listeners have time to connect.
	call_deferred("_emit_initial_state")


func _emit_initial_state() -> void:
	prompt_changed.emit(_prompt)
	shell_capabilities_changed.emit(ShellCapabilities.create_default())
	telemetry_changed.emit(SubsystemStatus.make_initial_set())


# ── Overrides ─────────────────────────────────────────────────────────────────

func execute_command(command: String) -> void:
	var echo_chunks: Array = [
		TerminalChunk.create(_prompt + command + "\n", TerminalChunk.ROLE_DEFAULT)
	]
	output_emitted.emit(echo_chunks)

	# Produce simple fake output for common commands.
	var fake: Array = []
	match command.strip_edges().split(" ")[0]:
		"ls":
			fake = [TerminalChunk.create(
				"documents  logs  notes  recovery.sh\n",
				TerminalChunk.ROLE_DEFAULT
			)]
		"pwd":
			fake = [TerminalChunk.create("/home/alice\n", TerminalChunk.ROLE_DEFAULT)]
		"whoami":
			fake = [TerminalChunk.create("alice\n", TerminalChunk.ROLE_DEFAULT)]
		"help":
			fake = [TerminalChunk.create(
				"Available stub commands: ls, pwd, whoami, help\n",
				TerminalChunk.ROLE_INFO
			)]
		_:
			fake = [TerminalChunk.create(
				"bash: %s: command not found\n" % command.strip_edges().split(" ")[0],
				TerminalChunk.ROLE_ERROR
			)]

	output_emitted.emit(fake)
	command_finished.emit()


func request_completion(partial_input: String, _cursor_index: int) -> void:
	# Return a few fake completions for test purposes.
	var candidates: Array[String] = []
	for word in ["documents", "logs", "notes", "recovery.sh"]:
		if word.begins_with(partial_input.get_slice(" ", partial_input.get_slice_count(" ") - 1)):
			candidates.append(word)
	completion_result_received.emit(candidates)


func request_interrupt() -> void:
	var chunks: Array = [TerminalChunk.create("^C\n", TerminalChunk.ROLE_WARNING)]
	output_emitted.emit(chunks)
	command_finished.emit()


func get_prompt() -> String:
	return _prompt


# ── Test helpers ──────────────────────────────────────────────────────────────

## Simulate a document open event (e.g. player ran `less notes/morgan.txt`).
func fire_open_document(doc_id: String, title: String, content: String) -> void:
	var doc := CompanionDocument.create(doc_id, title, content, "/home/alice/notes/" + doc_id, CompanionDocument.TYPE_GUIDE)
	document_requested.emit(doc)


## Simulate a telemetry update.
func fire_telemetry_update(id: StringName, state: String, sev: StringName, value: String = "") -> void:
	var s := SubsystemStatus.new()
	s.id = id
	s.interpreted_state = state
	s.severity = sev
	s.raw_value = value
	s.data_available = value != ""
	telemetry_changed.emit([s])


## Grant a capability and emit the change signal.
func unlock_capability(cap_name: String) -> void:
	var caps := ShellCapabilities.create_default()
	match cap_name:
		"command_history":     caps.command_history = true
		"tab_completion":      caps.tab_completion = true
		"interrupt":           caps.interrupt = true
		"companion_workspace": caps.companion_workspace = true
	shell_capabilities_changed.emit(caps)
