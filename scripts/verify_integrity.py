#!/usr/bin/env python3
"""Automated structural integrity and build verification test suite for Terminal Zero."""

import py_compile
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def test_py_compile():
    print("[1/8] Testing Python byte-compilation across all source files...")
    sources = list((ROOT / "terminal_zero").glob("**/*.py"))
    sources.append(ROOT / "scripts" / "bundle.py")
    for src in sources:
        py_compile.compile(str(src), doraise=True)
    print(f"      OK: {len(sources)} source files compiled cleanly.")

def test_apollo_purge():
    print("[2/8] Verifying total elimination of legacy 'apollo' references in terminal_zero/...")
    matches = []
    for p in (ROOT / "terminal_zero").rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        for line_num, line in enumerate(text.splitlines(), start=1):
            if "apollo" in line.lower():
                matches.append((p.name, line_num, line.strip()))
    if matches:
        for m in matches:
            print(f"      FAIL: Found legacy reference in {m[0]}:{m[1]} -> {m[2]}")
        sys.exit(1)
    print("      OK: Zero occurrences of 'apollo' found in terminal_zero/.")

def test_core_decoupling():
    print("[3/8] Verifying core layer independence (no content.narrative imports)...")
    # Clean sys.modules test
    for mod in list(sys.modules.keys()):
        if mod.startswith("terminal_zero"):
            del sys.modules[mod]
    
    import terminal_zero.core.state
    import terminal_zero.core.persistence
    import terminal_zero.core.vfs
    
    assert "terminal_zero.content.narrative" not in sys.modules, (
        "Circular dependency detected: terminal_zero.content.narrative was loaded by core!"
    )
    print("      OK: core modules import with zero dependencies on content.narrative.")

def test_lifecycle_and_events():
    print("[4/8] Verifying silent boot lifecycle, VFS event bus, and NarrativeSyncObserver...")
    from terminal_zero.core.events import Event, EventBus
    from terminal_zero.core.vfs import VirtualFilesystem
    from terminal_zero.core.state import TerminalState, CommandContext
    from terminal_zero.content.initial_vfs import build_default_vfs
    from terminal_zero.engine.narrative_sync import NarrativeSyncObserver
    from terminal_zero.engine.pipeline import PipelineEngine
    from terminal_zero.commands import COMMAND_TABLE

    # 1. Silent boot
    bus = EventBus()
    root_node = build_default_vfs()
    vfs = VirtualFilesystem(root_node)
    assert vfs.bus is None, "VFS has an event bus prematurely attached during boot"

    # 2. State & post-boot wiring
    state = TerminalState(vfs, bus, ["home", "alice"])
    vfs.set_event_bus(bus)
    assert vfs.bus is bus, "VFS failed to bind event bus via set_event_bus()"

    # 3. Observer attach
    sync_obs = NarrativeSyncObserver(state, bus, vfs)

    # Initial state assertions
    ph_node, _ = vfs.get_node([], "/opt/phoenix")
    assert ph_node is not None, "/opt/phoenix directory missing"
    assert ph_node.permissions == "700", f"Initial /opt/phoenix perms should be 700, got {ph_node.permissions}"

    # 4. Stream Redirection to .bashrc -> triggers vfs_node_modified -> triggers BASHRC_RESTORED
    ctx = CommandContext(vfs, state, bus)
    engine = PipelineEngine(COMMAND_TABLE, bus)
    res = engine.run("cat /opt/backup/profiles/alice.bashrc > /home/alice/.bashrc", state)
    assert res.exit_code == 0, f"Redirection failed: {res.stderr}"
    assert state.system_flags.get("BASHRC_RESTORED") is True, "BASHRC_RESTORED flag was not set by vfs_node_modified"
    assert state.unlocked_ergonomics.get("autocomplete") is True, "Autocomplete was not unlocked"
    assert state.unlocked_ergonomics.get("tab_completion") is True, "Tab completion was not unlocked"

    # 5. TODO.txt dynamic update verification
    todo_node, _ = vfs.get_node([], "/home/alice/TODO.txt")
    assert todo_node is not None, "/home/alice/TODO.txt missing"
    assert "[x] PHASE 1: USER SHELL ENVIRONMENT" in todo_node.content, "TODO.txt content did not sync phase status"

    # 6. Flag changed -> dynamic /opt/phoenix permissions
    bus.publish(Event("flag_changed", {"flag": "LOGS_AUDITED", "value": True}))
    assert ph_node.permissions == "755", f"/opt/phoenix permissions should be 755 after LOGS_AUDITED, got {ph_node.permissions}"

    # 7. Clue discovered -> INCIDENT_REPORT.log sync
    bus.publish(Event("clue_discovered", {"clue_id": "ALERT_0x01"}))
    dossier_node, _ = vfs.get_node([], "/home/alice/diagnostics/INCIDENT_REPORT.log")
    assert dossier_node is not None, "INCIDENT_REPORT.log missing"
    assert "ALERT-0x01" in dossier_node.content, "Dossier content missing clue tag"

    print("      OK: Silent boot, VFS mutation events, and NarrativeSyncObserver verified successfully.")

