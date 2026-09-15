## TerminalChunk
## A single semantic unit of terminal output.
##
## Owned by: Lead / Foundation (read-only for parallel agents)
## Contract version: 1.0
class_name TerminalChunk
extends RefCounted

## Allowed style roles — do not add new roles without a contract-change request.
const ROLE_DEFAULT    := &"DEFAULT"
const ROLE_SUCCESS    := &"SUCCESS"
const ROLE_INFO       := &"INFO"
const ROLE_WARNING    := &"WARNING"
const ROLE_ERROR      := &"ERROR"
const ROLE_DIRECTORY  := &"DIRECTORY"
const ROLE_EXECUTABLE := &"EXECUTABLE"
const ROLE_SPECIAL    := &"SPECIAL"
const ROLE_DIM        := &"DIM"

## The text content of this chunk.
var text: String = ""

## One of the ROLE_* constants above.
var style_role: StringName = ROLE_DEFAULT


static func create(p_text: String, p_role: StringName = ROLE_DEFAULT) -> TerminalChunk:
	var chunk := TerminalChunk.new()
	chunk.text = p_text
	chunk.style_role = p_role
	return chunk
