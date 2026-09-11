#!/usr/bin/env python3
"""End-to-End test suite for the Terminal Zero Hardened Vertical Slice."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terminal_zero.core.events import EventBus
from terminal_zero.core.vfs import VirtualFilesystem
from terminal_zero.core.state import TerminalState
from terminal_zero.content.initial_vfs import build_default_vfs
from terminal_zero.engine.narrative_sync import NarrativeSyncObserver
from terminal_zero.engine.pipeline import PipelineEngine
from terminal_zero.commands import COMMAND_TABLE


def create_engine():
    bus = EventBus()
    root_node = build_default_vfs()
    vfs = VirtualFilesystem(root_node)
    state = TerminalState(vfs, bus, ["home", "alice"])
    vfs.set_event_bus(bus)
    NarrativeSyncObserver(state, bus, vfs)
    return PipelineEngine(COMMAND_TABLE, bus, state=state, vfs=vfs)


try:
    import pytest

    @pytest.fixture
    def engine():
        return create_engine()
except ImportError:
    pass


def test_hardened_vertical_slice_e2e(engine):
    # 1. Oracle Bypass Defense: cluster_probe must fail before log triage
    probe_early = engine.execute("cluster_probe")
    assert probe_early.exit_code == 1
    assert "Master triage bus offline" in probe_early.stderr

    # 2. Milestone 0: Buffer Recovery
    engine.execute("stty sane")
    assert engine.state.unlocked_ergonomics.get("history") is True
    assert engine.state.system_flags.get("BUFFER_REPAIRED") is True

    # 3. Milestone 1: Profile Restoration
    engine.execute("rm /home/alice/.bashrc.corrupt")
    assert engine.vfs.resolve_path(["home", "alice", ".bashrc.corrupt"]) is None
    engine.execute("cp /opt/backup/profiles/alice.bashrc /home/alice/.bashrc")
    assert engine.state.system_flags.get("BASHRC_RESTORED") is True
    assert engine.state.unlocked_ergonomics.get("autocomplete") is True

    # 4. Central Forensic Chokepoint: Informational grep triage
    engine.execute("head -n 6 /var/log/auth.log")
    engine.execute("grep -i \"ALERT\" /var/log/auth.log")
    assert engine.state.system_flags.get("LOGS_AUDITED") is True

    # cluster_probe now allowed to run, but must report 3 PENDING items
    probe_mid = engine.execute("cluster_probe")
    assert "PENDING" in probe_mid.stdout
    assert engine.state.system_flags.get("VERTICAL_SLICE_COMPLETE", False) is False

    # 5. Spoke A: Compute Triage
    # Attempting to kill worker (104) while supervisor (102) is running should be rejected
    respawn_res = engine.execute("kill -9 104")
    assert respawn_res.exit_code == 1
    assert "supervisor (PID 102) immediately respawned worker" in respawn_res.stderr
    assert any(p.pid == 104 for p in engine.state.process_table)

    engine.execute("kill 102")
    assert engine.vfs.resolve_path(["tmp", "audit_report.txt"]) is not None
    assert not any(p.pid == 102 for p in engine.state.process_table)

    engine.execute("kill 104")  # Trapped signal
    assert any(p.pid == 104 for p in engine.state.process_table)

    engine.execute("kill -9 104")  # SIGKILL
    assert not any(p.pid == 104 for p in engine.state.process_table)
    assert engine.state.system_flags.get("CPU_NORMAL") is True

    # 6. Spoke B: Storage & Signal Interlock
    find_res = engine.execute("find /mnt/recovery -name \"*.sh\" -o -name \"*.key\"")
    assert "/mnt/recovery/bin/recovery.sh" in find_res.stdout
    assert "/mnt/recovery/keys/phoenix.key" in find_res.stdout

    perm_denied = engine.execute("/mnt/recovery/bin/recovery.sh")
    assert perm_denied.exit_code == 126

    engine.execute("chmod +x /mnt/recovery/bin/recovery.sh")
    script_res = engine.execute("/mnt/recovery/bin/recovery.sh")
    assert script_res.exit_code == 0
    assert engine.state.unlocked_ergonomics.get("ctrl_c") is True

    # 7. Spoke C: Network Uplink
    ping_down = engine.execute("ping -c 4 10.0.42.1")
    assert ping_down.exit_code == 2

    engine.execute("ip link set osiris0 up")
    ping_up = engine.execute("ping -c 4 10.0.42.1")
    assert ping_up.exit_code == 0
    assert engine.state.system_flags.get("NETWORK_ONLINE") is True

    # 8. Convergence Gate: Final Evaluation
    final_probe = engine.execute("cluster_probe")
    assert final_probe.exit_code == 0
    assert "PENDING" not in final_probe.stdout
    assert "SUCCESS" in final_probe.stdout
    assert engine.state.system_flags.get("VERTICAL_SLICE_COMPLETE") is True
    assert "Alice... the telemetry cleared" in final_probe.stdout


if __name__ == "__main__":
    print("[E2E] Running test_hardened_vertical_slice_e2e standalone...")
    eng = create_engine()
    test_hardened_vertical_slice_e2e(eng)
    print("[E2E] SUCCESS: All 8 vertical slice milestones passed cleanly!")
