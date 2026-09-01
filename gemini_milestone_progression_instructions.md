# GEMINI PROMPT & TECHNICAL SPECIFICATION
## Implementation Instructions: Milestone Progression Engine (Milestones 0 – 7)

### System Overview & Context
You are tasked with extending the **Terminal Zero** Python prototype (`Prototype.txt`) to implement the full continuous Metroidvania campaign defined in **`Milestone Progression.md`** and **`TERMINAL ZERO GDD v2.md`**.

This document provides exact Python data structures, VFS initialization functions, event triggers, and state flag transition logic to construct the complete workstation map across all eight milestones (Milestones 0 through 7).

---

### Module 1: Comprehensive VFS Workstation Map (`build_default_vfs`)

Replace the existing `build_default_vfs()` function in `Prototype.txt` with a fully populated Filesystem Hierarchy Standard (FHS) tree containing all files, logs, configs, and permissions required for Milestones 0–7.

```python
def build_default_vfs() -> VFSNode:
    root = VFSNode(type="dir", permissions="755", owner="root")

    # Helper function to recursively construct path
    def add_node(path_str: str, node: VFSNode):
        parts = [p for p in path_str.strip("/").split("/") if p]
        curr = root
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                curr.children[part] = node
            else:
                if part not in curr.children:
                    curr.children[part] = VFSNode(type="dir", permissions="755", owner="root")
                curr = curr.children[part]

    # Directories
    for d in [
        "/home/alice", "/var/log", "/bin", "/usr/bin", "/opt/backup/profiles",
        "/etc/skel", "/tmp", "/mnt/recovery/bin", "/mnt/recovery/keys",
        "/mnt/recovery/docs", "/etc/network", "/etc/phoenix", "/proc"
    ]:
        parts = [p for p in d.strip("/").split("/") if p]
        curr = root
        for part in parts:
            if part not in curr.children:
                curr.children[part] = VFSNode(type="dir", permissions="755", owner="root")
            curr = curr.children[part]

    # --- MILESTONE 0: COLD BOOT ---
    add_node("/home/alice/README.txt", VFSNode(
        type="file", permissions="644", owner="alice",
        content="APOLLO WORKSTATION EMERGENCY RECOVERY\n\n1. Input ring buffer desynchronized.\n2. Execute 'repair_buffer' or '/usr/bin/repair_buffer' to restore terminal line discipline.\n"
    ))
    add_node("/home/alice/BOOT_FAIL.log", VFSNode(
        type="file", permissions="644", owner="alice",
        content="[CRITICAL] TTY ring buffer desync at 0x0042F. Arrow history disabled.\n[WARN] Subsystem APOLLO offline.\n"
    ))
    add_node("/usr/bin/repair_buffer", VFSNode(
        type="file", permissions="755", owner="root",
        content="#!/bin/sh\n# System buffer repair binary\n"
    ))

    # --- MILESTONE 1: OPERATOR'S CACHE ---
    add_node("/home/alice/.note.txt", VFSNode(
        type="file", permissions="644", owner="alice",
        content="Autocomplete and readline profiles backed up in /opt/backup/profiles/alice.bashrc\nRedirect to ~/.bashrc using cat <src> > ~/.bashrc\n"
    ))
    add_node("/opt/backup/profiles/CHEAT_SHEET.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="REDIRECT OPERATORS:\n  cat source.txt > dest.txt    # Overwrite\n  cat source.txt >> dest.txt   # Append\n"
    ))
    add_node("/opt/backup/profiles/alice.bashrc", VFSNode(
        type="file", permissions="644", owner="root",
        content="# APOLLO Readline Config\nexport PATH=/bin:/usr/bin:/mnt/recovery/bin\nset show-all-if-ambiguous on\n"
    ))

    # --- MILESTONE 2: FORENSIC LOG ANALYSIS ---
    add_node("/var/log/NOTE.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="Audit auth.log for security breaches. Filter entries with grep -i 'breach' or grep -i 'rogue'.\n"
    ))
    add_node("/var/log/CHEAT_SHEET.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="GREP USAGE:\n  grep -i 'pattern' file.log\n  tail -n 20 file.log\n"
    ))
    # Generate ~180 lines of simulated PAM auth.log entries ending with breach indicators
    log_lines = [f"May 12 10:{i//60:02d}:{i%60:02d} apollo pam_unix(sshd:session): session opened for user systemd" for i in range(170)]
    log_lines.append("May 12 10:58:12 apollo SECURITY_ALERT: Breach detected from 10.0.42.99")
    log_lines.append("May 12 10:58:15 apollo MALWARE_INJECT: Rogue mining process spawned (/tmp/sys_miner, PID 104)")
    log_lines.append("May 12 10:58:20 apollo KERNEL_CRITICAL: Recovery tools locked on partition /mnt/recovery")
    add_node("/var/log/auth.log", VFSNode(
        type="file", permissions="640", owner="root",
        content="\n".join(log_lines) + "\n"
    ))

    # --- MILESTONE 3 & 4: RECOVERY PARTITION & PERMISSIONS ---
    add_node("/mnt/recovery/NOTE.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="Recovery partition mounted. Locate restoration scripts (*.sh) and keys (*.key) using 'find /mnt/recovery'.\n"
    ))
    add_node("/mnt/recovery/CHEAT_SHEET.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="FIND & CHMOD:\n  find /mnt/recovery -name '*.sh'\n  chmod +x /path/to/script.sh\n  chmod 755 /path/to/script.sh\n"
    ))
    add_node("/mnt/recovery/bin/recovery.sh", VFSNode(
        type="file", permissions="000", owner="root",  # Gated by 0000 permissions
        content="#!/bin/sh\n# Signal Trap Patch Binary\n"
    ))
    add_node("/mnt/recovery/keys/phoenix.key", VFSNode(
        type="file", permissions="600", owner="root",
        content="AUTH_TOKEN=PX-9942-APOLLO-RECOVERY-KEY-2042\n"
    ))

    # --- MILESTONE 5: RUNAWAY MITIGATION ---
    add_node("/tmp/NOTE.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="Rogue stealth miner running under PID 104. Locate via 'ps aux | grep miner' and terminate with 'kill -9 104'.\n"
    ))
    add_node("/tmp/CHEAT_SHEET.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="PROCESS SIGNALS:\n  ps aux\n  kill 104      # SIGTERM (-15)\n  kill -9 104   # SIGKILL (-9)\n"
    ))

    # --- MILESTONE 6: NETWORK UPLINK DIAGNOSTIC ---
    add_node("/etc/network/NOTE.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="Interface apollo0 is DOWN. Bring online with 'ip link set apollo0 up' and test gateway 'ping -c 4 10.0.42.1'.\n"
    ))
    add_node("/etc/network/CHEAT_SHEET.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="NETWORK COMMANDS:\n  ip addr\n  ip link set apollo0 up\n  ss -tulpn\n  ping -c 4 10.0.42.1\n"
    ))
    add_node("/etc/network/interfaces", VFSNode(
        type="file", permissions="644", owner="root",
        content="auto apollo0\niface apollo0 inet static\n    address 10.0.42.15/24\n    gateway 10.0.42.1\n"
    ))

    # --- MILESTONE 7: PHOENIX RESTORATION ---
    add_node("/etc/phoenix/NOTE.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="1. Append /mnt/recovery/keys/phoenix.key to /etc/phoenix/phoenix.conf using >>\n2. Set permissions: chmod 644 /etc/phoenix/phoenix.conf\n3. Launch service: phoenix_daemon start\n"
    ))
    add_node("/etc/phoenix/CHEAT_SHEET.txt", VFSNode(
        type="file", permissions="644", owner="root",
        content="DAEMON ORCHESTRATION:\n  cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf\n  chmod 644 /etc/phoenix/phoenix.conf\n  phoenix_daemon start\n"
    ))
    add_node("/etc/phoenix/phoenix.conf", VFSNode(
        type="file", permissions="000", owner="root",
        content="[PHOENIX_CONFIG]\nPORT=8080\nGATEWAY=10.0.42.1\n"
    ))

    return root
```

