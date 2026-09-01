# test_sprint_6.py
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
import json
import io

from terminal_zero import (
    build_default_vfs,
    VirtualFilesystem,
    TerminalState,
    EventBus,
    Event,
    CommandContext,
    TerminalShell,
    DebriefManager,
    cmd_ps,
    cmd_kill,
    cmd_ip,
    cmd_ss,
    cmd_ping,
    cmd_tail,
    cmd_cat,
    cmd_grep,
    cmd_man,
    cmd_chmod,
    save_game_state,
    load_game_state
)


def run_tests():
    # Setup test environment
    root = build_default_vfs()
    vfs = VirtualFilesystem(root)
    bus = EventBus()
    state = TerminalState(vfs, bus, ["home", "alice"])
    ctx = CommandContext(vfs, state, bus)

    captured_debriefs = []
    def capture_writer(text: str):
        captured_debriefs.append(text)

    debrief_mgr = DebriefManager(bus, output_writer=capture_writer)

    command_table = {
        "ps": cmd_ps,
        "kill": cmd_kill,
        "ip": cmd_ip,
        "ss": cmd_ss,
        "ping": cmd_ping,
        "tail": cmd_tail,
        "cat": cmd_cat,
        "grep": cmd_grep,
        "man": cmd_man,
        "chmod": cmd_chmod,
    }

    shell = TerminalShell(ctx, command_table)

    # -------------------------------------------------------------
    # 1. Test Module 1: Process Control (ps, kill)
    # -------------------------------------------------------------
    ps_res = cmd_ps(ctx, ["aux"])
    assert "USER" in ps_res.stdout and "PID" in ps_res.stdout, "ps output missing headers"
    assert "sys_miner" in ps_res.stdout or "miner" in ps_res.stdout, "ps missing rogue sys_miner process"
    assert "/sbin/init" in ps_res.stdout or "systemd" in ps_res.stdout, "ps missing init/systemd"

    # Kill invalid PID
    kill_inv = cmd_kill(ctx, ["99999"])
    assert kill_inv.exit_code == 1, "kill nonexistent PID should fail"
    assert "No such process" in kill_inv.stderr

    # Kill malware process with -9
    kill_res = cmd_kill(ctx, ["-9", "104"])
    assert kill_res.exit_code == 0, f"kill -9 104 failed: {kill_res.stderr}"
    assert state.system_flags["MALWARE_TERMINATED"] is True, "MALWARE_TERMINATED flag not set"
    assert any("sys_miner" not in proc.name for proc in state.process_table), "sys_miner still in process table"
    assert any("Process Administration & Signals" in d for d in captured_debriefs), "DebriefManager failed to emit MALWARE_TERMINATED modal"

    # -------------------------------------------------------------
    # 2. Test Module 2: Network Operations (ip, ss, ping)
    # -------------------------------------------------------------
    # Test ip addr
    ip_addr_res = cmd_ip(ctx, ["addr"])
    assert "127.0.0.1/8" in ip_addr_res.stdout, "ip addr missing loopback"
    assert "10.0.42.15/24" in ip_addr_res.stdout, "ip addr missing apollo0"

    # Test ping when network is DOWN
    ping_down = cmd_ping(ctx, ["-c", "2", "10.0.42.1"])
    assert ping_down.exit_code == 2, "ping should fail when apollo0 is DOWN"
    assert "Network is unreachable" in ping_down.stderr

    # Test ip link set apollo0 up
    ip_up_res = cmd_ip(ctx, ["link", "set", "apollo0", "up"])
    assert ip_up_res.exit_code == 0, f"ip link set failed: {ip_up_res.stderr}"
    assert state.network_interfaces["apollo0"]["state"] == "UP", "apollo0 state not updated to UP"
    assert state.system_flags["NETWORK_ONLINE"] is True, "NETWORK_ONLINE flag not set"
    assert any("Network Interface Management with 'ip'" in d for d in captured_debriefs), "DebriefManager failed to emit NETWORK_ONLINE modal"

    # Test ping when network is UP
    ping_up = cmd_ping(ctx, ["-c", "2", "10.0.42.1"])
    assert ping_up.exit_code == 0, f"ping failed: {ping_up.stderr}"
    assert "64 bytes from 10.0.42.1" in ping_up.stdout, "ping missing ICMP responses"
    assert "0% packet loss" in ping_up.stdout, "ping missing summary stats"

    # Test ss socket audit
    ss_res = cmd_ss(ctx, ["-tulpn"])
    assert "LISTEN" in ss_res.stdout, "ss missing listening sockets"
    assert "phoenix_daemon" in ss_res.stdout, "ss missing phoenix_daemon"
    assert "22" in ss_res.stdout, "ss missing sshd port 22"

    # -------------------------------------------------------------
    # 3. Test Module 3: Pipeline Execution Engine & tail -f
    # -------------------------------------------------------------
    # Test pipe execution in shell
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        shell.execute_line("ps aux | grep init")
        pipe_output = sys.stdout.getvalue()
        assert "init" in pipe_output, "ps aux | grep init failed"
    finally:
        sys.stdout = old_stdout

    # Test tail -f streaming simulation
    tail_f_res = cmd_tail(ctx, ["-f", "/var/log/syslog"])
    assert "[STREAM ACTIVE - Press Ctrl+C to exit]" in tail_f_res.stdout, "tail -f missing stream active indicator"
    assert "apollo0 link state change detected" in tail_f_res.stdout, "tail -f missing simulated log events"

    # -------------------------------------------------------------
    # 4. Test Module 4: Campaign World & VFS Hierarchy
    # -------------------------------------------------------------
    # Verify syslog, auth.log
    syslog_node, _ = vfs.get_node([], "/var/log/syslog")
    assert syslog_node is not None and "System Logging Service" in syslog_node.content, "/var/log/syslog missing"

    auth_node, _ = vfs.get_node([], "/var/log/auth.log")
    assert auth_node is not None and "192.168.1.105" in auth_node.content, "/var/log/auth.log missing"

    # Verify recovery partition binaries (permissions zeroed)
    rec_bin, _ = vfs.get_node([], "/mnt/recovery/bin/apollo-net")
    assert rec_bin is not None and rec_bin.permissions == "000", "apollo-net permissions should be 000"

    # Verify chmod on recovery binary
    cmd_chmod(ctx, ["755", "/mnt/recovery/bin/apollo-net"])
    assert rec_bin.permissions == "755", "chmod failed to elevate apollo-net permissions"

    # Verify phoenix config and daemon
    ph_conf, _ = vfs.get_node([], "/opt/phoenix/phoenix.conf")
    assert ph_conf is not None and "RECOVERY_KEY" in ph_conf.content, "phoenix.conf missing"

    # Verify bash_history and TODO.txt
    hist_node, _ = vfs.get_node([], "/home/alice/.bash_history")
    assert hist_node is not None and "ps aux | grep miner" in hist_node.content, ".bash_history missing"

    todo_node, _ = vfs.get_node([], "/home/alice/TODO.txt")
    assert todo_node is not None and "OPERATOR RECOVERY SCRATCHPAD" in todo_node.content, "TODO.txt missing"

    # -------------------------------------------------------------
    # 5. Test Module 5: Man Pages
    # -------------------------------------------------------------
    for cmd_name in ["ps", "kill", "ip", "ss", "ping"]:
        man_res = cmd_man(ctx, [cmd_name])
        assert man_res.exit_code == 0, f"man {cmd_name} failed"
        assert cmd_name.upper() in man_res.stdout or cmd_name in man_res.stdout, f"man {cmd_name} missing name section"

    # -------------------------------------------------------------
    # 6. Test Persistence & Hydration of Network and Processes
    # -------------------------------------------------------------
    save_file = "test_sprint_6_save.json"
    if os.path.exists(save_file):
        os.remove(save_file)

    save_game_state(state, save_file)
    assert os.path.exists(save_file), "Save file was not created on disk"

    loaded_state = load_game_state(save_file, bus)
    assert loaded_state is not None, "Failed to load saved state"
    assert loaded_state.network_interfaces["apollo0"]["state"] == "UP", "apollo0 state not hydrated properly"
    assert loaded_state.system_flags["MALWARE_TERMINATED"] is True, "MALWARE_TERMINATED flag not hydrated"
    assert loaded_state.system_flags["NETWORK_ONLINE"] is True, "NETWORK_ONLINE flag not hydrated"
    assert any("sshd" in p.name for p in loaded_state.process_table), "Process table not hydrated"

    if os.path.exists(save_file):
        os.remove(save_file)

    print("✅ All Sprint 6 Acceptance Tests Passed.")


if __name__ == "__main__":
    run_tests()
