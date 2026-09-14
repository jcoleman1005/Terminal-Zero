## TestTerminalHarness
## Standalone test scene for TerminalView — Milestone 1.
##
## Owned by: Terminal Agent
## Tests: tests/ui/terminal/
##
## Drives TerminalView with StubBackendAdapter.
## Runs without main_ui.tscn.
##
## Acceptance tests covered:
##   A1 — Submit: command moves to scrollback, output appears, fresh prompt returns.
##   A2 — Scrollback: mouse-wheel navigates older output.
##   A3 — New output: NEW OUTPUT indicator while scrolled up.
##   A4 — History gate: Up/Down capability-gated.
##   A5 — Completion: unique vs ambiguous candidates.
##
## Interactive controls injected into the top of the scene:
##   [Run A1-A3 Load] — fires enough fake lines to overflow, then fires delayed output
##   [Unlock History]  — grants command_history capability
##   [Unlock Completion] — grants tab_completion capability
##
class_name TestTerminalHarness
extends Control

## The stub adapter acts as the fake backend.
var _stub: StubBackendAdapter

@onready var _terminal: TerminalView = $Split/TerminalView
@onready var _btn_load:       Button = $ToolBar/BtnLoad
@onready var _btn_history:    Button = $ToolBar/BtnHistory
@onready var _btn_completion: Button = $ToolBar/BtnCompletion
@onready var _btn_interrupt:  Button = $ToolBar/BtnInterrupt
@onready var _status_label:   Label  = $ToolBar/StatusLabel


func _ready() -> void:
	# Create and wire stub.
	_stub = StubBackendAdapter.new()
	add_child(_stub)

	_stub.output_emitted.connect(_terminal.append_output)
	_stub.command_finished.connect(_terminal.on_command_finished)
	_stub.prompt_changed.connect(_terminal.set_prompt)
	_stub.shell_capabilities_changed.connect(_terminal.apply_capabilities)
	_stub.completion_result_received.connect(_terminal.show_completion)

	_terminal.command_submitted.connect(_stub.execute_command)
	_terminal.completion_requested.connect(_stub.request_completion)
	_terminal.interrupt_requested.connect(_stub.request_interrupt)

	# Button wiring.
	_btn_load.pressed.connect(_run_overflow_test)
	_btn_history.pressed.connect(_unlock_history)
	_btn_completion.pressed.connect(_unlock_completion)
	_btn_interrupt.pressed.connect(_unlock_interrupt)

	_status_label.text = "All capabilities OFF"


# ── Button actions ────────────────────────────────────────────────────────────

## A2/A3 — flood the terminal with fake lines, then emit output after 2 s.
func _run_overflow_test() -> void:
	_status_label.text = "Flooding scrollback…"
	for i in range(60):
		var chunks: Array = [
			TerminalChunk.create(
				"Line %02d: the quick brown fox jumps over the lazy dog\n" % i,
				TerminalChunk.ROLE_DEFAULT
			)
		]
		_stub.output_emitted.emit(chunks)
	_status_label.text = "Scroll UP, then wait 2 s for new output (A3)"
	await get_tree().create_timer(2.0).timeout
	var late: Array = [
		TerminalChunk.create("← NEW OUTPUT arrived while scrolled up\n", TerminalChunk.ROLE_INFO)
	]
	_stub.output_emitted.emit(late)
	_stub.command_finished.emit()


## A4 — grant command_history.
func _unlock_history() -> void:
	_stub.unlock_capability("command_history")
	_status_label.text = "History UNLOCKED — try Up/Down arrows"


## A5 — grant tab_completion.
func _unlock_completion() -> void:
	_stub.unlock_capability("tab_completion")
	_status_label.text = "Completion UNLOCKED — type 'doc' then Tab"


## A4/interrupt — grant interrupt.
func _unlock_interrupt() -> void:
	_stub.unlock_capability("interrupt")
	_status_label.text = "Interrupt UNLOCKED — try Ctrl+C"
