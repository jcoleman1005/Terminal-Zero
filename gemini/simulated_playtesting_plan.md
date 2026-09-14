# Implementation Plan: Terminal Zero Playtesting Simulation Engine

This document provides a comprehensive review of **Terminal Zero** (v2.2-PROD) and specifies the technical design for a **Playtesting Simulation Engine**.

---

## 1. Game Review & Playtest Dynamics Analysis

### 1.1 Core Architecture & Philosophy
Terminal Zero is a **Terminal Metroidvania / Educational CLI Investigation** game built around an authentic POSIX command-line experience inside a simulated Linux workstation (`OSIRIS`, kernel 5.15/5.19).

- **Safety & Isolation:** Fully in-memory virtual filesystem (`VFSNode`, `VirtualFilesystem`), simulated process table, network sockets, and event bus (`EventBus`). Zero host commands are executed.
- **Pedagogy & Error Translation:** Standard POSIX stderr errors are returned by default (e.g., `bash: cd: /var/log/auth.log: Not a directory`). The diegetic `decrypt` command acts as an error buffer translator, parsing `last_stderr` and providing contextual plain-English remediation without breaking immersion.
- **Ergonomic Progression (Hybrid Unlocks):**
  - *Boot:* Character editing, backspace, left/right arrows active.
  - *History (Up/Down arrows):* Corrupted at boot; unlocked via `repair_buffer` or `stty sane`.
  - *Tab Autocompletion & `ll`:* Unlocked by recovering `/opt/backup/profiles/alice.bashrc` into `~/.bashrc`.
  - *Signal Traps (`Ctrl+C` / SIGINT):* Unlocked by executing `/mnt/recovery/bin/recovery.sh`.

```
================================================================================
                    OSIRIS SYSTEM RECOVERY DEPENDENCY GRAPH
================================================================================

 [Boot: /home/alice]
         │
         ├──► Phase 0: Ring Buffer Fault ──► repair_buffer / stty sane ──► [History Recall Active]
         │
         ├──► Phase 1: Missing Profile ──► cp /opt/backup/profiles/alice.bashrc ~/.bashrc ──► [Tab Autocomplete & ll Active]
         │
         └──► Phase 2: Log Forensics & Dossier ──► grep/tail /var/log/auth.log ──► [LOGS_AUDITED (4 Leads Unmasked)]
                                                               │
         ┌─────────────────────────────────────────────────────┴─────────────────────────────────────────────────────┐
         │                                                     │                                                     │
         ▼                                                     ▼                                                     ▼
 [Phase 3: Storage & Signals]                       [Phase 4: Compute Triage]                     [Phase 5: Network Uplink]
  find /mnt/recovery                                 ps aux                                        cat /etc/network/interfaces
  chmod +x /mnt/recovery/bin/recovery.sh             kill 102 (task_audit supervisor)             ip link set osiris0 up
  ./recovery.sh                                      kill -9 104 (sys_miner worker)                ping -c 4 10.0.42.1
  └──► [SIGINT / Ctrl+C Active]                      └──► [CPU Normal @ 0%]                        └──► [Network Link Active]
         │                                                     │                                                     │
         └─────────────────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                                               │
                                                               ▼
                                       [Phase 6: Cluster Synthesis & Gateway Activation]
                                        cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf
                                        chmod 644 /etc/phoenix/phoenix.conf
                                        phoenix_daemon start / cluster_probe
                                        └──► [MISSION COMPLETE: PHOENIX ONLINE]
```

### 1.2 Historical Playtest Analysis (Playtest1–13 & Notes)
Reviewing the 13 historical playtests in `Playtests/` and `playtest_notes.txt` reveals clear behavioural patterns, friction points, and recurring mental models:

1. **The "Execution vs Cat" Confusion:** Novice players frequently try to execute data files directly (e.g., `TODO.txt` -> `cannot execute binary file: Exec format error` or `BOOT_FAIL.log`).
2. **Directory Context Blindness:** Players run `cat BOOT_FAIL.log` from `/home/alice` without realizing it is inside `diagnostics/`, prompting them to use `decrypt` or check `ls`.
3. **Supervisor Respawn Loop (Phase 4):** Players run `kill 104` or `kill -9 104` without realizing PID 102 (`task_audit`) is supervising PID 104 (`sys_miner`), causing it to instantly respawn until the supervisor is terminated first.
4. **Kill Argument Confusion:** Players attempt `kill sys_miner` (by name) instead of numeric PID (`kill -9 104`), requiring `decrypt` to remind them about numeric PIDs.
5. **Stream Appending vs Overwriting (Phase 6):** Risk of players using `>` instead of `>>` when transferring `phoenix.key` to `phoenix.conf`, clobbering existing configuration entries.
6. **Self-Documentation & In-Game Notes:** Real playtesters actively use `note <text>` or `feedback <text>` to document their confusion, feature requests, or eureka moments into `playtest_notes.txt`.

