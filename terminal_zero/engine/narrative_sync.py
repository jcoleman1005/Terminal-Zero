from terminal_zero.core.events import Event, EventBus
from terminal_zero.core.state import TerminalState
from terminal_zero.core.vfs import VirtualFilesystem
from terminal_zero.content.narrative import get_todo_content, get_incident_dossier


class NarrativeSyncObserver:
    def __init__(self, state: TerminalState, bus: EventBus, vfs: VirtualFilesystem):
        self.state = state
        self.bus = bus
        self.vfs = vfs

        self.bus.subscribe(self._on_event)
        self.sync_all()

    def sync_todo_and_dossier(self):
        todo_node, _ = self.vfs.get_node([], "/home/alice/TODO.txt")
        if todo_node:
            todo_node.content = get_todo_content(self.state.system_flags, self.state.discovered_clues)

        for dossier_path in ["/home/alice/diagnostics/INCIDENT_REPORT.log", "/home/alice/INCIDENT_REPORT.log"]:
            dossier_node, _ = self.vfs.get_node([], dossier_path)
            if dossier_node:
                dossier_node.content = get_incident_dossier(self.state.discovered_clues)

    def sync_phoenix_perms(self):
        if self.state.system_flags.get("LOGS_AUDITED") or self.state.system_flags.get("RECOVERY_LOCATED"):
            perms = "755"
        else:
            perms = "700"
        ph_node, _ = self.vfs.get_node([], "/opt/phoenix")
        if ph_node:
            ph_node.permissions = perms

    def sync_all(self):
        self.sync_todo_and_dossier()
        self.sync_phoenix_perms()

    def _on_event(self, event: Event):
        if event.type in ["flag_changed", "clue_discovered"]:
            self.sync_all()
        elif event.type == "command_executed":
            cmd = event.data.get("command", "")
            args = event.data.get("args", [])
            if cmd == "grep":
                args_str = " ".join(args).lower()
                has_breach_token = any(token in args_str for token in ["alert", "rogue", "breach"])
                has_auth_log = any("auth.log" in a.lower() for a in args)
                if has_breach_token and has_auth_log:
                    if not self.state.system_flags.get("LOGS_AUDITED", False):
                        self.state.system_flags["LOGS_AUDITED"] = True
                        self.bus.publish(Event("flag_changed", {"flag": "LOGS_AUDITED", "value": True}))
        elif event.type == "vfs_node_modified":
            path_parts = event.data.get("path", [])
            path_str = event.data.get("path_str", "")
            is_bashrc = (path_parts == ["home", "alice", ".bashrc"]) or (path_str == "/home/alice/.bashrc")
            if is_bashrc:
                content = event.data.get("content", "").strip()
                if content and not self.state.system_flags.get("BASHRC_RESTORED", False):
                    self.state.system_flags["BASHRC_RESTORED"] = True
                    self.state.unlocked_ergonomics["autocomplete"] = True
                    self.state.unlocked_ergonomics["tab_completion"] = True
                    self.bus.publish(Event("flag_changed", {"flag": "BASHRC_RESTORED", "value": True}))
