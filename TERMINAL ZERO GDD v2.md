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
| **Campaign Model** | *Systemic Pivot* | Converted episodic mission levels into a single, **continuous Metroidvania-style workstation map** (`OSIRIS`) with state flags, organic mounting, and environmental backtracking. Standardized network tooling on `ip` and `ss`.
|
| **Persistence Engine** | *Modification* | Replaced out-of-character `save`/`load` commands with automatic background checkpointing on state transitions and a diegetic `sync` command. Persists full virtual filesystem, process table, unlocks, and story flags to `savegame.json`.
|
| **MVP & Roadmap** | *Modification* | Redefined MVP around the continuous workstation slice and driver repairs. Formatted a 5-phase engineering roadmap and isolated expansions to conceptual-only status.
|
| **Incident Investigation & Tooling** | *Addition (v2.2)* | Renamed workstation from `APOLLO` to `OSIRIS` (with interface `osiris0` and diagnostic `osiris-diagnostics`). Added forensic triage mechanics (`triage_*`), discovered manuals inventory (`manuals`), debrief card vault (`fieldguide`), and fog-of-war checklist (`todo`).
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

The player assumes control of **`OSIRIS`**, a damaged local workstation running a degraded Linux environment. Through `OSIRIS`, the player must troubleshoot damaged subsystems, discover encrypted keys, and orchestrate the recovery of **`PHOENIX`**—a dormant, distributed emergency restoration network.

```
+-------------------------------------------------------------+
|                      WORKSTATION: OSIRIS                    |
|                                                             |
|  [Filesystem]         [Process Table]       [Network Stack] |
|  / (Root)             - PID 1 (init)        - lo (127.0.0.1)|
|  ├── /etc             - PID 104 (malware)   - osiris0 (down)|
|  ├── /var/log         - PID 500 (phoenix)   - Sockets (ss)  |
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
| `pwd` | None | Verify active working directory. |
| `ls` | `-a`, `-l`, `-la`, `-al`, `-h` | Traversal, hidden file discovery, permission inspection. |
| `ll` | Shortcut for `ls -la` | Quickly reveals permissions, owners, and hidden files. |
| `cd` | Relative paths, absolute paths, `..`, `~`, `-` | Filesystem navigation. |
| `cat` | File paths | Standard file reading and log dumping. |
| `head` | `-n <lines>` | Inspect header metadata and log origins. |
| `tail` | `-n <lines>`, `-f` (simulated event stream) | Inspect recent log entries and active events. |
| `grep` | `-i`, `-r` / `-R`, `-n`, `-v` | Filtering incident logs and identifying error traces. |
| `find` | `-name <pattern>`, `-type [f\|d]` | Locating scattered system keys and recovery scripts. |
| `chmod` | Symbolic (`+x`, `-w`, `u+rwx`), Numeric (`644`, `755`, `700`, `777`) | Restoring utility execution permissions and locking configs. |
| `ps` | `aux`, `-ef` | Process table auditing and PID identification. |
| `kill` | `-9` (SIGKILL), `-15` (SIGTERM) | Halting hostile/runaway process daemons. |
| `ip` | `addr`, `link`, `route` | Identifying virtual network interfaces and subnet states (`osiris0`). |
| `ss` | `-tulpn`, `-t`, `-u` | Auditing active listening sockets and ports. |
| `ping` | `-c <count>` | Verifying network connectivity across recovery gateways. |
| `append` | `append <file> "<content>"` | Helper for appending content (alternative to `>>`). |
| `tree` | `[path]` | Visual filesystem directory hierarchy overview. |
| `repair_buffer` | None (Diegetic recovery binary) | Calibrates TTY line discipline registers and unlocks command history. |
| `osiris-net` | None (Alias: `apollo-net`) | Queries `osiris0` interface state and gateway link reachability. |
| `phoenix_daemon` | `start`, `stop`, `status` (Alias: `phoenix_ctl`) | Restores and runs the emergency restoration cluster supervisor. |
| `taskctl` / `todo` | `todo`, `tasks`, `taskctl link` | In-game mission checklist with fog-of-war tracking. |
| `manuals` / `docs` | `manuals [name]` | Discovered field manuals, guides, and cheat sheets library. |
| `fieldguide` / `cards` | `fieldguide [card_id]` (Aliases: `debriefs`, `lore`) | Vault of real-world "Take It to Linux" system administration debrief cards. |
| `triage_*` | `triage_process`, `triage_sector`, `triage_interface`, `triage_service` | Audits and logs security breach leads into the incident dossier. |
| `sync` | None | Diegetic manual save-state flush to persistent storage. |
| `reboot` / `reset` | None | Restarts the workstation session from cold boot. |
| `man` / `--help` | Valid command names | High-utility, diegetic summaries with practical examples. |
| `decrypt` | None (Fictional utility; alias: `osiris-diagnostics`) | Analyzes the last `stderr` output to provide educational guidance. |

### 4.3 Pipeline & Stream Operations

* **Pipes (`|`):** Supports single-stage chaining (`cmd1 | cmd2`, e.g., `ps aux | grep phoenix` or `cat /var/log/syslog | grep error`).
* **Redirection (`>`, `>>`):** Supports standard output redirection and appending to files (e.g., `cat alice.bashrc > ~/.bashrc` or `cat key >> phoenix.conf`).

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
"[OSIRIS-DIAGNOSTIC]: Target path is a file, not a directory. Use 'cat' to read."

```

### 5.1 Authentic POSIX Feedback

The terminal emulator renders standard POSIX/GNU error messages verbatim. The system avoids breaking immersion with intrusive out-of-character tutorial modals.

