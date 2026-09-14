#!/usr/bin/env python3
"""Playtest Replay Regression Harness for Terminal Zero."""

import re
import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None

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

# Matches prompts from both osiris and legacy apollo transcripts
CMD_REGEX = re.compile(r"^(?:alice@osiris|alice@apollo):.*[$#]\s*(.+)$")


def create_engine():
    bus = EventBus()
    root_node = build_default_vfs()
    vfs = VirtualFilesystem(root_node)
    state = TerminalState(vfs, bus, ["home", "alice"])
    vfs.set_event_bus(bus)
    NarrativeSyncObserver(state, bus, vfs)
    return PipelineEngine(COMMAND_TABLE, bus, state=state, vfs=vfs)


def normalize_legacy_cmd(cmd: str) -> str:
    """Translates legacy apollo terminology from early playtests to osiris."""
    cmd = re.sub(r"\bapollo0\b", "osiris0", cmd)
    cmd = re.sub(r"\bapollo\b", "osiris", cmd)
    return cmd


def get_playtest_transcripts():
    playtests_dir = ROOT / "Playtests"
    if not playtests_dir.exists():
        return []
    return sorted(list(playtests_dir.glob("Playtest*.txt")) + list(playtests_dir.glob("Playtest*.ini")))


def test_playtest_regression():
    transcripts = get_playtest_transcripts()
    assert transcripts, "No playtest transcripts found in Playtests/"

    total_cmds = 0
    for path in transcripts:
        engine = create_engine()
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                match = CMD_REGEX.match(line.strip())
                if not match:
                    continue
                cmd = match.group(1).strip()
                if not cmd:
                    continue

                cmd = normalize_legacy_cmd(cmd)
                try:
                    engine.execute(cmd)
                except Exception as exc:
                    msg = f"Crash in {path.name}:{line_no} running {cmd!r}: {exc}"
                    if pytest:
                        pytest.fail(msg)
                    else:
                        raise AssertionError(msg) from exc

                assert engine.vfs.root is not None, f"VFS root collapsed in {path.name} after {cmd!r}"
                assert engine.state is not None, f"Engine state lost in {path.name} after {cmd!r}"
                total_cmds += 1

    return total_cmds


if __name__ == "__main__":
    print("[REPLAY] Running playtest regression harness across transcripts...")
    count = test_playtest_regression()
    print(f"[REPLAY] SUCCESS: Verified {count} recorded commands across transcripts with zero crashes!")
