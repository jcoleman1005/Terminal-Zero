# TERMINAL ZERO — Game Design Document (v2.0 Production Master)

## Document Revision Summary & Changelog

| Section / System | Type of Change | Summary of Architectural Decision |
| --- | --- | --- |
| **Platform Target** | *Cut* | Scoped strictly to desktop terminal environments (Linux, macOS, Windows). Cut mobile/Termux support.

 |
| **Campaign Length** | *Modification* | Re-benchmarked campaign playtime from 4–8h to a focused **2–3.5 hours** across a continuous workstation map.

 |
| **Filesystem & Lore** | *Addition* | Aligned virtual tree with real-world FHS/POSIX standards. Integrated diegetic explanations of Unix design history (e.g., `/var` evolution) into optional system artifacts.

 |
| **Shell Ergonomics** | *Systemic Pivot* | Adopted **Hybrid Ergonomic Unlocks** via `prompt_toolkit`. Cursor editing is available at boot; Command History (Up/Down), Tab Autocompletion, and Signal Traps (`Ctrl+C`) unlock diegetically via firmware/driver repairs.

 |
| **Command Progression** | *Systemic Pivot* | Replaced artificial syntax locking with **Diegetic Soft-Gating** (damaged binaries in `/usr/bin`, corrupted `$PATH`, unmounted directories). Bounded supported flag matrix. Replaced interactive pagers (`less`/`more`) with `cat`, `head`, and `tail`.

 |
| **Feedback & Hints** | *Systemic Pivot* | Standardized on authentic POSIX stderr strings. Added a fictional in-game `decrypt` command for optional error translation. Converted hints to environmental discovery (*Outer Wilds* style) and removed all popup tutorials.

 |
| **Scoring System** | *Cut* | Completely removed point scoring, hint penalties, and grade screens. Progression and puzzle resolution are the sole victory conditions.

 |
| **Campaign Model** | *Systemic Pivot* | Converted episodic mission levels into a single, **continuous Metroidvania-style workstation map** (`APOLLO`) with state flags, organic mounting, and environmental backtracking. Standardized network tooling on `ip` and `ss`.

 |
| **Persistence Engine** | *Modification* | Replaced out-of-character `save`/`load` commands with automatic background checkpointing on state transitions and a diegetic `sync` command. Persists full virtual filesystem, process table, unlocks, and story flags to `savegame.json`.

 |
| **MVP & Roadmap** | *Modification* | Redefined MVP around the continuous workstation slice and driver repairs. Formatted a 5-phase engineering roadmap and isolated expansions to conceptual-only status.

 |

---

## 1. Executive Summary & High Concept

* **Title:** TERMINAL ZERO


* **Genre:** Terminal Metroidvania / Educational CLI Investigation / Systems Adventure


* **Platform:** Linux, macOS, Windows (Desktop CLI / Terminal Emulators)


* **Runtime:** Python 3 (`prompt_toolkit`, `shlex`/`bashlex`)


* **Estimated Playtime:** 2–3.5 hours (Full Campaign)
* **Core Design Philosophy:** *The player should learn Linux because they need Linux to solve the game.* The terminal is not a mini-game—it is the entire gameplay engine and interface.


* **Safety Mandate:** Zero host execution. All commands, pipelines, and state mutations evaluate strictly within an isolated in-memory Python environment.



---

## 2. Narrative & Worldbuilding Architecture

### 2.1 The Setting

The year is 2042. A catastrophic cyber incident has crippled global infrastructure, taking down emergency grids, routing backbones, and municipal services.

The player assumes control of **`APOLLO`**, a damaged local workstation running a degraded Linux environment. Through `APOLLO`, the player must troubleshoot damaged subsystems, discover encrypted keys, and orchestrate the recovery of **`PHOENIX`**—a dormant, distributed emergency restoration network.

```
+-------------------------------------------------------------+
|                      WORKSTATION: APOLLO                    |
|                                                             |
|  [Filesystem]         [Process Table]       [Network Stack] |
|  / (Root)             - PID 1 (init)        - lo (127.0.0.1)|
|  ├── /etc             - PID 104 (malware)   - eth0 (offline)|
|  ├── /var/log         - PID 412 (phoenix)   - Sockets (ss)  |
|  └── /mnt/recovery                                          |
+-------------------------------------------------------------+

```

### 2.2 Environmental Storytelling & Historical Authenticity

* **Authentic FHS Layout:** The virtual tree strictly follows the Filesystem Hierarchy Standard (`/etc`, `/var/log`, `/proc`, `/home`, `/usr/bin`, `/mnt`).


* **Diegetic Unix History:** Log files, header comments, and old sysadmin memos explain real-world Linux conventions (e.g., explaining why `/var` isolates variable runtime data from the static `/usr` hierarchy) to ground abstract concepts in functional logic.
* **Sandbox File Delving:** Non-linear exploration is rewarded through optional lore notes, system artifacts, and operator scratchpads that yield context and unlock hints.