def test_bundler_parity():
    print("[5/8] Verifying bundler parity and Prototype.txt generation...")
    import subprocess
    bundle_script = ROOT / "scripts" / "bundle.py"
    proc = subprocess.run([sys.executable, str(bundle_script)], capture_output=True, text=True)
    assert proc.returncode == 0, f"Bundler script failed: {proc.stderr}"
    assert "Bundled 16 modules into Prototype.txt" in proc.stdout, f"Unexpected bundle output: {proc.stdout}"

    prototype_file = ROOT / "Prototype.txt"
    assert prototype_file.exists(), "Prototype.txt does not exist"
    py_compile.compile(str(prototype_file), doraise=True)
    print("      OK: scripts/bundle.py bundled 16 modules; Prototype.txt compiles cleanly.")

def test_network_and_commands():
    print("[6/8] Verifying command table and osiris network isolation...")
    from terminal_zero.commands import COMMAND_TABLE
    assert "apollo-net" not in COMMAND_TABLE, "Legacy 'apollo-net' still present in COMMAND_TABLE"
    assert "apollo-diagnostics" not in COMMAND_TABLE, "Legacy 'apollo-diagnostics' still present in COMMAND_TABLE"
    assert "osiris-net" in COMMAND_TABLE, "'osiris-net' missing from COMMAND_TABLE"
    assert "osiris-diagnostics" in COMMAND_TABLE, "'osiris-diagnostics' missing from COMMAND_TABLE"
    assert "stty" in COMMAND_TABLE, "'stty' missing from COMMAND_TABLE"
    assert "rm" in COMMAND_TABLE, "'rm' missing from COMMAND_TABLE"
    assert "cp" in COMMAND_TABLE, "'cp' missing from COMMAND_TABLE"
    assert "touch" in COMMAND_TABLE, "'touch' missing from COMMAND_TABLE"
    assert "cluster_probe" in COMMAND_TABLE, "'cluster_probe' missing from COMMAND_TABLE"
    print("      OK: Command table accurately standardized with new POSIX and diegetic tools.")

def test_vertical_slice_milestones():
    print("[7/8] Verifying complete hardened vertical slice E2E milestones...")
    from tests.test_vertical_slice_e2e import create_engine, test_hardened_vertical_slice_e2e
    eng = create_engine()
    test_hardened_vertical_slice_e2e(eng)
    print("      OK: All 8 vertical slice milestones passed in end-to-end simulation.")

def test_backup_and_permission_suite():
    print("[8/8] Verifying .default backup templates and POSIX permission guardrails...")
    from tests.test_backup_and_permissions import create_engine, test_backup_and_permission_enforcement
    eng = create_engine()
    test_backup_and_permission_enforcement(eng)
    print("      OK: All 5 backup template & POSIX permission checks passed cleanly.")

def main():
    print("==================================================")
    print("TERMINAL ZERO // STRUCTURAL INTEGRITY VERIFICATION")
    print("==================================================")
    test_py_compile()
    test_apollo_purge()
    test_core_decoupling()
    test_lifecycle_and_events()
    test_bundler_parity()
    test_network_and_commands()
    test_vertical_slice_milestones()
    test_backup_and_permission_suite()
    print("==================================================")
    print("ALL STRUCTURAL INTEGRITY CHECKS PASSED (8/8)")
    print("==================================================")

if __name__ == "__main__":
    main()
