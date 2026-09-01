# test_sprint_2.py
from terminal_zero import (
    build_default_vfs,
    VirtualFilesystem,
    TerminalState,
    EventBus,
    CommandContext,
    VFSCompleter,
    build_key_bindings,
    cmd_tree
)
from prompt_toolkit.document import Document

def run_tests():
    root = build_default_vfs()
    vfs = VirtualFilesystem(root)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["home", "alice"])
    ctx = CommandContext(vfs, state, bus)

    # 1. Autocomplete locked verification
    completer = VFSCompleter(lambda: ctx)
    doc = Document("re")
    completions = list(completer.get_completions(doc, None))
    assert len(completions) == 0, "Autocomplete yielded results while locked"

    # 2. Autocomplete unlocked verification
    state.unlocked_ergonomics["autocomplete"] = True
    doc = Document("read")
    completions = list(completer.get_completions(doc, None))
    assert any(c.text == "readme.txt" for c in completions), "Failed to autocomplete 'readme.txt'"

    # 3. Keybindings registration verification
    kb = build_key_bindings(lambda: ctx)
    assert kb is not None, "KeyBindings instance failed creation"

    print("[PASS] All Sprint 2 Acceptance Tests Passed.")

if __name__ == "__main__":
    run_tests()