---

## 2. Playtesting Simulation Engine Specification

The proposed tool is an automated, headless **Playtesting Simulation Engine** that can simulate diverse player cognitive profiles, run Monte Carlo playtests, benchmark friction and difficulty curves, replay historical human logs, and export telemetry and feedback notes.

```
+-----------------------------------------------------------------------------------------+
|                                PLAYTEST SIMULATION ENGINE                               |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [Historical Transcripts]            [Simulated Agent Personas]                         |
|  Playtest1.txt .. Playtest13.ini     • Novice (curious, errors, decrypt-dependent)      |
|           │                          • Intermediate (sysadmin, pipes, unix idioms)      |
|           │                          • Explorer (100% lore, all manuals, tree)          |
|           │                          • Speedrunner (optimal path, regression check)     |
|           │                          • Chaos Monkey (fuzzing, syntax edge-cases)        |
|           ▼                                       │                                     |
|   (Transcript Parser)                             ▼                                     |
|           │                             (Cognitive Loop: Observe ──► Decide ──► Act)     |
|           │                                       │                                     |
|           └───────────────────┬───────────────────┘                                     |
|                               ▼                                                         |
|                  [PipelineEngine & Virtual State]                                       |
|                               │                                                         |
|                               ▼                                                         |
|                  [Telemetry & Friction Collector]                                       |
|                  • Step counts & time-per-phase                                         |
|                  • Error hotspot heatmap & retry loops                                  |
|                  • Clue / manual discovery rates                                        |
|                  • Softlock / deadlock alerts                                           |
|                               │                                                         |
|         ┌─────────────────────┼─────────────────────────┐                               |
|         ▼                     ▼                         ▼                               |
| [Playtest Logs]        [Simulated Notes]        [Analytics Report]                      |
| Playtests/Sim_*.txt    playtest_notes.txt       Markdown / CLI Summary                  |
+-----------------------------------------------------------------------------------------+
```

### 2.1 Player Personas / Cognitive Models
Each persona is parameterized by curiosity, patience, Linux skill, typo probability, and hint reliance:

| Persona | Linux Skill | Typo / Error Rate | Decrypt / Manual Reliance | Exploration Behavior | Typical Blunders |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Novice** | Low | Medium-High (20–30%) | High (calls `decrypt` on error, checks `TODO.txt`) | Stays near current directory, relies on guided cues | Tries executing text files, `kill <name>`, forgets flags |
| **Intermediate** | High | Low (5%) | Low (prefers Unix tools like `man`, `ps aux`, `grep`) | Direct, searches system via `tree` and `/var/log` | Misses game-specific supervisor logic on first try |
| **Explorer** | Medium-High | Low | High (reads every `.txt`, `.log`, `.md`) | Exhaustive tree traversal, checks `manuals`, `fieldguide` | Wanders into late-game directories before early phases |
| **Speedrunner** | Expert | 0% | None (pure golden path) | Minimal path traversal | Tests regressions and optimal execution speed |
| **Chaos Monkey** | Adversarial | High | Dynamic | Random invalid commands, quotes, permission tampering | Tests game stability, softlock prevention, error formatting |

### 2.2 Cognitive Loop Architecture
The simulation runs headlessly against `PipelineEngine` and `TerminalState` using a discrete perception-action loop:
1. **Perceive:** Receive stdout, stderr, exit code, current directory, and unlocked flags.
2. **Update Memory:** Extract actionable facts from output (e.g. reading `BOOT_FAIL.log` adds `"repair_buffer"` to known candidate actions; reading `auth.log` extracts clue signatures).
3. **Check Frustration:** If the agent fails or spins in loops for $N$ turns ($N > \text{patience}$), trigger a simulated note entry (e.g., `note "I'm lost in /var/log trying to find the process ID"`).
4. **Decide Action:** Match active phase directives with known goals, persona traits, and available commands.
5. **Act:** Issue the raw command string to `PipelineEngine`.

### 2.3 Historical Transcript Replay Engine
To detect regressions across codebase revisions, the simulator includes a replayer that parses past playtest transcripts (`Playtest1.txt` .. `Playtest13.ini`), extracts player prompts (`alice@apollo:...$ <cmd>` or `alice@osiris:...$ <cmd>`), feeds them into `PipelineEngine`, and compares resulting exits and state mutations.

---

## 3. User Review Required

