## ShellCapabilities
## Tracks which shell ergonomics have been unlocked during play.
##
## Owned by: Lead / Foundation (read-only for parallel agents)
## Contract version: 1.0
##
## The simulation backend drives this state; the UI reads it.
## Do not modify capability fields from UI scripts.
class_name ShellCapabilities
extends RefCounted

## True once the player repairs the buffer — enables history navigation.
var command_history: bool = false

## True once the player restores .bashrc — enables tab completion.
var tab_completion: bool = false

## True once SIGINT is restored — enables Ctrl+C interrupt.
var interrupt: bool = false

## True once the companion module is repaired — enables split workspace.
var companion_workspace: bool = false


static func create_default() -> ShellCapabilities:
	return ShellCapabilities.new()


func duplicate_caps() -> ShellCapabilities:
	var c := ShellCapabilities.new()
	c.command_history     = command_history
	c.tab_completion      = tab_completion
	c.interrupt           = interrupt
	c.companion_workspace = companion_workspace
	return c
