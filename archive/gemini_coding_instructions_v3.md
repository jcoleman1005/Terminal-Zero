# GEMINI PROMPT & TECHNICAL SPECIFICATION (V3 MASTER)
## Comprehensive Implementation Instructions: Terminal Zero Hardened Engine & Milestone Progression

### System Overview & Context
You are tasked with updating and extending the **Terminal Zero** Python prototype (`Prototype.txt`) to achieve **100% feature parity** with **TERMINAL ZERO GDD v2.md**, **Milestone Progression.md**, and the hardened logic standards established in the **Critiques** and **Puzzle Progression Design Critique**.

The prototype contains the baseline infrastructure:
- POSIX Virtual Filesystem (`VFSNode`, `VirtualFilesystem`)
- `TerminalState` with `process_table`, `system_flags`, `unlocked_ergonomics`, `network_interfaces`, and `last_stderr`
- `EventBus` pub/sub architecture & `DebriefManager` ("Take It to Linux")
- `prompt_toolkit` REPL shell with `VFSCompleter` and key bindings
- `savegame.json` state serialization and `sync` command
- Standard utilities (`pwd`, `cd`, `ls`, `cat`, `head`, `tail`, `grep`, `find`, `chmod`, `man`, `ps`, `kill`, `ip`, `ss`, `ping`, `echo`, `repair_buffer`, `decrypt`)

You must implement all concrete logic fixes, state evaluation guards, pipeline write hooks, and the hardened Milestone 0–7 VFS workstation map without introducing external dependencies outside Python 3 standard library and `prompt_toolkit`.

---

### Critical Patch Fixes & Hardening Rules (From System Audits)

#### 1. Hardened Daemon Validation (`cmd_phoenix_daemon` & `cmd_phoenix_ctl`)
- **Bypass Prevention:** Replace unconditional flag assignment with strict state, file permission, and authorization token validation.
```python
def cmd_phoenix_daemon(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "phoenix_daemon", "args": args}))
    
    # 1. Validate Network State
    if not ctx.state.system_flags.get("NETWORK_ONLINE", False):
        return ctx.result_factory(
            stderr="[PHOENIX ERROR]: Network gateway unreachable. Interface 'apollo0' is DOWN.\n", 
            exit_code=1
        )
    
    # 2. Resolve Config Node
    conf_node = ctx.vfs.resolve_path(["etc", "phoenix", "phoenix.conf"])
    if not conf_node or not conf_node.is_file():
        return ctx.result_factory(
            stderr="[PHOENIX ERROR]: Missing configuration file /etc/phoenix/phoenix.conf\n", 
            exit_code=1
        )
    
    # 3. Check File Permissions (Must be 0644)
    if conf_node.permissions != "644":
        return ctx.result_factory(
            stderr=f"[PHOENIX ERROR]: Insecure permissions on /etc/phoenix/phoenix.conf (mode: {conf_node.permissions}). Required: 0644\n", 
            exit_code=1
        )
    
    # 4. Check Cryptographic Token Presence
    if "PX-KEY-7701-ALPHA" not in (conf_node.content or ""):
        return ctx.result_factory(
            stderr="[PHOENIX ERROR]: Authentication token missing or invalid in /etc/phoenix/phoenix.conf\n", 
            exit_code=1
        )

    # Success State Transition
    ctx.state.system_flags["PHOENIX_ONLINE"] = True
    
    # Dynamically bind port 8080 upon launch (if not already present)
    if not any(s.get("local") == "127.0.0.1:8080" for s in ctx.state.listening_sockets):
        ctx.state.listening_sockets.append({
            "proto": "tcp", "local": "127.0.0.1:8080", "peer": "0.0.0.0:*", 
            "state": "LISTEN", "pid": 500, "proc": "phoenix_daemon"
        })
        
    ctx.bus.publish(Event("flag_changed", {"flag": "PHOENIX_ONLINE", "value": True}))
    return ctx.result_factory(
        stdout="[PHOENIX-DAEMON]: Emergency Restoration Protocol activated. Listening on 127.0.0.1:8080. Gateway ONLINE.\n"
    )
```

#### 2. Sanitizing Initial Socket Registry State (`TerminalState`)
- **Desynchronization Fix:** Remove port `8080` from `TerminalState.__init__` socket initialization. Port `8080` must ONLY appear after `phoenix_daemon` successfully starts in Milestone 7.
```python
# Initial state: only sshd listening
self.listening_sockets: List[Dict[str, Any]] = [
    {"proto": "tcp", "local": "0.0.0.0:22", "peer": "0.0.0.0:*", "state": "LISTEN", "pid": 210, "proc": "sshd"}
]
```

#### 3. Stream Redirection VFS Write Hooks (`.bashrc` Restoration)
- Hook file output redirection (`>` and `>>`) in `PipelineEngine` or the shell execution wrapper so that writing to `/home/alice/.bashrc` automatically evaluates file contents and triggers `BASHRC_RESTORED`.
```python
def check_bashrc_restoration(vfs: VirtualFilesystem, state: TerminalState, bus: EventBus):
    node = vfs.resolve_path(["home", "alice", ".bashrc"])
    if node and node.is_file() and node.content and len(node.content.strip()) > 0:
        if not state.system_flags.get("BASHRC_RESTORED", False):
            state.system_flags["BASHRC_RESTORED"] = True
            state.unlocked_ergonomics["autocomplete"] = True
            state.unlocked_ergonomics["tab_completion"] = True
            bus.publish(Event("flag_changed", {"flag": "BASHRC_RESTORED", "value": True}))
```

