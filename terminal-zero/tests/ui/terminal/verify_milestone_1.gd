extends SceneTree

func _init() -> void:
	print("[VERIFY] Starting Milestone 1 Automated Verification...")
	call_deferred("_run_tests")

func _run_tests() -> void:
	var test_scene: PackedScene = load("res://tests/ui/terminal/test_terminal_view.tscn")
	assert(test_scene != null, "Failed to load test_terminal_view.tscn")
	
	var root_node: Node = test_scene.instantiate()
	root.add_child(root_node)
	
	# Wait for ready and deferred initial states
	await process_frame
	await process_frame
	
	var tv: TerminalView = root_node.get_node("VBoxRoot/Split/TerminalView")
	assert(tv != null, "TerminalView node not found in scene tree")
	
	# 1. Verify prompt initialization
	var prompt_label: Label = tv.get_node("VBox/InputRow/PromptLabel")
	print("[VERIFY] Prompt label text: '", prompt_label.text, "'")
	assert(prompt_label.text == "alice@osiris:~$ ", "Expected alice@osiris:~$ prompt from stub")
	
	# 2. Test A1: Submit command (pwd)
	print("[VERIFY] Testing A1: Submit command...")
	var line_edit: LineEdit = tv.get_node("VBox/InputRow/CommandLineEdit")
	line_edit.text = "pwd"
	tv._on_text_submitted("pwd")
	
	await process_frame
	await process_frame
	
	var output_label: RichTextLabel = tv.get_node("VBox/ScrollContainer/OutputLabel")
	var text_content: String = output_label.get_parsed_text()
	print("[VERIFY] Output text after 'pwd':\n'", text_content, "' (text property was: '", output_label.text, "')")
	assert(text_content.contains("pwd"), "Output should contain submitted command")
	assert(text_content.contains("/home/alice"), "Output should contain stub output '/home/alice'")
	
	# 3. Test A4: History gate
	print("[VERIFY] Testing A4: History gate...")
	# History currently disabled
	var initial_text: String = line_edit.text
	tv._history_navigate(1)
	assert(line_edit.text == initial_text, "History navigation should be blocked when capability is false")
	
	# Enable history
	var caps := ShellCapabilities.create_default()
	caps.command_history = true
	tv.apply_capabilities(caps)
	
	tv._history_navigate(1)
	print("[VERIFY] LineEdit after history navigate up: '", line_edit.text, "'")
	assert(line_edit.text == "pwd", "History should recall 'pwd'")
	
	tv._history_navigate(-1)
	print("[VERIFY] LineEdit after history navigate down: '", line_edit.text, "'")
	assert(line_edit.text == "", "History navigate down should restore initial draft")
	
	# 4. Test A5: Tab completion
	print("[VERIFY] Testing A5: Tab completion...")
	caps.tab_completion = true
	tv.apply_capabilities(caps)
	
	# Unique completion
	line_edit.text = "doc"
	tv.show_completion(["documents"])
	print("[VERIFY] LineEdit after unique completion: '", line_edit.text, "'")
	assert(line_edit.text == "documents", "Expected line edit to complete to 'documents'")
	
	# Ambiguous completion
	line_edit.text = "l"
	tv.show_completion(["logs", "legacy"])
	text_content = output_label.get_parsed_text()
	print("[VERIFY] Output after ambiguous completion:\n", text_content)
	assert(text_content.contains("logs  legacy"), "Should print candidates into output")
	
	# 5. Test A3: New Output indicator on scroll
	print("[VERIFY] Testing A3: New Output indicator...")
	var new_output_bar: Label = tv.get_node("VBox/NewOutputBar")
	assert(!new_output_bar.visible, "New output bar should initially be invisible")
	
	# Simulate user scrolling up
	tv._at_bottom = false
	tv.append_output([TerminalChunk.create("background message\n", TerminalChunk.ROLE_INFO)])
	assert(new_output_bar.visible, "New output bar should become visible when scrolled up")
	
	# Simulate returning to bottom
	tv._scroll_to_bottom()
	await process_frame
	await process_frame
	assert(!new_output_bar.visible, "New output bar should hide when returning to bottom")
	
	# 6. Test Public API methods
	print("[VERIFY] Testing public API contract methods...")
	tv.grab_input_focus()
	tv.set_prompt("test@unit:~$ ")
	assert(prompt_label.text == "test@unit:~$ ", "set_prompt should update PromptLabel")
	
	tv.on_command_finished()
	assert(tv._busy == false, "_busy should be false after command finished")
	
	print("[VERIFY] ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
	quit(0)
