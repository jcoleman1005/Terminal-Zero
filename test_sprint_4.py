# test_sprint_4.py
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from terminal_zero import (
    build_default_vfs,
    VirtualFilesystem,
    TerminalState,
    EventBus,
    CommandContext,
    cmd_cd,
    cmd_ls,
    cmd_chmod,
    cmd_man,
    cmd_decrypt,
)

def run_tests():
    root = build_default_vfs()
    vfs = VirtualFilesystem(root)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["home", "alice"])
    ctx = CommandContext(vfs, state, bus)

    # 1. Verify POSIX Error & Decrypt Pipeline
    # Attempt to cd into a regular file
    cd_res = cmd_cd(ctx, ["readme.txt"])
    assert "Not a directory" in cd_res.stderr, "Expected 'Not a directory' stderr"
    state.last_stderr = cd_res.stderr

    # Execute decrypt on the trapped stderr
    dec_res = cmd_decrypt(ctx, [])
    assert "FAULT 0x1C - INVALID TRAVERSAL" in dec_res.stdout, "decrypt failed to map error"
    assert "Use 'cat'" in dec_res.stdout, "decrypt guidance missing"

    # 2. Verify cd traversal
    cmd_cd(ctx, ["/var/log"])
    assert state.cwd_str == "/var/log", f"Failed cd to /var/log: got {state.cwd_str}"
    
    cmd_cd(ctx, [".."])
    assert state.cwd_str == "/var", f"Failed cd ..: got {state.cwd_str}"

    # 3. Verify ls flags
    ls_res = cmd_ls(ctx, ["-a"])
    assert "." in ls_res.stdout and ".." in ls_res.stdout, "ls -a missing dot references"

    # 4. Verify chmod numeric & symbolic mutation
    test_node, _ = vfs.get_node([], "/home/alice/readme.txt")
    cmd_chmod(ctx, ["+x", "/home/alice/readme.txt"])
    assert test_node.permissions == "755", f"Symbolic +x failed: {test_node.permissions}"
    
    cmd_chmod(ctx, ["600", "/home/alice/readme.txt"])
    assert test_node.permissions == "600", f"Numeric 600 failed: {test_node.permissions}"

    # 5. Verify man utility
    man_res = cmd_man(ctx, ["grep"])
    assert "print lines that match patterns" in man_res.stdout, "man grep failed output"

    print("✅ All Sprint 4 Acceptance Tests Passed.")

if __name__ == "__main__":
    run_tests()