#### 4. Strict Process Signaling in `cmd_kill` (PID 104 / `sys_miner`)
- `sys_miner` (PID 104) MUST trap standard `SIGTERM` (`-15` or no signal specifier) and refuse to exit.
- `sys_miner` requires explicit `kill -9 104` (`SIGKILL`) to force kernel termination and set `MALWARE_TERMINATED = True`.
```python
def cmd_kill(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "kill", "args": args}))
    if not args:
        return ctx.result_factory(
            stderr="kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ...\n", 
            exit_code=1
        )
    
    sig = "15"
    pid_str = None
    
    idx = 0
    while idx < len(args):
        if args[idx].startswith("-"):
            sig = args[idx].lstrip("-")
            idx += 1
        else:
            pid_str = args[idx]
            idx += 1
            
    if not pid_str or not pid_str.isdigit():
        return ctx.result_factory(stderr="kill: invalid pid or signal specification\n", exit_code=1)
        
    target_pid = int(pid_str)
    
    # Locate Process
    proc = next((p for p in ctx.state.process_table if p.pid == target_pid and p.status == "running"), None)
    if not proc:
        return ctx.result_factory(stderr=f"kill: ({target_pid}) - No such process\n", exit_code=1)
        
    # Special Handling for sys_miner (PID 104)
    if target_pid == 104 or proc.name == "sys_miner":
        if sig in ["9", "KILL", "SIGKILL"]:
            proc.status = "terminated"
            ctx.state.system_flags["MALWARE_TERMINATED"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "MALWARE_TERMINATED", "value": True}))
            return ctx.result_factory(stdout="[KERNEL]: Process 104 (sys_miner) forcefully killed by SIGKILL.\n")
        else:
            return ctx.result_factory(
                stdout="[sys_miner]: Caught SIGTERM signal. Trapping signal and continuing execution... (Use SIGKILL / -9 to force termination)\n"
            )

    # Default process termination for other PIDs
    proc.status = "terminated"
    return ctx.result_factory(stdout=f"Process {target_pid} terminated.\n")
```

#### 5. Softlock Protection Backups in `build_default_vfs()`
- Provide fallback copies in cold storage so players who overwrite `phoenix.conf` with `>` instead of appending `>>` can recover diegetically:
  - `/etc/phoenix/phoenix.conf.default` (permissions `0644`)
  - `/opt/backup/phoenix.conf` (permissions `0644`)

#### 6. Syntax Template Clue Alignment
- Ensure all `CHEAT_SHEET.txt` and `NOTE.txt` files provide abstract syntax templates (e.g., `cat <source_path> > <destination_path>`) rather than verbatim copy-paste commands, prompting active deduction.

---

### Module Specifications & Architecture

#### Pipeline & Stream Redirection Engine (`|`, `>`, `>>`)
1. Parse raw input using `split_unquoted(line, "|")` to identify pipeline stages.
2. Execute Stage 1 with `ctx.stdin = ""`. Pass stdout as `ctx.stdin` into Stage 2, and so forth.
3. For output redirection (`>` or `>>`), capture the stdout of the final pipeline stage and write/append content to the target `VFSNode`.
4. Trigger `check_bashrc_restoration` after file writes.

#### Automatic `last_stderr` Context Capture
- In `TerminalShell` / execution loop, wrap every command call:
```python
result = pipeline_engine.execute(line, ctx)
if result.exit_code != 0 and result.stderr:
    ctx.state.last_stderr = result.stderr
```

#### Diegetic Ergonomic Key Binding Interceptors
- Intercept key events in `build_key_bindings`:
  - **Up/Down Arrows:** If `not state.unlocked_ergonomics.get("history")`, print `[HARDWARE ERROR]: Input ring buffer desynchronized. Command history unavailable.`.
  - **Tab:** If `not state.unlocked_ergonomics.get("autocomplete")`, print `[HARDWARE ERROR]: Readline profile missing. Autocompletion unavailable.`.
  - **Ctrl+C:** If `not state.unlocked_ergonomics.get("sigint")`, print `[HARDWARE ERROR]: Signal trap handler offline. SIGINT unavailable.`.

---

### Workstation VFS Map (`build_default_vfs()`)

Construct the full continuous workstation map across `/home/alice`, `/var/log`, `/mnt/recovery`, `/etc/network`, and `/etc/phoenix`:

