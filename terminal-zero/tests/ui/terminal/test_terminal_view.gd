## TestTerminalView
## Standalone test scene for the Terminal Core agent.
##
## Convention: every parallel agent creates a test scene in their tests/ folder
## that can be launched directly from the Godot editor (F6 on the scene file).
##
## Required: the test scene must run without main_ui.tscn or any other
## parallel agent's scene. It connects a stub adapter directly.
##
## Naming convention:
##   tests/ui/terminal/test_terminal_view.tscn
##   tests/ui/companion/test_companion_workspace.tscn
##   tests/ui/status/test_status_strip.tscn
##   tests/ui/effects/test_effects_layer.tscn
##
## This is an empty GDScript placeholder. The Terminal Agent replaces it.
extends Control

func _ready() -> void:
	print("[TestTerminalView] Standalone test scene loaded — Terminal Agent should replace this.")
