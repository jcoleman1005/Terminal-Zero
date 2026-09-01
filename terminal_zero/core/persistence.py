import datetime
import json
import os
from typing import Any, Dict, Optional
from terminal_zero.core.events import Event, EventBus
from terminal_zero.core.vfs import VFSNode, VirtualFilesystem
from terminal_zero.core.state import ProcessEntry, TerminalState


def serialize_vfs_node(node: VFSNode) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {
        "type": node.type,
        "permissions": node.permissions,
        "owner": node.owner,
    }
    if node.is_file():
        serialized["content"] = node.content if node.content is not None else ""
    elif node.is_dir():
        serialized["children"] = {
            name: serialize_vfs_node(child) for name, child in node.children.items()
        }
    return serialized


def deserialize_vfs_node(data: Dict[str, Any]) -> VFSNode:
    node = VFSNode(
        type=data.get("type", "file"),
        permissions=data.get("permissions", "644"),
        owner=data.get("owner", "root"),
        content=data.get("content", None)
    )
    if node.is_dir() and "children" in data:
        node.children = {
            name: deserialize_vfs_node(child_data)
            for name, child_data in data["children"].items()
        }
    return node


def save_game_state(state: TerminalState, filepath: str = "savegame.json") -> None:
    # Ensure ergonomics aliases are synchronized
    ergo = dict(state.unlocked_ergonomics)
    hist = ergo.get("history", False) or ergo.get("history_arrows", False)
    auto = ergo.get("autocomplete", False) or ergo.get("tab_completion", False)
    sig = ergo.get("sigint", False) or ergo.get("sigint_trap", False)
    
    ergo["history"] = hist
    ergo["history_arrows"] = hist
    ergo["autocomplete"] = auto
    ergo["tab_completion"] = auto
    ergo["sigint"] = sig
    ergo["sigint_trap"] = sig

    payload = {
        "version": "2.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "player": {
            "current_directory": state.cwd_str,
            "env": state.env,
            "unlocked_ergonomics": ergo
        },
        "system_flags": state.system_flags,
        "discovered_clues": getattr(state, "discovered_clues", {}),
        "process_table": [
            {
                "pid": p.pid,
                "name": p.name,
                "user": p.user,
                "status": p.status,
                "cpu": p.cpu,
                "command": p.command
            }
            for p in state.process_table
        ],
        "network": {
            "interfaces": state.network_interfaces,
            "listening_sockets": state.listening_sockets
        },
        "virtual_fs": serialize_vfs_node(state.vfs.root)
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_game_state(filepath: str = "savegame.json", bus: Optional[EventBus] = None) -> Optional[TerminalState]:
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    event_bus = bus or EventBus()
    root_node = deserialize_vfs_node(data["virtual_fs"])
    vfs = VirtualFilesystem(root_node)

    raw_cwd = data.get("player", {}).get("current_directory", "/home/alice")
    cwd_parts = [p for p in raw_cwd.split("/") if p]

    state = TerminalState(vfs, event_bus, cwd_parts)
    state.env = data.get("player", {}).get("env", state.env)
    
    loaded_ergo = data.get("player", {}).get("unlocked_ergonomics", {})
    hist = bool(loaded_ergo.get("history") or loaded_ergo.get("history_arrows"))
    auto = bool(loaded_ergo.get("autocomplete") or loaded_ergo.get("tab_completion"))
    sig = bool(loaded_ergo.get("sigint") or loaded_ergo.get("sigint_trap"))

    state.unlocked_ergonomics = {
        "history": hist,
        "history_arrows": hist,
        "autocomplete": auto,
        "tab_completion": auto,
        "sigint": sig,
        "sigint_trap": sig
    }

    state.system_flags = data.get("system_flags", state.system_flags)
    if "discovered_clues" in data:
        state.discovered_clues = data["discovered_clues"]

    try:
        from terminal_zero.content.narrative import get_todo_content, get_incident_dossier
        todo_node, _ = state.vfs.get_node([], "/home/alice/TODO.txt")
        if todo_node:
            todo_node.content = get_todo_content(state.system_flags, state.discovered_clues)

        dossier_node, _ = state.vfs.get_node([], "/home/alice/INCIDENT_REPORT.log")
        if dossier_node:
            dossier_node.content = get_incident_dossier(state.discovered_clues)
    except ImportError:
        pass

    if state.system_flags.get("LOGS_AUDITED") or state.system_flags.get("RECOVERY_LOCATED"):
        ph_node, _ = state.vfs.get_node([], "/opt/phoenix")
        if ph_node:
            ph_node.permissions = "755"
    else:
        ph_node, _ = state.vfs.get_node([], "/opt/phoenix")
        if ph_node:
            ph_node.permissions = "700"

    loaded_processes = []
    for p_data in data.get("process_table", []):
        loaded_processes.append(
            ProcessEntry(
                pid=p_data["pid"],
                name=p_data["name"],
                user=p_data.get("user", "root"),
                status=p_data.get("status", "running"),
                cpu=p_data.get("cpu", 0.0),
                command=p_data.get("command", "")
            )
        )
    state.process_table = loaded_processes

    if "network" in data:
        state.network_interfaces = data["network"].get("interfaces", state.network_interfaces)
        state.listening_sockets = data["network"].get("listening_sockets", state.listening_sockets)

    return state


def register_autosave_handler(bus: EventBus, get_state):
    def on_event(event: Event):
        if event.type in ["flag_changed", "clue_discovered"]:
            state = get_state()
            if state:
                save_game_state(state, "savegame.json")
    bus.subscribe(on_event)