---

### Module 2: Event Traps & VFS Mutation Listeners

To ensure organic Metroidvania progression, implement state transition checks inside command execution handlers or an `EventBus` observer to evaluate player actions against milestone criteria:

#### 2.1 Milestone 1 Trigger: `.bashrc` Redirection Observer
In `PipelineEngine` or `cmd_cat` / redirection handling, when `/home/alice/.bashrc` is written:
```python
def check_bashrc_restoration(ctx: CommandContext):
    node = ctx.vfs.resolve_path(["home", "alice", ".bashrc"])
    if node and node.is_file() and "show-all-if-ambiguous" in (node.content or ""):
        if not ctx.state.system_flags.get("BASHRC_RESTORED"):
            ctx.state.system_flags["BASHRC_RESTORED"] = True
            ctx.state.unlocked_ergonomics["autocomplete"] = True
            ctx.state.unlocked_ergonomics["tab_completion"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "BASHRC_RESTORED", "value": True}))
```

#### 2.2 Milestone 4 Trigger: Binary Execution (`recovery.sh`)
Add custom execution behavior when running `./recovery.sh` or `/mnt/recovery/bin/recovery.sh`:
```python
def execute_recovery_script(ctx: CommandContext) -> CommandResult:
    node = ctx.vfs.resolve_path(["mnt", "recovery", "bin", "recovery.sh"])
    if not node or node.permissions in ["000", "0000"]:
        return ctx.result_factory(stderr="bash: ./recovery.sh: Permission denied\n", exit_code=126)
    
    ctx.state.system_flags["PERMISSIONS_RESTORED"] = True
    ctx.state.system_flags["SIGINT_UNLOCKED"] = True
    ctx.state.unlocked_ergonomics["sigint"] = True
    ctx.state.unlocked_ergonomics["sigint_trap"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "PERMISSIONS_RESTORED", "value": True}))
    ctx.bus.publish(Event("flag_changed", {"flag": "SIGINT_UNLOCKED", "value": True}))
    
    return ctx.result_factory(
        stdout="[RECOVERY PROTOCOL]: Kernel signal traps linked. SIGINT (Ctrl+C) unlocked.\n"
    )
```

