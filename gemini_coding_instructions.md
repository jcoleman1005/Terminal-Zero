# GEMINI PROMPT & TECHNICAL SPECIFICATION
## Implementation Instructions: Terminal Zero Missing Features & Command Suites

### System Overview & Context
You are tasked with extending the current **Terminal Zero** prototype (`Prototype.txt`) to reach full feature parity with **TERMINAL ZERO GDD v2.md**. 

The current prototype already implements:
- POSIX Virtual Filesystem (`VFSNode`, `VirtualFilesystem`)
- `TerminalState` with `process_table`, `system_flags`, `unlocked_ergonomics`, `last_stderr`, and env vars
- `EventBus` and pub/sub architecture
- `prompt_toolkit` REPL shell with `VFSCompleter` and key bindings
- `savegame.json` state serialization and `cmd_sync`
- Inspection/navigation tools: `pwd`, `cd`, `ls`, `cat`, `head`, `tail`, `grep`, `find`, `chmod`, `man`, `decrypt`

You must implement the remaining 5 technical modules defined in GDD v2 without breaking existing contracts or introducing external runtime dependencies outside standard Python 3 and `prompt_toolkit`.

---

### Module 1: Process Control Suite (`ps`, `kill`)

#### 1.1 `cmd_ps(ctx: CommandContext, args: List[str]) -> CommandResult`
- **Supported Flags:** `aux`, `-ef` (default to standard process table list if no flags provided).
- **Behavior:**
  - Read `ctx.state.process_table` (list of `ProcessEntry` dataclass instances).
  - Format output as an aligned tabular string with headers: `USER PID %CPU COMMAND`.
  - Filter or format entries depending on flags (e.g., `aux` shows all user processes with CPU usage; `-ef` shows full command format).
- **Event Bus:** Publish `Event("command_executed", {"command": "ps", "args": args})`.

#### 1.2 `cmd_kill(ctx: CommandContext, args: List[str]) -> CommandResult`
- **Supported Flags/Arguments:** `-[signal]` (`-9` / `SIGKILL`, `-15` / `SIGTERM`) and `<PID>`.
  - Default signal is `15` (`SIGTERM`) if omitted (e.g., `kill 104`).
- **Behavior:**
  - Parse target `PID` integer from positional arguments. Return exit code `1` with `kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ...` if PID is missing or invalid.
  - Search `ctx.state.process_table` for matching `pid`.
  - If PID not found, return `stderr="kill: ({pid}) - No such process
"`, `exit_code=1`.
  - Remove target `ProcessEntry` from `ctx.state.process_table` or update its `status` to `"terminated"`.
- **Milestone 5 Event Integration:**
  - If the killed process is the malware binary (`sys_miner`, PID 104) and signal is `-9` or `-15`:
    1. Set `ctx.state.system_flags["MALWARE_TERMINATED"] = True`.
    2. Publish `Event("flag_changed", {"flag": "MALWARE_TERMINATED", "value": True})`.
    3. Return `stdout=f"Process {pid} ({proc_name}) terminated by signal {sig}.
"`.

---

### Module 2: Network Operations Suite (`ip`, `ss`, `ping`)

#### 2.1 State Model Extension (`TerminalState`)
Add network state structures to `TerminalState.__init__`:
```python
self.network_interfaces: Dict[str, Dict[str, Any]] = {
    "lo": {"ip": "127.0.0.1/8", "state": "UP", "mac": "00:00:00:00:00:00"},
    "apollo0": {"ip": "10.0.42.15/24", "state": "DOWN", "mac": "52:54:00:12:34:56"}
}
self.listening_sockets: List[Dict[str, Any]] = [
    {"proto": "tcp", "local": "0.0.0.0:22", "peer": "0.0.0.0:*", "state": "LISTEN", "pid": 210, "proc": "sshd"},
    {"proto": "tcp", "local": "127.0.0.1:8080", "peer": "0.0.0.0:*", "state": "LISTEN", "pid": 500, "proc": "phoenix_daemon"}
]
```

#### 2.2 `cmd_ip(ctx: CommandContext, args: List[str]) -> CommandResult`
- **Subcommands:** `addr` (or `a`), `link` (or `l`), `route` (or `r`).
- **Behavior:**
  - `ip addr`: Print formatted interface details including interface name, flags, inet IP, and MAC address.
  - `ip link`: Print link state (`UP` or `DOWN`). Support `ip link set <iface> up` to toggle interface state to `UP`.
  - `ip route`: Print default routing table (e.g., `default via 10.0.42.1 dev apollo0`).