---

## 3. Terminal Engine & UI/UX Architecture

### 3.1 Input Engine & Parser Flow

The game utilizes Python's `prompt_toolkit` to deliver an authentic terminal experience while executing an internal parsing engine:

```
[Player Keystroke]
        │
        ▼
[prompt_toolkit Input Handler] ───► (Check Ergonomic Driver Flags)
        │
        ▼
[Lexer / AST Generator (shlex / bashlex)]
        │
        ▼
[Diegetic Binary & PATH Registry] ───► (Is Command Repaired / Accessible?)
        │
        ▼
[Virtual Execution Engine] ───► Mutates Virtual FS / Process Table / Sockets
        │
        ▼
[Output Formatter] ───► Returns POSIX stdout / stderr to TUI

```

### 3.2 Progressive Ergonomic Drivers (Hybrid Unlocks)

To balance authentic muscle memory with diegetic progression, basic line editing is active from boot, while advanced shell ergonomics are unlocked via in-game system repairs:

* **Baseline (Boot):** Character entry, Backspace, Delete, and Left/Right cursor movement are fully active.
* **Command History (Up/Down Arrows):** Corrupted at boot. Repaired in early investigation by patching the terminal input ring buffer.
* **Tab Autocompletion:** Unlocked after reconstructing the shell environment profile (`.bashrc` / `libreadline`).


* **Signal Traps (`Ctrl+C` / SIGINT):** Unlocked when repairing process management signal handlers prior to tackling runaway processes.


* **Diagnostic Feedback:** Hitting a locked shortcut triggers an explicit hardware advisory:
```text
[HARDWARE ADVISORY: Input driver corrupted. Missing libreadline hooks.]

```



---

## 4. Command Architecture & Bounded Flag Matrix

### 4.1 Diegetic Soft-Gating

Commands are never artificially blocked by arbitrary game locks. Instead, progression is gated through **in-world system state**:

* Binaries in `/usr/bin` may have permissions zeroed (`000`), requiring symbolic or numeric restoration.


* Utilities may reside on unmounted recovery partitions (`/mnt/recovery/bin/`).


* Corrupted `$PATH` variables require direct configuration file updates.
* Puzzles are gated behind state dependencies, password fragments, and daemon sockets rather than obscure syntax gating.

### 4.2 Supported Command Matrix

| Command | Supported Flags / Syntax | Primary Mechanical Purpose |
| --- | --- | --- |
| `pwd` | None | Verify active working directory.

 |
| `ls` | `-a`, `-l`, `-la`, `-al`, `-h` | Traversal, hidden file discovery, permission inspection.

 |
| `cd` | Relative paths, absolute paths, `..`, `~`, `-` | Filesystem navigation.

 |
| `cat` | File paths | Standard file reading and log dumping.

 |
| `head` | `-n <lines>` | Inspect header metadata and log origins.

 |
| `tail` | `-n <lines>`, `-f` (simulated event stream) | Inspect recent log entries and active events.

 |
| `grep` | `-i`, `-r` / `-R`, `-n`, `-v` | Filtering incident logs and identifying error traces.

 |
| `find` | `-name <pattern>`, `-type [f|d]` | Locating scattered system keys and recovery scripts.

 |
| `chmod` | Symbolic (`+x`, `-w`, `u+rwx`), Numeric (`644`, `755`, `700`, `777`) | Restoring utility execution permissions and locking configs.

 |
| `ps` | `aux`, `-ef` | Process table auditing and PID identification.

 |
| `kill` | `-9` (SIGKILL), `-15` (SIGTERM) | Halting hostile/runaway process daemons.

 |
| `ip` | `addr`, `link`, `route` | Identifying virtual network interfaces and subnet states.

 |
| `ss` | `-tulpn`, `-t`, `-u` | Auditing active listening sockets and ports.

 |
| `ping` | `-c <count>` | Verifying network connectivity across recovery gateways.

 |
| `sync` | None | Diegetic manual save-state flush to persistent storage.

 |
| `man` / `--help` | Valid command names | High-utility, diegetic summaries with practical examples.

 |
| `decrypt` | None (Fictional utility) | Analyzes the last `stderr` output to provide educational guidance. |

### 4.3 Pipeline & Stream Operations

* **Pipes (`|`):** Supports single-stage chaining (`cmd1 | cmd2`, e.g., `ps aux | grep phoenix` or `cat /var/log/syslog | grep error`).
* **Redirection (`>`, `>>`):** Supports standard output redirection and appending to files (e.g., `cat key.pub >> /etc/phoenix/authorized_keys`).

---

