# test_sprint_4.py
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
    cmd_find,
    cmd_pwd,
    cmd_cd,
    cmd_ls,
    cmd_chmod,
    cmd_man,
    cmd_decrypt,
    MAN_PAGES,
)

def run_tests():
    # Setup test environment
    root = build_default_vfs()
    vfs = VirtualFilesystem(root)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["home", "alice"])
    ctx = CommandContext(vfs, state, bus)

    # -------------------------------------------------------------
    # 1. Test pwd
    # -------------------------------------------------------------
    res = cmd_pwd(ctx, [])
    assert res.stdout == "/home/alice\n", f"pwd mismatch: {res.stdout}"

    # -------------------------------------------------------------
    # 2. Test cd
    # -------------------------------------------------------------
    # cd notes
    res = cmd_cd(ctx, ["notes"])
    assert res.exit_code == 0
    assert state.current_path == ["home", "alice", "notes"]

    # cd ..
    res = cmd_cd(ctx, [".."])
    assert res.exit_code == 0
    assert state.current_path == ["home", "alice"]

    # cd to root /
    res = cmd_cd(ctx, ["/"])
    assert res.exit_code == 0
    assert state.current_path == []

    # cd with no args (defaults to ~ -> /home/alice)
    res = cmd_cd(ctx, [])
    assert res.exit_code == 0
    assert state.current_path == ["home", "alice"]

    # cd non-existent
    res = cmd_cd(ctx, ["nonexistent_dir"])
    assert res.exit_code == 1
    assert "No such file or directory" in res.stderr

    # cd into a file
    res = cmd_cd(ctx, ["readme.txt"])
    assert res.exit_code == 1
    assert "Not a directory" in res.stderr

    # cd too many args
    res = cmd_cd(ctx, ["dir1", "dir2"])
    assert res.exit_code == 1
    assert "too many arguments" in res.stderr

    # -------------------------------------------------------------
    # 3. Test ls
    # -------------------------------------------------------------
    # Standard ls in /home/alice
    res = cmd_ls(ctx, [])
    assert "notes" in res.stdout
    assert "readme.txt" in res.stdout
    assert ".bashrc" not in res.stdout  # hidden without -a

    # ls -a
    res = cmd_ls(ctx, ["-a"])
    assert ".bashrc" in res.stdout
    assert "." in res.stdout
    assert ".." in res.stdout

    # ls -l
    res = cmd_ls(ctx, ["-l"])
    assert "alice" in res.stdout

    # ls nonexistent
    res = cmd_ls(ctx, ["missing_folder"])
    assert res.exit_code == 2
    assert "No such file or directory" in res.stderr

    # -------------------------------------------------------------
    # 4. Test chmod
    # -------------------------------------------------------------
    # Missing operand
    res = cmd_chmod(ctx, ["755"])
    assert res.exit_code == 1
    assert "missing operand" in res.stderr

    # Numeric mode
    res = cmd_chmod(ctx, ["777", "readme.txt"])
    assert res.exit_code == 0
    node, _ = vfs.get_node(state.current_path, "readme.txt")
    assert node.permissions == "777"

    # Symbolic mode (+x, -x)
    res = cmd_chmod(ctx, ["+x", "readme.txt"])
    assert res.exit_code == 0
    assert node.permissions == "755"

    res = cmd_chmod(ctx, ["-x", "readme.txt"])
    assert res.exit_code == 0
    assert node.permissions == "644"

    # Invalid mode
    res = cmd_chmod(ctx, ["invalid", "readme.txt"])
    assert res.exit_code == 1
    assert "invalid mode" in res.stderr

    # -------------------------------------------------------------
    # 5. Test man & MAN_PAGES
    # -------------------------------------------------------------
    # No args
    res = cmd_man(ctx, [])
    assert res.exit_code == 1
    assert "What manual page do you want?" in res.stderr

    # Valid man lookup
    for cmd_key in ["ls", "cd", "cat", "head", "tail", "grep", "find", "chmod", "decrypt"]:
        assert cmd_key in MAN_PAGES, f"MAN_PAGES missing {cmd_key}"
        res = cmd_man(ctx, [cmd_key])
        assert res.exit_code == 0
        assert cmd_key in res.stdout

    # Nonexistent man
    res = cmd_man(ctx, ["foobar"])
    assert res.exit_code == 1
    assert "No manual entry for foobar" in res.stderr

    # -------------------------------------------------------------
    # 6. Test decrypt (Diegetic Advisory Engine)
    # -------------------------------------------------------------
    # Empty stderr
    ctx.state.last_stderr = ""
    res = cmd_decrypt(ctx, [])
    assert "No recent hardware or kernel fault recorded in buffer." in res.stdout

    # 0x1A - PATH NOT FOUND
    ctx.state.last_stderr = "cat: foo.txt: No such file or directory\n"
    res = cmd_decrypt(ctx, [])
    assert "FAULT 0x1A - PATH NOT FOUND" in res.stdout

    # 0x1B - ILLEGAL NODE TYPE
    ctx.state.last_stderr = "cat: notes: Is a directory\n"
    res = cmd_decrypt(ctx, [])
    assert "FAULT 0x1B - ILLEGAL NODE TYPE" in res.stdout

    # 0x1C - INVALID TRAVERSAL
    ctx.state.last_stderr = "bash: cd: readme.txt: Not a directory\n"
    res = cmd_decrypt(ctx, [])
    assert "FAULT 0x1C - INVALID TRAVERSAL" in res.stdout

    # 0x2E - ACCESS RESTRICTED
    ctx.state.last_stderr = "bash: ./script.sh: Permission denied\n"
    res = cmd_decrypt(ctx, [])
    assert "FAULT 0x2E - ACCESS RESTRICTED" in res.stdout

    # 0x4F - BINARY UNREGISTERED
    ctx.state.last_stderr = "bash: help: command not found\n"
    res = cmd_decrypt(ctx, [])
    assert "FAULT 0x4F - BINARY UNREGISTERED" in res.stdout

    # 0x05 - ARITY MISMATCH
    ctx.state.last_stderr = "cat: missing file operand\n"
    res = cmd_decrypt(ctx, [])
    assert "FAULT 0x05 - ARITY MISMATCH" in res.stdout

    # -------------------------------------------------------------
    # 7. Shell REPL Execution & Event Bus Verification
    # -------------------------------------------------------------
    commands = {
        "tree": cmd_tree,
        "cat": cmd_cat,
        "head": cmd_head,
        "tail": cmd_tail,
        "grep": cmd_grep,
        "find": cmd_find,
        "pwd": cmd_pwd,
        "cd": cmd_cd,
        "ls": cmd_ls,
        "chmod": cmd_chmod,
        "man": cmd_man,
        "decrypt": cmd_decrypt,
    }
    shell = TerminalShell(ctx, commands)

    events_captured = []
    bus.subscribe(lambda ev: events_captured.append(ev.type))

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    shell.execute_line("pwd")
    shell.execute_line("ls")
    shell.execute_line("man cd")
    shell.execute_line("chmod 755 readme.txt")
    out = sys.stdout.getvalue()
    sys.stdout = old_stdout

    assert "/home/alice" in out
    assert "readme.txt" in out
    assert "change the working directory" in out
    assert "command_executed" in events_captured

    print("[PASS] All Sprint 4 Acceptance Tests Passed.")

if __name__ == "__main__":
    run_tests()