- **Milestone 6 Integration:** Toggling `apollo0` to `UP` sets `ctx.state.system_flags["NETWORK_ONLINE"] = True`.

#### 2.3 `cmd_ss(ctx: CommandContext, args: List[str]) -> CommandResult`
- **Supported Flags:** `-tulpn`, `-t`, `-u`, `-l`, `-p`, `-n`.
- **Behavior:** Print tabular network socket state with headers: `Netid State Recv-Q Send-Q Local Address:Port Peer Address:Port Process`.

#### 2.4 `cmd_ping(ctx: CommandContext, args: List[str]) -> CommandResult`
- **Supported Flags:** `-c <count>` (default `4`).
- **Behavior:**
  - Check `apollo0` state in `ctx.state.network_interfaces`. If `"DOWN"`, return `stderr="ping: connect: Network is unreachable
"`, `exit_code=2`.
  - If `apollo0` is `"UP"`, output `<count>` lines of simulated ICMP echo responses: `64 bytes from {target}: icmp_seq={i} ttl=64 time=0.042 ms`, followed by packet statistics summary.

---

### Module 3: Pipeline Execution Engine (`|`) & `tail -f`

#### 3.1 Pipeline Chaining (`|`)
Modify command execution logic in `TerminalShell` / parser:
1. Parse the input string by splitting on unquoted `|` symbols into a list of pipeline stages.
2. For stage $1$, execute command with `ctx.stdin = ""`. Capture `CommandResult.stdout`.
3. For stage $i > 1$, pass `stdout` of stage $i-1$ into stage $i$ as `CommandContext(stdin=previous_stdout)`.
4. The final pipeline result returns stdout from the last command stage.
5. Supported use cases: `ps aux | grep miner`, `cat /var/log/syslog | grep error`, `find / -name "*.sh" | head -n 5`.

#### 3.2 Simulated Event Streaming (`tail -f`)
- In `cmd_tail`, detect the `-f` flag.
- Print initial $N$ lines, followed by a simulated stream log message: `[STREAM ACTIVE - Press Ctrl+C to exit]`, followed by simulated runtime event bursts.

---

### Module 4: Campaign World & VFS Hierarchy (Milestones 0–7)

Expand `build_default_vfs()` to construct the continuous workstation map for APOLLO:

1. **`/var/log/`:**
   - `/var/log/syslog`: System startup logs and network interface crash records.
   - `/var/log/auth.log`: Authentication log entries showing brute-force attempts and timestamp traces.
2. **`/mnt/recovery/bin/`:**
   - Store backup binaries (`apollo-net`, `recovery-tool`) with `permissions="000"`. Players must use `chmod +x` or `chmod 755` after mounting/locating them.
3. **`/opt/phoenix/`:**
   - `/opt/phoenix/phoenix.conf`: Daemon configuration file containing network port and gateway IP.
   - `/opt/phoenix/phoenix_daemon`: Main restoration executable.
4. **`/home/alice/`:**
   - `.bash_history`: Corrupted shell history file containing historical command hints.
   - `TODO.txt`: Operational scratchpad providing diegetic orientation hints (*Outer Wilds* style).

---

### Module 5: Pedagogical Features ("Take It to Linux" Debriefs)

#### 5.1 `DebriefManager`
Create a helper class `DebriefManager` subscribed to the `EventBus`:
- Listens for `flag_changed` events.
- When key narrative milestones transition to `True` (e.g., `BUFFER_REPAIRED`, `MALWARE_TERMINATED`, `NETWORK_ONLINE`, `PHOENIX_ONLINE`), print a styled TUI modal:
```text
┌────────────────────────────────────────────────────────────────────────┐
│ [TAKE IT TO LINUX]: Real-World System Administration                  │
├────────────────────────────────────────────────────────────────────────┤
│ You just used 'kill -9' to terminate a rogue process.                  │
│ In production Linux environments:                                     │
│ • SIGTERM (-15) allows processes to clean up sockets & open files.     │
│ • SIGKILL (-9) immediately revokes kernel resources; use with care!    │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Integration Checklist & Verification
1. Register `cmd_ps`, `cmd_kill`, `cmd_ip`, `cmd_ss`, `cmd_ping` in `COMMAND_TABLE`.
2. Add manual pages for all new commands (`ps`, `kill`, `ip`, `ss`, `ping`) to `MAN_PAGES`.
3. Verify that `save_game_state` and `load_game_state` serialize and deserialize `network_interfaces` and `listening_sockets` to/from `savegame.json`.
4. Ensure zero host execution: All operations strictly mutate internal data structures in memory.