## 5. Pedagogical Architecture & Hint System

```
[Player Runs Malformed Command]
               │
               ▼
[Terminal Emits Authentic POSIX Error]
(e.g., "bash: cd: /var/log/auth.log: Not a directory")
               │
               ▼
[Player Investigates In-World Clues] ────► (Checks 'man', Notes, Logs)
               │
      (If Permanently Stuck)
               ▼
[Player Runs 'decrypt']
               │
               ▼
[Diegetic Diagnostic Output Emitted]
"[APOLLO-DIAGNOSTIC]: Target path is a file, not a directory. Use 'cat' to read."

```

### 5.1 Authentic POSIX Feedback

The terminal emulator renders standard POSIX/GNU error messages verbatim. The system avoids breaking immersion with intrusive out-of-character tutorial modals.

### 5.2 The `decrypt` Diagnostic Assistant

To assist beginners without breaking real-world command habits:

* The game includes a specialized diagnostic binary (`decrypt` / `apollo-diagnostics`).
* Running `decrypt` immediately after an error evaluates the last entry in the `stderr` buffer and prints a plain-language explanation and recovery hint.
* Styled distinctly with fictional terminal formatting to prevent players from expecting this utility on production Linux servers.

### 5.3 In-World Hint Discovery (*Outer Wilds* Model)

All systemic hints are embedded directly within the environment:

* Corrupted bash histories in `/home/operator/.bash_history` illustrating previous administrative commands.
* Post-it scratchpads (`TODO.txt`, `notes.md`) left in damaged user home directories.
* Diagnostic kernel messages broadcast to the TUI via simulated `wall` broadcasts.

### 5.4 "Take It to Linux" Transition Reference

Upon resolving major system milestones, players receive an optional, reference debrief detailing how the commands they used function on a live, real-world Linux installation.

---

## 6. Metroidvania Campaign Design & World State

```
+-------------------------------------------------------------------------+
|                    APOLLO SYSTEM RECOVERY PROGRESSION                   |
|                                                                         |
|  [Sector 0: Boot] ──────► [Sector 1: Home/Base] ───► [Sector 2: System Logs]
|  - pwd, ls, cd            - History Unlock           - grep, head, tail |
|                           - Tab Autocomplete         - /var/log/syslog  |
|                                                              │          |
|  [Sector 5: Subnet] ◄─── [Sector 4: Process Core] ◄──────────┘          |
|  - ip, ss, ping          - ps, kill, SIGINT                             |
|  - Socket Audit          - Runaway Malware                              |
|         │                                                               |
|         ▼                                                               |
|  [Sector 6: PHOENIX Restoration (Finale Synthesis)]                     |
|  - Permissions (chmod), Configuration Patching, Multi-Pipe Recovery    |
+-------------------------------------------------------------------------+

```

### 6.1 Continuous Workstation Map

* The entire game takes place on a unified, persistent machine (`APOLLO`).


* Progression is non-linear and event-driven: restoring a driver or gaining permission opens access to subdirectories (`/opt/phoenix/`, `/root/`, `/var/backups/`) encountered earlier in the campaign.


* World state is governed by an internal event flag registry (`SYSTEM_FLAGS`).

### 6.2 Major Milestone Breakdown

* **Milestone 0: Cold Boot (Orientation & Buffer Repair)**
* *Focus:* `pwd`, `ls`, `cd`, input buffer restoration.


* *Action:* Boot workstation, identify offline status, repair terminal ring buffer to unlock **Command History**.




* **Milestone 1: The Operator's Cache (Traversal & Shell Config)**
* *Focus:* `ls -a`, `cat`, relative paths.


* *Action:* Discover hidden dotfiles in home directory; restore `.bashrc` to unlock **Tab Autocompletion**.




* **Milestone 2: Forensic Log Analysis (Text Filtering)**
* *Focus:* `grep`, `head`, `tail`, `/var/log` navigation.


* *Action:* Filter extensive authentication logs to isolate malicious ingress timestamps and locate damaged binary paths.




* **Milestone 3: Recovery Partition Mounting (Filesystem Discovery)**
* *Focus:* `find`, `man`, path resolution.


* *Action:* Search unmounted volumes to locate backup copies of stripped system utilities.




* **Milestone 4: Security Integrity & Permissions (Executable Rights)**
* *Focus:* `chmod` (symbolic and numeric: `+x`, `755`).


* *Action:* Repair permissions on locked diagnostic utilities to make them executable.




* **Milestone 5: Runaway Mitigation (Process Signaling)**
* *Focus:* `ps aux`, `kill -9`, process signal handlers.


* *Action:* Repair signal handlers to unlock **`Ctrl+C` (SIGINT)**; identify and terminate runaway mining threads consuming CPU cycles.




