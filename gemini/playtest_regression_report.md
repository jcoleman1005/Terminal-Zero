# Playtest Replay & Engine Regression Report

**Project:** Terminal Zero  
**Version:** 2.2-PROD  
**Date:** September 12, 2026  
**Test Suite:** `tests/test_playtest_regression.py`  
**Evaluation Target:** 13 Historical Playtest Transcripts (`Playtests/`)  

---

## 1. Executive Summary

A continuous replay regression test harness was designed and executed against the **Terminal Zero** command pipeline. The test harness ingested all historical playtest logs recorded across early prototypes and recent hardened slices, extracting real human player commands and executing them against clean, headless virtual engine instances.

### Key Results
- **Total Playtests Evaluated:** 13 Transcripts
- **Total Commands Replayed:** 1,013 Commands
- **Unhandled Python Exceptions:** 0
- **Engine / VFS Crashes:** 0
- **Regression Pass Rate:** 100%

---

## 2. Transcript Evaluation Breakdown

| Transcript | Format | Commands Evaluated | Primary Gameplay Phase / Focus | Status |
| :--- | :---: | :---: | :--- | :---: |
| `Playtest1.txt` | `.txt` | 43 | Phase 0–1 Orientation, initial traversal | **PASS** |
| `Playtest2.txt` | `.txt` | 4 | Early boot abort / quick disconnect | **PASS** |
| `Playtest3.txt` | `.txt` | 57 | Exploration, `.bashrc` profile restore | **PASS** |
| `Playtest4.txt` | `.txt` | 57 | Traversal & dotfile discovery | **PASS** |
| `Playtest5.txt` | `.txt` | 53 | Session resets, error diagnostic tests | **PASS** |
| `Playtest6.txt` | `.txt` | 54 | Partition inspection & recovery tools | **PASS** |
| `Playtest7.txt` | `.txt` | 33 | Permission checks and file reading | **PASS** |
| `Playtest8.txt` | `.txt` | 123 | Extended log forensics & grep queries | **PASS** |
| `Playtest9.txt` | `.txt` | 91 | Forensic triage & incident dossier | **PASS** |
| `Playtest10.ini` | `.ini` | 102 | Process auditing & kill signaling | **PASS** |
| `Playtest11.ini` | `.ini` | 131 | Network link activation & routing | **PASS** |
| `Playtest12.txt` | `.txt` | 88 | Field manual indexing & manuals | **PASS** |
| `Playtest13.ini` | `.ini` | 177 | Full multi-phase playthrough & feedback notes | **PASS** |
| **TOTAL** | — | **1,013** | **All Campaign Phases & Edge Cases** | **100% PASS** |

---

## 3. Structural Findings & Architecture Hardening

### 3.1 Headless Decoupling of `get_boot_screen`
- **Issue Detected:** While replaying `Playtest5.txt:6` (`reset`), the command invoked `cmd_reboot()`, which previously imported `get_boot_screen` from `terminal_zero.engine.repl`. In headless environments or automated test runners without `prompt_toolkit`, this triggered an unnecessary `ModuleNotFoundError`.
- **Resolution:** `get_boot_screen()` was relocated to `terminal_zero.content.narrative` alongside sibling narrative formatters (`get_todo_content`, `get_incident_dossier`, `get_victory_screen`). Both `engine/repl.py` and `commands/diegetic.py` now import from `content.narrative`.
- **Outcome:** The engine can now execute complete system reboots and resets in 100% headless automated test suites without graphical or TUI library dependencies.

### 3.2 Legacy Token Normalization
- **Issue Detected:** Early playtests (`Playtest1` through `Playtest5`) used legacy workstation naming (`apollo` and `apollo0`).
- **Resolution:** A regex-based normalizer (`normalize_legacy_cmd`) was integrated into the test loop to map `\bapollo0\b` -> `osiris0` and `\bapollo\b` -> `osiris`.
- **Outcome:** Enables backwards-compatible regression testing across the entire project history while enforcing the current `OSIRIS` naming convention.

---

## 4. Playtester Behavior & Friction Analysis

Analysis of the 1,013 executed commands alongside `playtest_notes.txt` reveals recurring cognitive patterns and user friction points:

### 4.1 Non-Executable File Execution
- **Behavior:** Novice players frequently attempt to execute documentation or checklist files directly as commands (e.g., typing `TODO.txt` or `BOOT_FAIL.log` instead of `cat TODO.txt`).
- **Engine Response:** Accurately emits standard POSIX error: `cannot execute binary file: Exec format error` (exit code 126).
- **Pedagogical Impact:** Players who subsequently type `decrypt` receive immediate guidance: *"Cannot execute standard data file. Use 'cat' to read contents."*

### 4.2 Working Directory Misalignment
- **Behavior:** Players attempt `cat BOOT_FAIL.log` while standing in `/home/alice`, receiving `No such file or directory`.
- **Remediation Observed:** Players check `ls`, see `diagnostics/`, and navigate using `cd diagnostics`.

### 4.3 Process Supervisor Interlock
- **Behavior:** In Phase 4, players attempt to terminate the rogue miner worker (`kill -9 104`) before dealing with the supervisor process (`task_audit`, PID 102).
- **Engine Response:** Rejects the kill with an explicit warning: `supervisor (PID 102) immediately respawned worker`.
- **Resolution:** Forces players to think hierarchically about Linux process management.

### 4.4 Note-Taking During Play
- **Behavior:** Players heavily utilize the diegetic `note` and `feedback` commands (over 25 entries in `Playtest13.ini` and `playtest_notes.txt`).
- **Resilience:** The pipeline accepts multiline strings, unquoted freeform text, and nested punctuation without syntax errors.

---

## 5. Next Steps & Recommendations

1. **Continuous Integration (CI):** Add `python3 tests/test_playtest_regression.py` to pre-commit checks and automated build workflows alongside `scripts/verify_integrity.py`.
2. **Verbose Replay CLI Flag:** Add a `--summary` or `-v` flag to `test_playtest_regression.py` to optionally print per-transcript command tallies during manual developer runs.
3. **Future Playtest Archival:** Ensure newly recorded human playtests (`Playtest14.txt`, etc.) are deposited into `Playtests/` to automatically expand regression test coverage.