#### 2.3 Milestone 7 Trigger: Daemon Launch (`phoenix_daemon`)
Update `cmd_phoenix_daemon` to validate authorization tokens prior to enabling victory state:
```python
def cmd_phoenix_daemon(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "phoenix_daemon", "args": args}))
    
    conf_node = ctx.vfs.resolve_path(["etc", "phoenix", "phoenix.conf"])
    if not conf_node or "AUTH_TOKEN=" not in (conf_node.content or ""):
        return ctx.result_factory(
            stderr="[PHOENIX ERROR]: Authentication token missing in /etc/phoenix/phoenix.conf\n",
            exit_code=1
        )
    
    ctx.state.system_flags["PHOENIX_ONLINE"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "PHOENIX_ONLINE", "value": True}))
    
    return ctx.result_factory(
        stdout=(
            "========================================================================\n"
            " [PHOENIX RESTORATION COMPLETE]: Emergency Mesh Online!\n"
            " Gateway 10.0.42.1 synchronized. All APOLLO workstation systems nominal.\n"
            "========================================================================\n"
        )
    )
```

---

### Module 3: Key Binding Interceptors & Lock Advisories

Wire `build_key_bindings` in `prompt_toolkit` to check `unlocked_ergonomics` and display diegetic hardware advisories when locked:

```python
def build_key_bindings(get_context):
    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        ctx = get_context()
        if not ctx.state.unlocked_ergonomics.get("history"):
            print("\n[HARDWARE ERROR]: Input ring buffer desynchronized. Command history unavailable.")
            return
        event.current_buffer.auto_up()

    @kb.add("c-c")
    def _(event):
        ctx = get_context()
        if not ctx.state.unlocked_ergonomics.get("sigint"):
            print("\n[HARDWARE ERROR]: Signal trap handler offline. SIGINT (Ctrl+C) unavailable.")
            return
        event.current_buffer.reset()

    return kb
```

---

### Verification & Test Sequence (Milestones 0 – 7)

Validate game flow by executing the precise solution path:

1. **M0:** Run `repair_buffer` -> `BUFFER_REPAIRED = True`, Up/Down history enabled.
2. **M1:** Run `cat /opt/backup/profiles/alice.bashrc > /home/alice/.bashrc` -> `BASHRC_RESTORED = True`, Tab completion enabled.
3. **M2:** Run `grep -i "breach" /var/log/auth.log` -> Identifies PID 104 and `/mnt/recovery`.
4. **M3:** Run `find /mnt/recovery -name "*.sh"` -> Locates `/mnt/recovery/bin/recovery.sh`.
5. **M4:** Run `chmod 755 /mnt/recovery/bin/recovery.sh` and execute `./recovery.sh` -> `SIGINT_UNLOCKED = True`, Ctrl+C enabled.
6. **M5:** Run `ps aux | grep miner` then `kill -9 104` -> `MALWARE_TERMINATED = True`.
7. **M6:** Run `ip link set apollo0 up` then `ping -c 4 10.0.42.1` -> `NETWORK_ONLINE = True`.
8. **M7:** Run `cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf`, `chmod 644 /etc/phoenix/phoenix.conf`, and `phoenix_daemon start` -> `PHOENIX_ONLINE = True` (Victory Sequence).