```python
def build_default_vfs() -> VFSNode:
    root = VFSNode(type="dir", permissions="755", owner="root")
    
    # Directory Structure
    dirs = [
        "bin", "usr/bin", "home/alice", "var/log", "tmp", 
        "mnt/recovery/bin", "mnt/recovery/keys", "mnt/recovery/docs",
        "opt/backup/profiles", "etc/network", "etc/phoenix"
    ]
    for d in dirs:
        parts = d.split("/")
        curr = root
        for p in parts:
            if p not in curr.children:
                curr.children[p] = VFSNode(type="dir", permissions="755", owner="root")
            curr = curr.children[p]

    # Milestone 0: /home/alice & /usr/bin
    root.resolve_path_relative(["home", "alice"]).children["README.txt"] = VFSNode(
        type="file", permissions="0644", owner="alice",
        content="APOLLO WORKSTATION RECOVERY\n1. Inspect BOOT_FAIL.log.\n2. Run /usr/bin/repair_buffer to restore history buffer.\n"
    )
    root.resolve_path_relative(["home", "alice"]).children["BOOT_FAIL.log"] = VFSNode(
        type="file", permissions="0644", owner="alice",
        content="[FAULT]: TTY ring buffer desynced. Run repair_buffer to clear fault.\n"
    )

    # Milestone 1: /opt/backup/profiles & /home/alice
    root.resolve_path_relative(["home", "alice"]).children[".note.txt"] = VFSNode(
        type="file", permissions="0644", owner="alice",
        content="Shell readline profile missing. Backup profiles stored in /opt/backup/profiles/.\n"
    )
    root.resolve_path_relative(["opt", "backup", "profiles"]).children["CHEAT_SHEET.txt"] = VFSNode(
        type="file", permissions="0644", owner="root",
        content="RESTORING SHELL PROFILES:\nUse stdout redirection to copy profile templates:\ncat <profile_src> > <target_path>\n"
    )
    root.resolve_path_relative(["opt", "backup", "profiles"]).children["alice.bashrc"] = VFSNode(
        type="file", permissions="0644", owner="root",
        content="# ALICE BASHRC TEMPLATE\nexport PATH=/bin:/usr/bin:/mnt/recovery/bin\nalias ll='ls -la'\n"
    )

    # Milestone 2: /var/log/auth.log
    auth_content = "[INFO]: System boot complete.\n" + (" [WARN]: Normal PAM session.\n" * 20) + \
                   "[ALERT]: Unauthorized access detected. Rogue miner deployed to /tmp/sys_miner (PID 104).\n" + \
                   "[ALERT]: Recovery binary stripped in /mnt/recovery/bin/recovery.sh.\n"
    root.resolve_path_relative(["var", "log"]).children["auth.log"] = VFSNode(
        type="file", permissions="0640", owner="root", content=auth_content
    )

    # Milestone 3 & 4: /mnt/recovery/bin/recovery.sh
    root.resolve_path_relative(["mnt", "recovery", "bin"]).children["recovery.sh"] = VFSNode(
        type="file", permissions="0000", owner="root",
        content="#!/bin/bash\necho '[KERNEL]: Restoring signal trap vector...'\necho 'SIGINT handler online.'\n"
    )
    root.resolve_path_relative(["mnt", "recovery", "keys"]).children["phoenix.key"] = VFSNode(
        type="file", permissions="0600", owner="root", content="PX-KEY-7701-ALPHA\n"
    )

    # Milestone 6: /etc/network/interfaces
    root.resolve_path_relative(["etc", "network"]).children["interfaces"] = VFSNode(
        type="file", permissions="0644", owner="root",
        content="auto lo\niface lo inet loopback\n\nauto apollo0\niface apollo0 inet static\n  address 10.0.42.15/24\n  gateway 10.0.42.1\n"
    )

    # Milestone 7: /etc/phoenix/ & Fallback Backups
    initial_conf = "[PHOENIX_DAEMON_CONFIG]\nLISTEN_PORT=8080\nGATEWAY=10.0.42.1\n"
    root.resolve_path_relative(["etc", "phoenix"]).children["phoenix.conf"] = VFSNode(
        type="file", permissions="0600", owner="root", content=initial_conf
    )
    # Cold storage backup copies to prevent softlock
    root.resolve_path_relative(["etc", "phoenix"]).children["phoenix.conf.default"] = VFSNode(
        type="file", permissions="0644", owner="root", content=initial_conf
    )
    root.resolve_path_relative(["opt", "backup"]).children["phoenix.conf"] = VFSNode(
        type="file", permissions="0644", owner="root", content=initial_conf
    )

    return root
```

---

### Complete Implementation Checklist
1. **Precondition Validation:** Implement strict checks in `cmd_phoenix_daemon` for network interface, file permissions (`0644`), and authorization key.
2. **Socket Cleanup:** Initialize `listening_sockets` with port 22 only.
3. **Write Hook:** Hook file write redirection to evaluate `/home/alice/.bashrc` and set `BASHRC_RESTORED`.
4. **Strict Signal Handling:** Enforce `-9` / `SIGKILL` requirement for PID 104 in `cmd_kill`.
5. **Softlock Protection:** Instantiate backup configs (`phoenix.conf.default`) in `build_default_vfs()`.
6. **Error Capture:** Store stderr in `last_stderr` on non-zero command returns.
7. **Verification:** Ensure state serialization to `savegame.json` preserves all mutated flags and sockets.