> [!IMPORTANT]
> **Decisions for User Review:**
> 1. **Simulator Code Location:** We propose placing the core simulator package in `terminal_zero/simulator/` (with a CLI entry script at `scripts/simulate_playtest.py`). This keeps the package organized and allows importing simulator helpers in automated test suites without contaminating production runtime.
> 2. **Playtest Output Location:** Should simulated playtest transcripts be written to `Playtests/Simulated_Playtest_<timestamp>.txt` or a separate subfolder like `Playtests/simulated/`?
> 3. **Feedback Note Appending:** The simulator can emit realistic simulated playtest notes. Should it append directly to the existing `playtest_notes.txt`, or write to `Playtests/simulated_notes.txt` to keep human playtester notes isolated?

---

## 4. Proposed File Changes

### Component: Playtest Simulator Engine (`terminal_zero/simulator/`)

#### [NEW] `terminal_zero/simulator/__init__.py`
Exports public simulator API (`SimulatedPlayer`, `SimulationRunner`, `PersonaConfig`, `TranscriptReplayer`, `TelemetryCollector`).

#### [NEW] `terminal_zero/simulator/personas.py`
Defines cognitive configuration dataclasses and persona factory functions:
- `PersonaConfig`: `name`, `linux_skill`, `exploration_weight`, `patience_limit`, `typo_rate`, `decrypt_reliance`, `preferred_tools`.
- Preset personas: `NOVICE`, `INTERMEDIATE`, `EXPLORER`, `SPEEDRUNNER`, `CHAOS`.

#### [NEW] `terminal_zero/simulator/agent.py`
Implements `SimulatedPlayer`:
- Working memory: known files, known binaries, discovered clues, goal hierarchy.
- Heuristic action planner: selects next logical step based on current phase and persona heuristics.
- Action noise generator: injects typos, improper syntax, or missing arguments according to persona error rates.
- Frustration monitor: emits `note` / `feedback` commands when stuck.

#### [NEW] `terminal_zero/simulator/telemetry.py`
Implements `TelemetryCollector`:
- Records command history, timestamps, exit codes, stderr traces.
- Computes phase transition timings and step counts.
- Generates error heatmaps and identifies friction hotspots.
- Detects softlocks (e.g., deleted critical files or missing tools with zero chance of recovery).

#### [NEW] `terminal_zero/simulator/replay.py`
Implements `TranscriptReplayer`:
- Regex parser for `Playtest*.txt` and `Playtest*.ini` logs.
- Replays sequential commands through `PipelineEngine`.
- Generates diff reports comparing historical behavior with current engine execution.

#### [NEW] `terminal_zero/simulator/reporter.py`
Formats simulation metrics into:
- Visual terminal dashboard (ASCII tables, phase completion funnels).
- Markdown report artifacts for game balance reviews.

---

### Component: CLI Entry Point & Tooling (`scripts/`)

#### [NEW] `scripts/simulate_playtest.py`
Standalone CLI utility with arguments:
```bash
python3 scripts/simulate_playtest.py --persona novice --runs 5 --report
python3 scripts/simulate_playtest.py --replay Playtests/Playtest13.ini
python3 scripts/simulate_playtest.py --all-personas --runs 20 --output-dir Playtests/simulated/
```

---

### Component: Test Suite (`tests/`)

#### [NEW] `tests/test_playtest_simulator.py`
Automated test suite verifying:
1. Deterministic simulation with fixed RNG seeds.
2. Speedrunner persona successfully solves Phase 0–6 in minimal steps.
3. Novice persona uses `decrypt` upon errors and eventually recovers.
4. Historical transcript replay parses and runs `Playtest13.ini` without crashes.
5. Telemetry collector accurately flags friction points and phase progression.

---

## 5. Verification Plan

### Automated Tests
1. **Source Code Integrity:**
   ```bash
   python3 scripts/verify_integrity.py
   ```
   Ensures byte-compilation passes, no forbidden legacy strings exist, and core decoupling is maintained.
2. **Simulator Unit & Integration Tests:**
   ```bash
   python3 -m unittest tests/test_playtest_simulator.py
   ```
3. **End-to-End Simulation Smoke Test:**
   ```bash
   python3 scripts/simulate_playtest.py --persona speedrunner --runs 1
   python3 scripts/simulate_playtest.py --persona novice --runs 1 --seed 42
   ```
4. **Historical Playtest Replay:**
   ```bash
   python3 scripts/simulate_playtest.py --replay Playtests/Playtest13.ini
   ```

### Manual Verification
- Review the generated simulation log format against `Playtests/Playtest13.ini` to ensure visual and structural parity.
- Inspect the generated telemetry report for friction bottlenecks and softlock alerts.
