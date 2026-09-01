import os
import sys
from terminal_zero.core.events import EventBus
from terminal_zero.core.vfs import VirtualFilesystem
from terminal_zero.core.state import CommandContext, TerminalState
from terminal_zero.core.persistence import load_game_state, register_autosave_handler
from terminal_zero.content.initial_vfs import build_default_vfs
from terminal_zero.content.debriefs import DebriefManager
from terminal_zero.commands import COMMAND_TABLE
from terminal_zero.engine.repl import TerminalShell


def main():
    bus = EventBus()
    reset_requested = any(arg in sys.argv for arg in ["--reset", "--new", "--fresh", "-r", "--restart"])
    if reset_requested and os.path.exists("savegame.json"):
        try:
            os.remove("savegame.json")
        except Exception:
            pass

    state = None if reset_requested else load_game_state("savegame.json", bus)
    if not state:
        root_node = build_default_vfs()
        vfs = VirtualFilesystem(root_node)
        state = TerminalState(vfs, bus, ["home", "alice"])
    else:
        vfs = state.vfs

    register_autosave_handler(bus, lambda: state)
    DebriefManager(bus)
    ctx = CommandContext(vfs, state, bus)

    shell = TerminalShell(ctx, COMMAND_TABLE)
    shell.run()


if __name__ == "__main__":
    main()
