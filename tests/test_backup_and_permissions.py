#!/usr/bin/env python3
"""Automated verification suite for .default backup templates and POSIX permissions."""

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


def test_backup_and_permission_enforcement(engine):
    # 1. Verify alice cannot delete root-owned default templates
    res_rm = engine.execute("rm /mnt/recovery/bin/recovery.sh.default")
    assert res_rm.exit_code == 1
    assert "Permission denied" in res_rm.stderr
    assert engine.vfs.resolve_path(["mnt", "recovery", "bin", "recovery.sh.default"]) is not None

    # 2. Verify alice cannot chmod root-owned templates
    res_chmod = engine.execute("chmod 777 /mnt/recovery/bin/recovery.sh.default")
    assert res_chmod.exit_code == 1
    assert "Operation not permitted" in res_chmod.stderr

    # 3. Verify alice CAN chmod recovery.sh because she owns it (even if mode was 0000)
    target = engine.vfs.resolve_path(["mnt", "recovery", "bin", "recovery.sh"])
    assert target.owner == "alice"
    assert target.permissions == "0000"
    res_chmod_own = engine.execute("chmod +x /mnt/recovery/bin/recovery.sh")
    assert res_chmod_own.exit_code == 0
    assert int(target.permissions, 8) & 0o111

    # 4. Verify recovery via cp from .default when working file is accidentally removed
    engine.execute("rm /home/alice/.bashrc.corrupt")
    # Simulate accidental clobber of active file
    engine.execute("cp /home/alice/.bashrc.default /home/alice/.bashrc")
    restored = engine.vfs.resolve_path(["home", "alice", ".bashrc"])
    assert restored is not None
    assert restored.owner == "alice"
    assert "alias ll=" in restored.content

    # 5. Verify /etc/skel fallback accessibility
    skel = engine.vfs.resolve_path(["etc", "skel", ".bashrc"])
    assert skel is not None
    assert skel.owner == "root"
    res_skel_cp = engine.execute("cp /etc/skel/.bashrc /home/alice/.bashrc_from_skel")
    assert res_skel_cp.exit_code == 0
    assert engine.vfs.resolve_path(["home", "alice", ".bashrc_from_skel"]) is not None


if __name__ == "__main__":
    eng = create_engine()
    test_backup_and_permission_enforcement(eng)
    print("[TEST] test_backup_and_permission_enforcement PASSED!")
