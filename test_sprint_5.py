# test_sprint_5.py
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
import json
from terminal_zero import (
    build_default_vfs,
    VirtualFilesystem,
    TerminalState,
    EventBus,
    Event,
    CommandContext,
    cmd_sync,
    save_game_state,
    load_game_state,
    register_autosave_handler
)

def run_tests():
    save_file = "test_savegame.json"
    if os.path.exists(save_file):
        os.remove(save_file)

    # 1. Setup mutated state
    root = build_default_vfs()
    vfs = VirtualFilesystem(root)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["var", "log"])
    state.unlocked_ergonomics["history"] = True
    state.system_flags["BUFFER_REPAIRED"] = True
    
    # Mutate a file in VFS
    node, _ = vfs.get_node([], "/home/alice/notes/sysadmin_notes.txt")
    if node:
        node.content = "MUTATED CONTENT FOR PERSISTENCE TEST"

    # 2. Test manual save and reload
    save_game_state(state, save_file)
    assert os.path.exists(save_file), "Save file was not created on disk"

    loaded_state = load_game_state(save_file, bus)
    assert loaded_state is not None, "Failed to deserialize saved state"
    assert loaded_state.cwd_str == "/var/log", f"CWD mismatch: {loaded_state.cwd_str}"
    assert loaded_state.unlocked_ergonomics["history"] is True, "Ergonomics unlock not persisted"
    assert loaded_state.system_flags["BUFFER_REPAIRED"] is True, "System flags not persisted"
    
    loaded_node, _ = loaded_state.vfs.get_node([], "/home/alice/notes/sysadmin_notes.txt")
    if node:
        assert loaded_node.content == "MUTATED CONTENT FOR PERSISTENCE TEST", "VFS node content mutation not persisted"

    # 3. Test diegetic sync command
    ctx = CommandContext(vfs, state, bus)
    res_sync = cmd_sync(ctx, [])
    assert res_sync.exit_code == 0, f"cmd_sync failed: {res_sync.stderr}"
    assert os.path.exists("savegame.json"), "savegame.json not written by sync"

    # 4. Test autosave observer
    register_autosave_handler(bus, lambda: state)
    state.system_flags["BASHRC_RESTORED"] = True
    bus.publish(Event("flag_changed", {"flag": "BASHRC_RESTORED", "value": True}))
    
    with open("savegame.json", "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["system_flags"]["BASHRC_RESTORED"] is True, "Autosave failed on flag_changed event"

    # Cleanup test artifacts
    if os.path.exists(save_file): os.remove(save_file)
    if os.path.exists("savegame.json"): os.remove("savegame.json")

    print("✅ All Sprint 5 Acceptance Tests Passed.")

if __name__ == "__main__":
    run_tests()