* **Milestone 6: Network Uplink Diagnostic (Sockets & Routing)**
* *Focus:* `ip addr`, `ss -tulpn`, `ping`.


* *Action:* Bring virtual network interfaces online, audit open listener ports, and verify connectivity with remote gateway nodes.




* **Milestone 7: PHOENIX Restoration (Campaign Finale)**
* *Focus:* Full multi-tool synthesis, piping, configuration redirection.


* *Action:* Reconstruct main PHOENIX daemon configuration, set appropriate file rights, and launch the restoration service.





*(Note: Detailed puzzle dependency graphs, file manifests, and exact clue paths are scheduled for a dedicated mission design breakdown pass).*

---

## 7. Metagame Architecture & State Persistence

### 7.1 JSON Save-State Schema (`savegame.json`)

The game state serializes into a clean, human-readable JSON schema:

```json
{
  "version": "2.0.0",
  "timestamp": "2042-10-14T08:22:15Z",
  "player": {
    "current_directory": "/var/log",
    "unlocked_ergonomics": {
      "history": true,
      "autocomplete": true,
      "sigint": false
    }
  },
  "system_flags": {
    "BUFFER_REPAIRED": true,
    "BASHRC_RESTORED": true,
    "MALWARE_TERMINATED": false,
    "PHOENIX_ONLINE": false
  },
  "process_table": [
    {"pid": 1, "name": "systemd", "status": "running", "cpu": 0.0},
    {"pid": 104, "name": "sys_miner", "status": "running", "cpu": 98.2}
  ],
  "virtual_fs": {
    "/": {
      "type": "dir",
      "permissions": "755",
      "owner": "root"
    },
    "/etc/phoenix.conf": {
      "type": "file",
      "permissions": "644",
      "owner": "root",
      "content": "SERVICE_ENABLED=0\nPORT=8080"
    }
  }
}

```

### 7.2 Checkpoint & Persistence Mechanics

* **Autosave Engine:** State persists automatically whenever a major `SYSTEM_FLAGS` milestone changes.
* **Diegetic Manual Sync:** Running the standard `sync` command writes all in-memory buffers to `savegame.json`.


* **Replay & Fresh Runs:** Players can reset workstation `APOLLO` to its corrupted boot state to attempt clean incident runs.



---

## 8. Development Roadmap & MVP Specification

### 8.1 MVP Acceptance Criteria (Metroidvania Slice)

The MVP build is considered successful when a player can:

1. Launch the game in a standard desktop terminal via Python 3.


2. Navigate the virtual filesystem using `pwd`, `ls -a`, and `cd`.


3. Inspect files via `cat`, `head`, and `tail`.


4. Solve the initial buffer repair puzzle to unlock Up/Down arrow command history.
5. Solve the `.bashrc` recovery puzzle to unlock Tab autocompletion.
6. Trigger an authentic POSIX error and successfully resolve it using the `decrypt` tool.
7. Save and reload the mutated filesystem state cleanly via `savegame.json`.



### 8.2 Production Engineering Roadmap

```
Phase 1: Engine Foundation
├── TUI Input Loop (prompt_toolkit)
├── Lexer & AST Parser (shlex / bashlex)
├── In-Memory Virtual Tree & Process Table
└── JSON State Serializer

Phase 2: Investigation & Discovery Layer
├── Core Utilities (ls, cd, cat, head, tail, grep, find)
├── Ergonomic Driver Unlock Architecture
├── Diegetic 'decrypt' Diagnostic Engine
└── Sandbox Story Artifacts & Logs

Phase 3: Permissions & Stream Composition
├── Symbolic & Numeric chmod Handlers
├── Pipe (|) & Redirect (>, >>) Stream Processor
└── Metroidvania Backtracking Puzzle Chains

Phase 4: Systems Diagnostics & Networking
├── Process Table Controller (ps, kill, SIGINT)
├── Virtual Network Stack (ip, ss, ping)
└── System Broadcast & Event Trigger System

Phase 5: Campaign Finale & Production Polish
├── PHOENIX Orchestration Finale Puzzles
├── Take It to Linux Educational Reference Modules
└── Terminal Theme & Display Hardening

```

### 8.3 Post-Launch Expansion Concepts (Design Backlog)

* **Expansion 1: SYSADMIN** — User account administration (`useradd`, `sudo`), cron automation, systemd unit files, and package management.


* **Expansion 2: NETWORK OPS** — Routing table repairs, DNS query tracing, firewall rules (`iptables`/`nftables`), and remote SSH jumps.


* **Expansion 3: DEVOPS** — Local Git incident auditing, environment configuration variables, and container lifecycle simulation.


* **Expansion 4: SHELL AUTOMATION** — Scripting logic, variable expansion, conditional branching, and loop automation.



---

*End of Game Design Document (v2.0 Production Master)*

---