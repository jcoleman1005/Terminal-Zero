# GEMINI PROMPT & TECHNICAL SPECIFICATION (VERSION 2)
## Implementation Instructions: Terminal Zero - Final Feature Parity & Engineering Checklist

### System Overview & Context
You are extending the **Terminal Zero** Python prototype (`Prototype.txt`) to reach 100% feature parity with **TERMINAL ZERO GDD v2.md**.

The existing prototype already includes:
- Virtual Filesystem (`VFSNode`, `VirtualFilesystem`)
- Process Table & Network State Data Models
- Process Commands (`ps`, `kill`) and Network Commands (`ip`, `ss`, `ping`)
- Erudite Diagnostic Assistant (`decrypt`) inspecting `state.last_stderr`
- Pedagogical Debrief Engine (`DebriefManager`) hooked into `EventBus`
- JSON Persistence Engine (`savegame.json`, `cmd_sync`)
- Extended POSIX Utilities: `chmod`, `man`, `head`, `tail`, `grep`, `find`

Follow these step-by-step technical specifications to implement the 5 remaining modules.

---

### Module 1: Pipeline Execution Engine (`|`) & Redirection (`>`, `>>`)

#### 1.1 Multi-Stage Pipeline Chaining (`|`)
- **Parser Update:** Update command parsing to split raw user input on unquoted pipe `|` characters into an ordered list of `ParsedCommand` stages.
- **Execution Workflow:**
  1. For stage $1$, initialize `CommandContext(stdin="")`.
  2. Execute stage $1$ and capture `CommandResult.stdout`.
  3. If stage $1$ fails (`exit_code != 0`), abort pipeline execution unless handled, returning stage $1$'s `stderr` and `exit_code`.
  4. For each subsequent stage $i > 1$, instantiate `CommandContext` with `stdin=stage_{i-1}.stdout`.
  5. The pipeline's final result is the `CommandResult` of the last stage.
- **Example Supported Pipelines:**
  - `ps aux | grep sys_miner`
  - `cat /var/log/syslog | grep error`
  - `find / -name "*.conf" | head -n 3`

#### 1.2 File Redirection (`>`, `>>`)
- **Behavior:**
  - `>` (Overwrite): Redirect stdout of the final command/pipeline stage to write to target VFS file path. If file exists, overwrite content; if not, create new `VFSNode`.
  - `>>` (Append): Redirect stdout to append to target VFS file path.
- **Error Handling:** Check write permissions on target parent directory before redirecting. Return `exit_code=1` with `Permission denied` on failure.

---

### Module 2: Diegetic `prompt_toolkit` Ergonomic Interceptors

#### 2.1 Key Binding Interceptors
Modify `prompt_toolkit` key bindings in `TerminalShell` to intercept keys before ergonomics are unlocked:
- **Up / Down Arrows (Command History):**
  - Check `ctx.state.unlocked_ergonomics.get("history_arrows", False)`.
  - If `False`, suppress history navigation and display diegetic alert:
    `[HARDWARE ERROR]: Input ring buffer corrupted. Navigation history disabled.`
- **Tab Key (Autocompletion):**
  - Check `ctx.state.unlocked_ergonomics.get("tab_completion", False)`.
  - If `False`, suppress tab completion and display diegetic alert:
    `[DRIVER MISSING]: libreadline unit offline. Tab autocompletion unavailable.`
- **Ctrl+C (SIGINT Trap):**
  - Check `ctx.state.unlocked_ergonomics.get("sigint_trap", False)`.
  - If `False`, display:
    `[SIGNAL FAULT]: Process signal traps unconfigured. SIGINT ignored.`

#### 2.2 Ergonomic Unlocks via Event Triggers
- When `/bin/repair_buffer` is executed or `BUFFER_REPAIRED` flag transitions to `True`: set `state.unlocked_ergonomics["history_arrows"] = True`.
- When `/home/alice/.bashrc` is restored or `BASHRC_RESTORED` flag is set: set `state.unlocked_ergonomics["tab_completion"] = True`.

---

### Module 3: Automatic `last_stderr` Wrapper Integration

#### 3.1 Execution Wrapper Modification
Ensure every command execution automatically captures `stderr` output to `state.last_stderr`:
```python
def execute_command_line(self, raw_input: str) -> CommandResult:
    result = self.pipeline_engine.run(raw_input, self.state)
    if result.exit_code != 0 and result.stderr:
        self.state.last_stderr = result.stderr.strip()
    return result
```

#### 3.2 `decrypt` Diagnostic Integration
- When running `decrypt` (or `apollo-diagnostics`), inspect `self.state.last_stderr`.
- Match error patterns (e.g., `Permission denied`, `No such file or directory`, `Command not found`, `Network is unreachable`).
- Return plain-language diagnostic advice explaining what command failed and providing diegetic hints on how to resolve it.

---

### Module 4: Complete Workstation VFS Map & Milestones 0–7

Expand `build_default_vfs()` to construct the continuous workstation map for APOLLO across all milestones:

#### 4.1 VFS Structure
1. **`/var/log/`:**
   - `syslog`: Timeline of system failure, kernel messages, and rogue miner startup sequence.
   - `auth.log`: Failed authentication records and unauthorized privilege escalation events.
2. **`/mnt/recovery/bin/`:**
   - Unmounted/damaged binaries (`apollo-net`, `repair_buffer`, `phoenix_ctl`) with `permissions="000"`.
   - Players must use `chmod +x` or `chmod 755` to make them executable.
3. **`/opt/phoenix/`:**
   - `phoenix.conf`: Daemon config file specifying target gateway IP (`10.0.42.1`) and socket port (`8080`).
   - `phoenix_daemon`: Main restoration daemon executable.
4. **`/home/alice/`:**
   - `.bashrc`: Configuration script missing `libreadline` alias bindings.
   - `.bash_history`: Log of past operator commands offering solution hints.
   - `TODO.txt`: In-world operational scratchpad.

#### 4.2 Global Event Flag Triggers
Ensure execution of key actions fires `EventBus` events that trigger system flag transitions:
- `chmod +x /mnt/recovery/bin/repair_buffer` → Sets `BUFFER_REPAIRED = True`
- Restoring `.bashrc` → Sets `BASHRC_RESTORED = True`
- `kill -9 104` (terminating `sys_miner`) → Sets `MALWARE_TERMINATED = True`
- `ip link set apollo0 up` → Sets `NETWORK_ONLINE = True`
- Executing `/opt/phoenix/phoenix_daemon start` → Sets `PHOENIX_ONLINE = True`

---

### Module 5: Simulated Live Log Streaming (`tail -f`)

#### 5.1 `cmd_tail` Implementation with `-f`
- When `-f` flag is present in `tail`:
  1. Print the last $N$ lines of the target file (default $10$).
  2. Output streaming marker: `[LOG STREAM ACTIVE - Press Ctrl+C to abort]`.
  3. Append simulated real-time event entries depending on system flags (e.g., periodic daemon ping messages or network interface status probes).
  4. Allow user to break out using `Ctrl+C` (or simulated return).

---

### Verification & Delivery Checklist
1. All new commands (`ps`, `kill`, `ip`, `ss`, `ping`, `decrypt`, `chmod`, `man`, `head`, `tail`, `grep`, `find`) registered in `COMMAND_TABLE`.
2. Pipeline operator `|` correctly passes `stdout` to subsequent command `stdin`.
3. `state.last_stderr` reliably populated on non-zero command returns.
4. `savegame.json` state serialization updated to cover all new flags, network state, and ergonomic toggle states.
5. Zero host execution: All VFS operations, process state, and network simulations run strictly in memory within the sandbox environment.