### 5.2 The `decrypt` Diagnostic Assistant

To assist beginners without breaking real-world command habits:

* The game includes a specialized diagnostic binary (`decrypt` / `osiris-diagnostics`, aliased as `apollo-diagnostics`).
* Running `decrypt` immediately after an error evaluates the last entry in the `stderr` buffer and prints a plain-language explanation and recovery hint.
* Styled distinctly with fictional terminal formatting to prevent players from expecting this utility on production Linux servers.

### 5.3 In-World Hint Discovery (*Outer Wilds* Model)

All systemic hints are embedded directly within the environment:

* Corrupted bash profiles and manuals (`.HOW_TO_READ_LL.txt`, `.grep_juice`) explaining syntax and conventions.
* Post-it scratchpads (`NOTE_FROM_MORGAN.txt`) left in damaged user home and recovery directories.
* Diagnostic kernel messages broadcast to the TUI via simulated boot logs and kernel alerts.

### 5.4 "Take It to Linux" Transition Reference & Field Guide Vault

Upon resolving major system milestones, players receive an optional reference debrief detailing how the commands they used function on a live, real-world Linux installation.
* These cards are automatically preserved in the in-game `fieldguide` vault (accessible at any time via `fieldguide` or `cards`).
* Similarly, all recovered reference sheets are cataloged in the `manuals` command inventory.

---

## 6. Metroidvania Campaign Design & World State

```
+-------------------------------------------------------------------------+
|                    OSIRIS SYSTEM RECOVERY PROGRESSION                   |
|                                                                         |
|  [Sector 0: Boot] ──────► [Sector 1: Home/Base] ───► [Sector 2: System Logs]
|  - pwd, ls, cd            - History Unlock           - grep, head, tail |
|                           - Tab Autocomplete         - Triage Verification|
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

* The entire game takes place on a unified, persistent machine (`OSIRIS`).

* Progression is non-linear and event-driven: restoring a driver or gaining permission opens access to subdirectories (`/opt/phoenix/`, `/mnt/recovery/`, `/etc/network/`) encountered earlier in the campaign.

* World state is governed by an internal event flag registry (`SYSTEM_FLAGS`) and clue discovery table.

### 6.2 Major Campaign Phase Breakdown (Production Phases 0–6)

* **Phase 0: Cold Boot & Orientation (Buffer Repair)**
  * *Focus:* `pwd`, `ls`, `cat`, input buffer restoration.
  * *Action:* Boot workstation `OSIRIS`, inspect `diagnostics/BOOT_FAIL.log`, run maintenance utility `repair_buffer` to recalibrate TTY ring registers and unlock **Command History (Up/Down arrows)**.

* **Phase 1: The Operator's Cache (Traversal & Shell Config)**
  * *Focus:* `ls -a`, `ll`, `cd`, relative/absolute paths, output redirection (`>`).
  * *Action:* Discover hidden dotfiles in home directory, locate clean profile template in `/opt/backup/profiles/alice.bashrc`, redirect it to `/home/alice/.bashrc` to restore Readline bindings and unlock **Tab Autocompletion** and the `ll` shortcut.

* **Phase 2: Incident Log Forensics & Triage (Text Filtering & Dossier)**
  * *Focus:* `grep` (`-i`, `-v`), `head`, `tail`, piping (`|`), forensic triage commands.
  * *Action:* Filter extensive authentication logs in `/var/log/auth.log` to isolate security breach indicators. Log confirmed findings into the incident dossier via `triage_process`, `triage_sector`, `triage_interface`, and `triage_service` to unmask all 4 attack vectors.

* **Phase 3: Recovery Partition & Recursive Search (Search & Executable Rights)**
  * *Focus:* `find` (`-name`), `chmod` (`+x`, `755`), script execution (`./recovery.sh`).
  * *Action:* Traverse `/mnt/recovery`, locate stripped recovery tools and the PHOENIX cluster authorization key, restore executable permissions on `/mnt/recovery/bin/recovery.sh`, run the script to link signal traps and unlock the `find` utility across the system.

* **Phase 4: Runaway Mitigation & Process Control (Process Signaling)**
  * *Focus:* `ps aux`, `kill` (`-9`, `-15`).
  * *Action:* Audit the system process table to identify high-CPU runaway miner process (`sys_miner`, PID 104) deployed in `/tmp`, and issue unconditional `kill -9 104` to eliminate malware and liberate system resources.

* **Phase 5: Network Hardware & Gateway Uplink (Sockets & Routing)**
  * *Focus:* `ip addr`, `ip link set <dev> up`, `osiris-net`, `ss -tulpn`, `ping -c <count>`.
  * *Action:* Inspect `/etc/network/interfaces`, discover degraded interface `osiris0`, bring link state `UP`, audit network sockets, and verify gateway reachability (`ping -c 4 10.0.42.1`).

* **Phase 6: PHOENIX Restoration & Cluster Activation (Campaign Finale)**
  * *Focus:* Stream appending (`>>` / `append`), `chmod 644`, daemon supervisor management.
  * *Action:* Safely append recovered cluster authorization key from `/mnt/recovery/keys/phoenix.key` into `/etc/phoenix/phoenix.conf`, lock down secure permissions (`chmod 644`), and launch `phoenix_daemon start` on port 8080 to restore the emergency grid.

*(Note: In-game checklists and objectives are dynamically tracked via `taskctl` and `todo`, and collected reference debriefs are archived in `manuals` and `fieldguide`).*

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


* **Replay & Fresh Runs:** Players can reset workstation `OSIRIS` to its corrupted boot state to attempt clean incident runs.



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