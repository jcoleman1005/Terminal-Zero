# test_sprint_7_final.py
import io
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from terminal_zero import (
    build_default_vfs,
    VirtualFilesystem,
    VFSNode,
    TerminalState,
    EventBus,
    Event,
    CommandContext,
    TerminalShell,
    PipelineEngine,
    DebriefManager,
    COMMAND_TABLE,
    cmd_cat,
    cmd_head,
    cmd_tail,
    cmd_grep,
    cmd_find,
    cmd_chmod,
    cmd_man,
    cmd_decrypt,
    cmd_ps,
    cmd_kill,
    cmd_ip,
    cmd_ss,
    cmd_ping,
    cmd_sync,
    cmd_repair_buffer,
    cmd_phoenix_daemon,
    cmd_phoenix_ctl,
    save_game_state,
    load_game_state,
    build_key_bindings,
    VFSCompleter,
    get_todo_content,
)


def run_tests():
    print("=== STARTING TERMINAL ZERO V3 FINAL ACCEPTANCE TEST SUITE ===")

    # Setup baseline test environment
    root = build_default_vfs()
    vfs = VirtualFilesystem(root)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["home", "alice"])
    ctx = CommandContext(vfs, state, bus)
    shell = TerminalShell(ctx, COMMAND_TABLE)

    # Verify initial dynamic TODO.txt scratchpad
    todo_node, _ = vfs.get_node([], "/home/alice/TODO.txt")
    assert todo_node is not None
    assert todo_node.content == get_todo_content(state.system_flags)
    assert "[ ] 0. Terminal line buffer desynced" in todo_node.content

    # Verify initial sanitized socket state (only sshd on port 22, port 8080 offline)
    assert len(state.listening_sockets) == 1
    assert state.listening_sockets[0]["local"] == "0.0.0.0:22"
    assert not any(s.get("local") == "127.0.0.1:8080" for s in state.listening_sockets)

    # -------------------------------------------------------------
    # 1. Module 1: Pipeline Execution Engine (|) & Redirection (>, >>) & Write Hooks
    # -------------------------------------------------------------
    print("Testing Module 1: Pipeline Engine & Redirection & Write Hooks...")

    # Multi-stage pipe: cat -> grep -> head
    res_multi = shell.execute_command_line("cat /var/log/syslog | grep kernel | head -n 1")
    assert res_multi.exit_code == 0, f"Multi-stage pipeline failed: {res_multi.stderr}"
    assert "Linux version" in res_multi.stdout, f"Unexpected stdout: {res_multi.stdout}"

    # Quoted pipe character preservation
    res_quoted = shell.execute_command_line("echo 'alpha | beta' | grep 'alpha | beta'")
    assert res_quoted.exit_code == 0
    assert "alpha | beta" in res_quoted.stdout

    # Pipeline failure aborts subsequent stages
    res_abort = shell.execute_command_line("cat /nonexistent/file.txt | grep foo | head -n 1")
    assert res_abort.exit_code == 1
    assert "No such file or directory" in res_abort.stderr
    assert res_abort.stdout == ""

    # Redirection Overwrite (>)
    res_redir = shell.execute_command_line("head -n 2 /var/log/auth.log > /home/alice/auth_summary.txt")
    assert res_redir.exit_code == 0
    node, _ = vfs.get_node([], "/home/alice/auth_summary.txt")
    assert node is not None and node.is_file(), "File was not created via redirection >"

    # Redirection Append (>>)
    res_append = shell.execute_command_line("echo 'APPENDED_LINE' >> /home/alice/auth_summary.txt")
    assert res_append.exit_code == 0
    assert "APPENDED_LINE" in node.content

    # Stream Redirection Write Hook: writing to ~/.bashrc triggers BASHRC_RESTORED
    assert not state.system_flags["BASHRC_RESTORED"]
    res_bashrc_restore = shell.execute_command_line("cat /opt/backup/profiles/alice.bashrc > /home/alice/.bashrc")
    assert res_bashrc_restore.exit_code == 0
    assert state.system_flags["BASHRC_RESTORED"] is True
    assert state.unlocked_ergonomics["autocomplete"] is True
    assert state.unlocked_ergonomics["tab_completion"] is True

    # Redirection into non-existent parent directory fails
    res_bad_parent = shell.execute_command_line("echo 'test' > /nonexistent/dir/file.txt")
    assert res_bad_parent.exit_code == 1
    assert "No such file or directory" in res_bad_parent.stderr

    # Redirection into read-only / locked directory fails
    alice_node, _ = vfs.get_node([], "/home/alice")
    if alice_node:
        alice_node.children["locked_dir"] = VFSNode(type="dir", permissions="000")
    res_locked_redir = shell.execute_command_line("echo 'test' > /home/alice/locked_dir/test.txt")
    assert res_locked_redir.exit_code == 1
    assert "Permission denied" in res_locked_redir.stderr

    # -------------------------------------------------------------
    # 2. Module 2: Diegetic prompt_toolkit Ergonomic Interceptors
    # -------------------------------------------------------------
    print("Testing Module 2: Diegetic Ergonomics & Key Interceptors...")

    # Verify initial ergonomic locks (reset for test isolation)
    state.unlocked_ergonomics["history_arrows"] = False
    state.unlocked_ergonomics["history"] = False
    state.unlocked_ergonomics["tab_completion"] = False
    state.unlocked_ergonomics["autocomplete"] = False
    state.unlocked_ergonomics["sigint_trap"] = False
    state.unlocked_ergonomics["sigint"] = False

    # Mock prompt_toolkit keybinding interaction for locked alerts
    class DummyBuffer:
        def __init__(self):
            self.reset_called = False
        def auto_up(self): pass
        def auto_down(self): pass
        def start_completion(self): pass
        def reset(self): self.reset_called = True

    class DummyApp:
        def __init__(self):
            self.output = self
            self.current_buffer = DummyBuffer()
        def flush(self): pass

    class DummyEvent:
        def __init__(self):
            self.app = DummyApp()

    kb = build_key_bindings(lambda: ctx)
    key_handlers = {}
    for binding in kb.bindings:
        k = binding.keys[0]
        k_str = k.value if hasattr(k, "value") else str(k)
        key_handlers[k_str] = binding.handler

    # Test locked Up arrow
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        key_handlers["up"](DummyEvent())
        out = sys.stdout.getvalue()
        assert "[HARDWARE ERROR]: Input ring buffer" in out, f"Unexpected: {out}"
    finally:
        sys.stdout = old_stdout

    # Test locked Tab key ('c-i' or 'tab')
    sys.stdout = io.StringIO()
    try:
        tab_handler = key_handlers.get("c-i") or key_handlers.get("tab")
        tab_handler(DummyEvent())
        out = sys.stdout.getvalue()
        assert "[DRIVER MISSING]: libreadline unit offline" in out, f"Unexpected: {out}"
    finally:
        sys.stdout = old_stdout

    # Test locked Ctrl+C key ('c-c')
    sys.stdout = io.StringIO()
    try:
        sig_handler = key_handlers.get("c-c")
        sig_handler(DummyEvent())
        out = sys.stdout.getvalue()
        assert "[SIGNAL FAULT]: Process signal traps unconfigured" in out, f"Unexpected: {out}"
    finally:
        sys.stdout = old_stdout

    # Trigger BUFFER_REPAIRED flag -> verifies automatic history unlock
    bus.publish(Event("flag_changed", {"flag": "BUFFER_REPAIRED", "value": True}))
    assert state.unlocked_ergonomics["history_arrows"] is True
    assert state.unlocked_ergonomics["history"] is True

    # Trigger BASHRC_RESTORED flag -> verifies automatic tab_completion unlock
    bus.publish(Event("flag_changed", {"flag": "BASHRC_RESTORED", "value": True}))
    assert state.unlocked_ergonomics["tab_completion"] is True
    assert state.unlocked_ergonomics["autocomplete"] is True

    # -------------------------------------------------------------
    # 3. Module 3: Automatic last_stderr Wrapper & decrypt Diagnostic
    # -------------------------------------------------------------
    print("Testing Module 3: last_stderr Integration & decrypt Diagnostic...")

    # Execute failing command and assert state.last_stderr populated
    res_err = shell.execute_command_line("cd /var/log/syslog")
    assert res_err.exit_code == 1
    assert "Not a directory" in state.last_stderr

    # Test decrypt diagnostics for 'Not a directory'
    res_dec = shell.execute_command_line("decrypt")
    assert "FAULT 0x1C - INVALID TRAVERSAL" in res_dec.stdout
    assert "Use 'cat'" in res_dec.stdout

    # Test decrypt diagnostics for 'Network is unreachable'
    shell.execute_command_line("ping -c 1 10.0.42.1")
    res_dec_net = shell.execute_command_line("apollo-diagnostics")
    assert "FAULT 0x3D - NETWORK OFFLINE" in res_dec_net.stdout
    assert "ip link set apollo0 up" in res_dec_net.stdout

    # Test decrypt diagnostics for 'Permission denied'
    shell.execute_command_line("/mnt/recovery/bin/apollo-net")
    res_dec_perm = shell.execute_command_line("decrypt")
    assert "FAULT 0x2E - ACCESS RESTRICTED" in res_dec_perm.stdout
    assert "chmod +x" in res_dec_perm.stdout

    # Test sanitized decrypt advisory for typo / 'command not found'
    shell.execute_command_line("sl")
    res_dec_typo = shell.execute_command_line("decrypt")
    assert "[DECRYPT ADVISORY]: The command entered does not exist." in res_dec_typo.stdout
    assert "Check spelling or type 'ls'" in res_dec_typo.stdout
    assert "Standard utilities: pwd, ls, cd, cat, man, sync." in res_dec_typo.stdout

    # -------------------------------------------------------------
    # 4. Module 4: Complete Workstation VFS Map & Milestones 0-7
    # -------------------------------------------------------------
    print("Testing Module 4: Workstation VFS Map & Hardened Milestone Progression...")

    # Verify softlock protection backups exist
    def_conf, _ = vfs.get_node([], "/etc/phoenix/phoenix.conf.default")
    assert def_conf is not None and def_conf.permissions == "644"
    bak_conf, _ = vfs.get_node([], "/opt/backup/phoenix.conf")
    assert bak_conf is not None and bak_conf.permissions == "644"

    # Check recovery partition permissions zeroed
    repair_bin, _ = vfs.get_node([], "/mnt/recovery/bin/repair_buffer")
    assert repair_bin is not None and repair_bin.permissions == "000"

    # Execution fails before chmod
    res_exec_fail = shell.execute_command_line("/mnt/recovery/bin/repair_buffer")
    assert res_exec_fail.exit_code == 126
    assert "Permission denied" in res_exec_fail.stderr

    # chmod +x elevates and triggers BUFFER_REPAIRED
    res_chmod = shell.execute_command_line("chmod +x /mnt/recovery/bin/repair_buffer")
    assert res_chmod.exit_code == 0
    assert repair_bin.permissions == "755"
    assert state.system_flags["BUFFER_REPAIRED"] is True

    # Execution now succeeds
    res_exec_ok = shell.execute_command_line("/mnt/recovery/bin/repair_buffer")
    assert res_exec_ok.exit_code == 0
    assert "Ring buffer synchronized" in res_exec_ok.stdout

    # Strict Process Signaling: Standard SIGTERM / kill 104 is trapped by sys_miner
    res_kill_sigterm = shell.execute_command_line("kill 104")
    assert res_kill_sigterm.exit_code == 0
    assert "Trapping signal and continuing execution" in res_kill_sigterm.stdout
    assert not state.system_flags["MALWARE_TERMINATED"]
    assert any(p.pid == 104 and p.status == "running" for p in state.process_table)

    # Terminate malware via strict kill -9 104 (SIGKILL)
    res_kill = shell.execute_command_line("kill -9 104")
    assert res_kill.exit_code == 0
    assert "forcefully killed by SIGKILL" in res_kill.stdout
    assert state.system_flags["MALWARE_TERMINATED"] is True
    assert not any(p.pid == 104 for p in state.process_table)

    # Precondition check: phoenix_daemon fails if network is DOWN
    res_phoenix_nonet = shell.execute_command_line("phoenix_daemon start")
    assert res_phoenix_nonet.exit_code == 1
    assert "Network gateway unreachable" in res_phoenix_nonet.stderr

    # Bring network up via ip link set apollo0 up
    res_ip = shell.execute_command_line("ip link set apollo0 up")
    assert res_ip.exit_code == 0
    assert state.system_flags["NETWORK_ONLINE"] is True

    # Precondition check: phoenix_daemon fails if permissions on /etc/phoenix/phoenix.conf are 0600 (not 0644)
    res_phoenix_noperm = shell.execute_command_line("phoenix_daemon start")
    assert res_phoenix_noperm.exit_code == 1
    assert "Insecure permissions on /etc/phoenix/phoenix.conf" in res_phoenix_noperm.stderr

    # Test decrypt diagnostics on insecure permissions
    res_dec_phoenix = shell.execute_command_line("decrypt")
    assert "FAULT 0x2E - ACCESS RESTRICTED" in res_dec_phoenix.stdout

    # Fix permissions to 644
    res_chmod_conf = shell.execute_command_line("chmod 644 /etc/phoenix/phoenix.conf")
    assert res_chmod_conf.exit_code == 0

    # Precondition check: phoenix_daemon fails if auth key is missing
    res_phoenix_nokey = shell.execute_command_line("phoenix_daemon start")
    assert res_phoenix_nokey.exit_code == 1
    assert "Authentication token missing" in res_phoenix_nokey.stderr

    # Test decrypt diagnostics on missing token
    res_dec_key = shell.execute_command_line("decrypt")
    assert "FAULT 0x5B - AUTHENTICATION REQUIRED" in res_dec_key.stdout

    # Append key to config via redirection >>
    res_append_key = shell.execute_command_line("cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf")
    assert res_append_key.exit_code == 0

    # Launch phoenix daemon with full authorization
    res_phoenix = shell.execute_command_line("phoenix_daemon start")
    assert res_phoenix.exit_code == 0
    assert "Emergency Restoration Protocol activated" in res_phoenix.stdout
    assert state.system_flags["PHOENIX_ONLINE"] is True

    # Verify socket port 8080 was dynamically bound upon daemon start
    res_ss_8080 = shell.execute_command_line("ss -tulpn | grep 8080")
    assert res_ss_8080.exit_code == 0
    assert "127.0.0.1:8080" in res_ss_8080.stdout
    assert "phoenix_daemon" in res_ss_8080.stdout

    # Also test phoenix_ctl alias
    res_phoenix_ctl = shell.execute_command_line("phoenix_ctl start")
    assert res_phoenix_ctl.exit_code == 0

    # -------------------------------------------------------------
    # 5. Module 5: Simulated Live Log Streaming (tail -f)
    # -------------------------------------------------------------
    print("Testing Module 5: Simulated Live Log Streaming (tail -f)...")

    res_tail_f = shell.execute_command_line("tail -f -n 5 /var/log/syslog")
    assert "[LOG STREAM ACTIVE - Press Ctrl+C to abort]" in res_tail_f.stdout
    assert "Interface apollo0 link state UP" in res_tail_f.stdout
    assert "sys_miner) terminated" in res_tail_f.stdout
    assert "Listening for restoration heartbeat on 127.0.0.1:8080" in res_tail_f.stdout

    # -------------------------------------------------------------
    # 6. Full Serialization & Roundtrip
    # -------------------------------------------------------------
    print("Testing Persistence & State Hydration...")

    save_path = "test_sprint_7_save.json"
    if os.path.exists(save_path):
        os.remove(save_path)

    save_game_state(state, save_path)
    assert os.path.exists(save_path)

    loaded_st = load_game_state(save_path, bus)
    assert loaded_st is not None
    assert loaded_st.system_flags["BUFFER_REPAIRED"] is True
    assert loaded_st.system_flags["BASHRC_RESTORED"] is True
    assert loaded_st.system_flags["MALWARE_TERMINATED"] is True
    assert loaded_st.system_flags["NETWORK_ONLINE"] is True
    assert loaded_st.system_flags["PHOENIX_ONLINE"] is True
    assert loaded_st.unlocked_ergonomics["history_arrows"] is True
    assert loaded_st.unlocked_ergonomics["tab_completion"] is True
    assert loaded_st.network_interfaces["apollo0"]["state"] == "UP"
    assert any(s.get("local") == "127.0.0.1:8080" for s in loaded_st.listening_sockets)

    loaded_todo, _ = loaded_st.vfs.get_node([], "/home/alice/TODO.txt")
    assert loaded_todo is not None
    assert loaded_todo.content == get_todo_content(loaded_st.system_flags)
    assert "[x] 0. Terminal line buffer desynced" in loaded_todo.content
    assert "[x] 5. Restore PHOENIX daemon" in loaded_todo.content

    if os.path.exists(save_path):
        os.remove(save_path)

    print("🎉 [ALL FINAL PARITY TESTS PASSED - 100% FEATURE PARITY ACHIEVED]")


if __name__ == "__main__":
    run_tests()
