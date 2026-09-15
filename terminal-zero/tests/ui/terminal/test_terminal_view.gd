## TestTerminalView
## Standalone test harness scene for the Terminal Core — Milestone 1.
##
## Owned by: Terminal Agent
## Tests: tests/ui/terminal/
##
## Runs without main_ui.tscn.
## Uses StubBackendAdapter to drive TerminalView in isolation.
##
## Acceptance tests covered (AGENT_TERMINAL.md):
##   A1 — Submit: type a command → scrollback committed, output appears, fresh prompt.
##   A2 — Scrollback: flood terminal, mouse-wheel through history.
##   A3 — New output: scroll up, trigger delayed output → NEW OUTPUT appears.
##   A4 — History gate: Up/Down capability-gated by ShellCapabilities.command_history.
##   A5 — Completion: unique candidate completes; ambiguous prints listing, no popup.
##
## Interactive controls:
##   [A2/A3: Flood] — sends 60 lines, then 2 s delayed line (tests A3 with scroll)
##   [A4: Unlock History]     — grants command_history capability
##   [A5: Unlock Completion]  — grants tab_completion capability
##   [Unlock Interrupt]       — grants interrupt capability (Ctrl+C)
##
extends Control

var _stub: StubBackendAdapter

@onready var _terminal: TerminalView = $VBoxRoot/Split/TerminalView
@onready var _btn_load:       Button = $VBoxRoot/ToolBar/BtnLoad
@onready var _btn_history:    Button = $VBoxRoot/ToolBar/BtnHistory
@onready var _btn_completion: Button = $VBoxRoot/ToolBar/BtnCompletion
@onready var _btn_interrupt:  Button = $VBoxRoot/ToolBar/BtnInterrupt
@onready var _status_label:   Label  = $VBoxRoot/ToolBar/StatusLabel


func _ready() -> void:
	_stub = StubBackendAdapter.new()
	add_child(_stub)

	# Wire backend → UI.
	_stub.output_emitted.connect(_terminal.append_output)
	_stub.command_finished.connect(_terminal.on_command_finished)
	_stub.prompt_changed.connect(_terminal.set_prompt)
	_stub.shell_capabilities_changed.connect(_terminal.apply_capabilities)
	_stub.completion_result_received.connect(_terminal.show_completion)

	# Wire UI → backend.
	_terminal.command_submitted.connect(_stub.execute_command)
	_terminal.completion_requested.connect(_stub.request_completion)
	_terminal.interrupt_requested.connect(_stub.request_interrupt)

	_btn_load.pressed.connect(_run_overflow_test)
	_btn_history.pressed.connect(_unlock_history)
	_btn_completion.pressed.connect(_unlock_completion)
	_btn_interrupt.pressed.connect(_unlock_interrupt)

	_status_label.text = "All capabilities OFF — type commands below"


## A2 / A3: flood with 60 lines, then emit a delayed line after 2 s.
func _run_overflow_test() -> void:
	_status_label.text = "Flooding scrollback… scroll UP before the 2 s timer fires (tests A3)"
	for i in range(60):
		_stub.output_emitted.emit([
			TerminalChunk.create(
				"Line %02d: sphinx of black quartz judge my vow\n" % i,
				TerminalChunk.ROLE_DEFAULT
			)
		])
	await get_tree().create_timer(2.0).timeout
	_stub.output_emitted.emit([
		TerminalChunk.create(
			"← NEW OUTPUT arrived while scrolled up — indicator should be visible\n",
			TerminalChunk.ROLE_INFO
		)
	])
	_stub.command_finished.emit()
	_status_label.text = "Flood complete. Scroll back down to dismiss NEW OUTPUT indicator."


func _unlock_history() -> void:
	_stub.unlock_capability("command_history")
	_status_label.text = "History UNLOCKED — submit several commands, then try Up/Down"


func _unlock_completion() -> void:
	_stub.unlock_capability("tab_completion")
	_status_label.text = "Completion UNLOCKED — type 'doc' then Tab (unique), or 'l' then Tab (ambiguous)"


func _unlock_interrupt() -> void:
	_stub.unlock_capability("interrupt")
	_status_label.text = "Interrupt UNLOCKED — press Ctrl+C"
