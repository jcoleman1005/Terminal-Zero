from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from terminal_zero.core.events import Event, EventBus
from terminal_zero.core.vfs import VirtualFilesystem


@dataclass
class ProcessEntry:
    pid: int
    name: str
    user: str = "root"
    status: str = "running"
    cpu: float = 0.0
    command: str = ""


class TerminalState:
    def __init__(self, vfs: VirtualFilesystem, event_bus: EventBus, initial_path: List[str]):
        self.vfs = vfs
        self.bus = event_bus
        self.current_path = initial_path
        self.env: Dict[str, str] = {
            "USER": "alice",
            "HOME": "/home/alice",
            "HOST": "apollo",
            "TERM": "xterm-256color",
            "PATH": "/bin:/usr/bin"
        }
        self.unlocked_ergonomics: Dict[str, bool] = {
            "history": False,
            "autocomplete": False,
            "sigint": False,
            "history_arrows": False,
            "tab_completion": False,
            "sigint_trap": False
        }
        self.system_flags: Dict[str, bool] = {
            "README_INSPECTED": False,
            "TODO_LINKED": False,
            "BUFFER_REPAIRED": False,
            "BASHRC_RESTORED": False,
            "LOGS_AUDITED": False,
            "MALWARE_TERMINATED": False,
            "NETWORK_ONLINE": False,
            "PHOENIX_ONLINE": False
        }
        self.discovered_clues: Dict[str, bool] = {
            "ALERT_0x01": False,
            "ALERT_0x02": False,
            "ALERT_0x03": False,
            "ALERT_0x04": False,
        }
        self.process_table: List[ProcessEntry] = [
            ProcessEntry(pid=1, name="systemd", user="root", cpu=0.1, command="/sbin/init"),
            ProcessEntry(pid=104, name="sys_miner", user="root", cpu=98.2, command="/tmp/sys_miner --stealth"),
            ProcessEntry(pid=210, name="sshd", user="root", cpu=0.0, command="/usr/sbin/sshd -D")
        ]
        self.network_interfaces: Dict[str, Dict[str, Any]] = {
            "lo": {"ip": "127.0.0.1/8", "state": "UP", "mac": "00:00:00:00:00:00"},
            "apollo0": {"ip": "10.0.42.15/24", "state": "DOWN", "mac": "52:54:00:12:34:56"}
        }
        # Initial state: only sshd listening (port 8080 binds dynamically when phoenix_daemon starts)
        self.listening_sockets: List[Dict[str, Any]] = [
            {"proto": "tcp", "local": "0.0.0.0:22", "peer": "0.0.0.0:*", "state": "LISTEN", "pid": 210, "proc": "sshd"}
        ]
        self.last_stderr: str = ""

        # Hook state observer for ergonomic flags synchronization
        self.bus.subscribe(self._on_event)

        # Update dynamic TODO.txt & INCIDENT_REPORT.log if present in VFS
        self._sync_todo()

        # Soft-gate /opt/phoenix based on initial system flags
        self._sync_phoenix_perms()

    def _sync_todo(self):
        try:
            from terminal_zero.content.narrative import get_todo_content, get_incident_dossier
            todo_node, _ = self.vfs.get_node([], "/home/alice/TODO.txt")
            if todo_node:
                todo_node.content = get_todo_content(self.system_flags, self.discovered_clues)
            
            dossier_node, _ = self.vfs.get_node([], "/home/alice/INCIDENT_REPORT.log")
            if dossier_node:
                dossier_node.content = get_incident_dossier(self.discovered_clues)
        except ImportError:
            pass

    def _sync_phoenix_perms(self):
        if self.system_flags.get("LOGS_AUDITED") or self.system_flags.get("RECOVERY_LOCATED"):
            ph_node, _ = self.vfs.get_node([], "/opt/phoenix")
            if ph_node:
                ph_node.permissions = "755"
        else:
            ph_node, _ = self.vfs.get_node([], "/opt/phoenix")
            if ph_node:
                ph_node.permissions = "700"

    def _on_event(self, event: Event):
        if event.type == "flag_changed":
            flag = event.data.get("flag")
            val = bool(event.data.get("value"))
            self.system_flags[flag] = val
            self._sync_todo()
            self._sync_phoenix_perms()
            if flag == "BUFFER_REPAIRED" and val:
                self.unlocked_ergonomics["history"] = True
                self.unlocked_ergonomics["history_arrows"] = True
            elif flag == "BASHRC_RESTORED" and val:
                self.unlocked_ergonomics["autocomplete"] = True
                self.unlocked_ergonomics["tab_completion"] = True
            elif (flag == "MALWARE_TERMINATED" or flag == "SIGINT_REPAIRED") and val:
                self.unlocked_ergonomics["sigint"] = True
                self.unlocked_ergonomics["sigint_trap"] = True
        elif event.type == "clue_discovered":
            clue_id = event.data.get("clue_id")
            if clue_id in self.discovered_clues:
                self.discovered_clues[clue_id] = True
            self._sync_todo()

    @property
    def cwd_str(self) -> str:
        if not self.current_path:
            return "/"
        return "/" + "/".join(self.current_path)


@dataclass
class CommandResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


@dataclass
class CommandContext:
    vfs: VirtualFilesystem
    state: TerminalState
    bus: EventBus
    stdin: str = ""

    def result_factory(self, stdout: str = "", stderr: str = "", exit_code: int = 0) -> CommandResult:
        return CommandResult(stdout=stdout, stderr=stderr, exit_code=exit_code)
