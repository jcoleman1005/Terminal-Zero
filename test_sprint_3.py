# test_sprint_3.py
import io
import sys
from terminal_zero import (
    build_default_vfs,
    VirtualFilesystem,
    TerminalState,
    EventBus,
    CommandContext,
    TerminalShell,
    cmd_tree,
    cmd_cat,
    cmd_head,
    cmd_tail,
    cmd_grep,
    cmd_find
)

def run_tests():
    # Setup test environment
    root = build_default_vfs()
    vfs = VirtualFilesystem(root)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["home", "alice"])
    ctx = CommandContext(vfs, state, bus)

    # -------------------------------------------------------------
    # 1. Test cat
    # -------------------------------------------------------------
    res = cmd_cat(ctx, ["readme.txt"])
    assert "APOLLO WORKSTATION LOGON" in res.stdout, "cat failed to read file"

    # cat missing file
    res = cmd_cat(ctx, ["nonexistent.txt"])
    assert res.exit_code == 1
    assert "No such file or directory" in res.stderr

    # cat directory
    res = cmd_cat(ctx, ["notes"])
    assert res.exit_code == 1
    assert "Is a directory" in res.stderr

    # cat with stdin
    ctx.stdin = "hello stdin"
    res = cmd_cat(ctx, [])
    assert res.exit_code == 0
    assert res.stdout == "hello stdin"
    ctx.stdin = ""

    # -------------------------------------------------------------
    # 2. Test head / tail
    # -------------------------------------------------------------
    ctx_log = CommandContext(vfs, state, bus)
    res_head = cmd_head(ctx_log, ["-n", "1", "/var/log/system.log"])
    assert res_head.stdout.startswith("03:40:12"), f"head mismatch: {res_head.stdout}"
    
    res_tail = cmd_tail(ctx_log, ["-n", "1", "/var/log/system.log"])
    assert "phoenix-sync terminated" in res_tail.stdout, f"tail mismatch: {res_tail.stdout}"

    # head / tail from stdin
    ctx.stdin = "a\nb\nc\nd\ne\n"
    res = cmd_head(ctx, ["-n", "3"])
    assert res.exit_code == 0
    assert res.stdout == "a\nb\nc\n"
    ctx.stdin = ""

    ctx.stdin = "a\nb\nc\nd\ne\n"
    res = cmd_tail(ctx, ["-n", "2"])
    assert res.exit_code == 0
    assert res.stdout == "d\ne\n"
    ctx.stdin = ""

    # -------------------------------------------------------------
    # 3. Test grep (case-insensitive & recursive)
    # -------------------------------------------------------------
    res_grep = cmd_grep(ctx, ["-i", "apollo", "readme.txt"])
    assert "APOLLO WORKSTATION LOGON" in res_grep.stdout, "grep failed case-insensitive match"

    # Invert match & line number
    res = cmd_grep(ctx, ["-v", "-n", "APOLLO", "readme.txt"])
    assert res.exit_code == 0
    assert "2:[SYSTEM ADVISORY]:" in res.stdout

    # Grep recursive (-r)
    res = cmd_grep(ctx, ["-r", "link down", "/var/log"])
    assert res.exit_code == 0
    assert "system.log" in res.stdout
    assert "eth0 link down" in res.stdout

    # -------------------------------------------------------------
    # 4. Test find by name and type
    # -------------------------------------------------------------
    res_find = cmd_find(ctx, ["/opt", "-name", "*.sh", "-type", "f"])
    assert "recovery.sh" in res_find.stdout or "/opt" in res_find.stdout, "find failed pattern resolution"

    res_find_dir = cmd_find(ctx, ["/home/alice", "-type", "d"])
    assert res_find_dir.exit_code == 0
    assert "/home/alice/notes" in res_find_dir.stdout

    # -------------------------------------------------------------
    # 5. Test stdin pipeline compatibility
    # -------------------------------------------------------------
    ctx.stdin = "line1\nline2\nline3\nmatch_target\nline5\n"
    res_pipe_grep = cmd_grep(ctx, ["match_target"])
    assert res_pipe_grep.stdout.strip() == "match_target", "grep stdin matching failed"
    ctx.stdin = ""

    # -------------------------------------------------------------
    # 6. VirtualFilesystem write_file & walk
    # -------------------------------------------------------------
    success, err = vfs.write_file(state.current_path, "test.txt", "line 1\nline 2\nline 3\n")
    assert success, f"Failed write_file: {err}"
    
    node, _ = vfs.get_node(state.current_path, "test.txt")
    assert node is not None and node.content == "line 1\nline 2\nline 3\n"

    # Append
    success, err = vfs.write_file(state.current_path, "test.txt", "line 4\n", append=True)
    assert success
    assert node.content == "line 1\nline 2\nline 3\nline 4\n"

    # Walk test
    walk_results = vfs.walk(state.current_path, ".")
    walk_names = [name for _, _, name in walk_results]
    assert "test.txt" in walk_names
    assert "readme.txt" in walk_names

    # -------------------------------------------------------------
    # 7. TerminalShell Pipeline & Redirection Tests
    # -------------------------------------------------------------
    commands = {
        "tree": cmd_tree,
        "cat": cmd_cat,
        "head": cmd_head,
        "tail": cmd_tail,
        "grep": cmd_grep,
        "find": cmd_find,
    }
    shell = TerminalShell(ctx, commands)

    # Simple Pipe
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    shell.execute_line("cat readme.txt | grep APOLLO")
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    assert "APOLLO WORKSTATION LOGON" in output

    # Multi-stage Pipe
    sys.stdout = io.StringIO()
    shell.execute_line("cat test.txt | grep line | head -n 2")
    output = sys.stdout.getvalue()
    sys.stdout = old_stdout
    assert output == "line 1\nline 2\n"

    # Redirection Overwrite (>)
    shell.execute_line("head -n 2 readme.txt > /home/alice/snippet.txt")
    node, _ = vfs.get_node([], "/home/alice/snippet.txt")
    assert node is not None
    assert "APOLLO WORKSTATION LOGON" in node.content

    # Redirection Append (>>)
    shell.execute_line("tail -n 1 test.txt >> /home/alice/snippet.txt")
    node, _ = vfs.get_node([], "/home/alice/snippet.txt")
    assert "line 4\n" in node.content

    # Pipe into Redirection
    shell.execute_line("cat /var/log/system.log | grep kernel > /home/alice/kernel.log")
    node, _ = vfs.get_node([], "/home/alice/kernel.log")
    assert node is not None
    assert "eth0 link down" in node.content

    # Command Not Found in Pipeline
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()
    shell.execute_line("badcommand | grep foo")
    err_output = sys.stderr.getvalue()
    sys.stderr = old_stderr
    assert "command not found" in err_output

    print("[PASS] All Sprint 3 Acceptance Tests Passed.")

if __name__ == "__main__":
    run_tests()
