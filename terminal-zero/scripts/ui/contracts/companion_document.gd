## CompanionDocument
## A document loaded into the CompanionWorkspace reader.
##
## Owned by: Lead / Foundation (read-only for parallel agents)
## Contract version: 1.0
##
## The backend emits these; the CompanionWorkspace displays them.
## CompanionWorkspace does not read the filesystem directly.
class_name CompanionDocument
extends RefCounted

## ── Document type constants ───────────────────────────────────────────────────
const TYPE_GUIDE    := &"GUIDE"
const TYPE_MISSION  := &"MISSION"
const TYPE_LOG      := &"LOG"
const TYPE_MANUAL   := &"MANUAL"
const TYPE_DOSSIER  := &"DOSSIER"
const TYPE_GENERIC  := &"GENERIC"

## ── Fields ───────────────────────────────────────────────────────────────────

## Unique stable identifier used for tab deduplication.
var document_id: String = ""

## Display name shown in the companion tab header.
var title: String = ""

## Full text content of the document (plain text, may include box-drawing chars).
var content: String = ""

## Virtual filesystem path this document originated from (informational).
var source_path: String = ""

## One of the TYPE_* constants.
var document_type: StringName = TYPE_GENERIC


static func create(
	p_id: String,
	p_title: String,
	p_content: String,
	p_source: String = "",
	p_type: StringName = TYPE_GENERIC
) -> CompanionDocument:
	var doc := CompanionDocument.new()
	doc.document_id   = p_id
	doc.title         = p_title
	doc.content       = p_content
	doc.source_path   = p_source
	doc.document_type = p_type
	return doc
