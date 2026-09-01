# test_sprint_1.py
from terminal_zero import (
    build_default_vfs,
    VirtualFilesystem,
    TerminalState,
    EventBus,
    cmd_tree,
)

def run_tests():
    # 1. Setup Environment
    root_node = build_default_vfs()
    vfs = VirtualFilesystem(root_node)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["home", "alice"])

    # 2. Verify VFS Path & Node Resolution
    bashrc, _ = vfs.get_node([], "/home/alice/.bashrc")
    assert bashrc is not None, "Failed to resolve /home/alice/.bashrc"
    assert bashrc.type == "file" and bashrc.is_file(), "Expected .bashrc to be a file"
    assert bashrc.permissions == "644", f"Expected 644, got {bashrc.permissions}"
    assert bashrc.owner == "alice", f"Expected owner 'alice', got {bashrc.owner}"

    tree_bin, _ = vfs.get_node([], "/opt/phoenix/recovery/tree")
    assert tree_bin is not None, "Failed to resolve /opt/phoenix/recovery/tree"
    assert tree_bin.type == "file" and tree_bin.is_file(), "Expected tree binary to be a file"
    assert tree_bin.permissions == "755", f"Expected 755, got {tree_bin.permissions}"

    # 3. Verify Process Table & System Flags
    pids = [p.pid for p in state.process_table]
    assert pids == [1, 104, 210], f"Process table mismatch: {pids}"
    assert not any(state.system_flags.values()), "All system flags must initialize to False"
    assert not any(state.unlocked_ergonomics.values()), "All ergonomics must initialize to False"

    # 4. Verify Diegetic Tree Execution
    class MockContext:
        def __init__(self, virtual_fs, terminal_st, event_bus):
            self.vfs = virtual_fs
            self.state = terminal_st
            self.bus = event_bus

        def result_factory(self, stdout="", stderr="", exit_code=0):
            return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}

    ctx = MockContext(vfs, state, bus)
    res = cmd_tree(ctx, [])
    assert res["exit_code"] == 0, f"cmd_tree failed execution: {res.get('stderr')}"
    assert "/home/alice" in res["stdout"], "CWD not at top of tree output"
    assert "notes" in res["stdout"], "Child folder missing from tree output"

    print("[PASS] All Sprint 1 Acceptance Tests Passed.")

if __name__ == "__main__":
    run_tests()