## TerminalBackendAdapter
## Abstract interface between the Godot UI and the Terminal Zero simulation.
##
## Owned by: Lead / Foundation
## Contract version: 1.0
##
## ── Purpose ───────────────────────────────────────────────────────────────────
##
## The UI should depend only on this adapter, never on simulation internals.
## The simulation is currently a Python process; this stub defines the API
## that will be implemented when GDExtension or subprocess bridging is ready.
##
## TerminalView calls the methods below.
## The adapter emits the signals below when the simulation responds.
##
## ── Integration note ─────────────────────────────────────────────────────────
##
## Parallel agents: do NOT subclass or modify this file.
## Create a concrete implementation in scripts/ui/ (integration-owner task).
##
class_name TerminalBackendAdapter
extends Node

# ── Outgoing signals (simulation → UI) ───────────────────────────────────────

## Emitted when the simulation produces output for the terminal.
## @param chunks  Array[TerminalChunk]
signal output_emitted(chunks: Array)

## Emitted when the current command has finished executing.
signal command_finished()

## Emitted when the shell prompt string changes (e.g. cwd changes).
## @param prompt  String  e.g. "alice@osiris:~/logs$ "
signal prompt_changed(prompt: String)

## Emitted when shell capabilities change (unlock events).
## @param capabilities  ShellCapabilities
signal shell_capabilities_changed(capabilities: ShellCapabilities)

## Emitted when a tab-completion response is ready.
## @param result  Array[String]  sorted list of candidates
signal completion_result_received(result: Array)

## Emitted when the simulation wants to open a document in the companion reader.
## @param document  CompanionDocument
signal document_requested(document: CompanionDocument)

## Emitted when one or more subsystem telemetry readings change.
## @param statuses  Array[SubsystemStatus]
signal telemetry_changed(statuses: Array)


# ── Incoming calls (UI → simulation) ─────────────────────────────────────────

## Submit a command string for execution by the simulation.
## The simulation will emit output_emitted / command_finished in response.
func execute_command(command: String) -> void:
	push_warning("TerminalBackendAdapter.execute_command() not implemented — command: %s" % command)


## Request completion candidates for the given partial input.
## The simulation responds via completion_result_received.
func request_completion(partial_input: String, cursor_index: int) -> void:
	push_warning(
		"TerminalBackendAdapter.request_completion() not implemented — partial: '%s' cursor: %d"
		% [partial_input, cursor_index]
	)


## Signal the simulation that the user pressed Ctrl+C.
## Only meaningful when ShellCapabilities.interrupt is true.
func request_interrupt() -> void:
	push_warning("TerminalBackendAdapter.request_interrupt() not implemented")


## Return the current shell prompt string synchronously.
## Used during initialisation before the first prompt_changed signal.
func get_prompt() -> String:
	return "guest@osiris:~$ "
