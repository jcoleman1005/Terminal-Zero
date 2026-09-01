from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import datetime
import fnmatch
import json
import os
from pathlib import Path
import re
import shlex
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style

# =====================================================================
# 1. CORE EVENT BUS
# =====================================================================

@dataclass
class Event:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)

class EventBus:
    def __init__(self):
        self._listeners = []

    def subscribe(self, callback):
        self._listeners.append(callback)

    def publish(self, event: Event):
        for listener in list(self._listeners):
            listener(event)


# =====================================================================
# 2. POSIX VIRTUAL FILESYSTEM & PROCESS LAYER
# =====================================================================

@dataclass
class VFSNode:
    type: str  # "dir" or "file"
    permissions: str = "755"
    owner: str = "root"
    content: Optional[str] = None
    children: Dict[str, "VFSNode"] = field(default_factory=dict)

    def is_dir(self) -> bool:
        return self.type == "dir"

    def is_file(self) -> bool:
        return self.type == "file"


class VirtualFilesystem:
    def __init__(self, root_node: VFSNode):
        self.root = root_node

    def resolve_path(self, path_parts: List[str]) -> Optional[VFSNode]:
        current = self.root
        for part in path_parts:
            if not current.is_dir():
                return None
            if part not in current.children:
                return None
            current = current.children[part]
        return current

    def get_node(self, current_cwd: List[str], target_path: str) -> Tuple[Optional[VFSNode], List[str]]:
        if not target_path or target_path == ".":
            return self.resolve_path(current_cwd), current_cwd
        
        parts = target_path.split("/")
        if target_path.startswith("/"):
            resolved_parts: List[str] = []
        else:
            resolved_parts = list(current_cwd)

        for part in parts:
            if not part or part == ".":
                continue
            elif part == "..":
                if resolved_parts:
                    resolved_parts.pop()
            elif part == "~":
                resolved_parts = ["home", "alice"]
            else:
                resolved_parts.append(part)

        node = self.resolve_path(resolved_parts)
        return node, resolved_parts

    def write_file(self, current_cwd: List[str], target_path: str, content: str, append: bool = False, owner: str = "root") -> Tuple[bool, str]:
        node, resolved_path = self.get_node(current_cwd, target_path)
        if node:
            if node.is_dir():
                return False, f"{target_path}: Is a directory"
            if node.permissions == "000" or node.permissions.startswith("4"):
                return False, f"{target_path}: Permission denied"
            if append:
                node.content = (node.content or "") + content
            else:
                node.content = content
            return True, ""

        if "/" in target_path:
            parent_path, filename = target_path.rsplit("/", 1)
            if not parent_path:
                parent_path = "/"
        else:
            parent_path, filename = ".", target_path

        if not filename:
            return False, f"{target_path}: Invalid filename"

        parent_node, _ = self.get_node(current_cwd, parent_path)
        if not parent_node or not parent_node.is_dir():
            return False, f"{target_path}: No such file or directory"

        if parent_node.permissions == "000":
            return False, f"{target_path}: Permission denied"

        new_node = VFSNode(type="file", permissions="644", owner=owner, content=content)
        parent_node.children[filename] = new_node
        return True, ""

    def walk(self, current_cwd: List[str], target_path: str = ".") -> List[Tuple[str, VFSNode, str]]:
        """
        Recursively walks the VFS starting from target_path.
        Returns a list of tuples: (display_path, node, filename).
        """
        start_node, resolved_path = self.get_node(current_cwd, target_path)
        if not start_node:
            return []

        results: List[Tuple[str, VFSNode, str]] = []
        base_display = target_path if target_path != "." else "."
        base_name = target_path.split("/")[-1] if target_path != "." else "."

        def _recurse(node: VFSNode, curr_display: str, name: str):
            results.append((curr_display, node, name))
            if node.is_dir():
                for child_name, child_node in sorted(node.children.items()):
                    sub_display = f"{curr_display}/{child_name}" if curr_display != "/" else f"/{child_name}"
                    _recurse(child_node, sub_display, child_name)

        _recurse(start_node, base_display, base_name)
        return results


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
            "BUFFER_REPAIRED": False,
            "BASHRC_RESTORED": False,
            "MALWARE_TERMINATED": False,
            "NETWORK_ONLINE": False,
            "PHOENIX_ONLINE": False
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
        self.listening_sockets: List[Dict[str, Any]] = [
            {"proto": "tcp", "local": "0.0.0.0:22", "peer": "0.0.0.0:*", "state": "LISTEN", "pid": 210, "proc": "sshd"},
            {"proto": "tcp", "local": "127.0.0.1:8080", "peer": "0.0.0.0:*", "state": "LISTEN", "pid": 500, "proc": "phoenix_daemon"}
        ]
        self.last_stderr: str = ""

        # Hook state observer for ergonomic flags synchronization
        self.bus.subscribe(self._on_event)

    def _on_event(self, event: Event):
        if event.type == "flag_changed":
            flag = event.data.get("flag")
            val = bool(event.data.get("value"))
            self.system_flags[flag] = val
            if flag == "BUFFER_REPAIRED" and val:
                self.unlocked_ergonomics["history"] = True
                self.unlocked_ergonomics["history_arrows"] = True
            elif flag == "BASHRC_RESTORED" and val:
                self.unlocked_ergonomics["autocomplete"] = True
                self.unlocked_ergonomics["tab_completion"] = True
            elif (flag == "MALWARE_TERMINATED" or flag == "SIGINT_REPAIRED") and val:
                self.unlocked_ergonomics["sigint"] = True
                self.unlocked_ergonomics["sigint_trap"] = True

    @property
    def cwd_str(self) -> str:
        if not self.current_path:
            return "/"
        return "/" + "/".join(self.current_path)


# =====================================================================
# 3. DIEGETIC ENVIRONMENT INITIALIZER
# =====================================================================

def build_default_vfs() -> VFSNode:
    root = VFSNode(type="dir", permissions="755", owner="root")

    def add_dir(path: str, perms: str = "755", owner: str = "root") -> VFSNode:
        parts = [p for p in path.split("/") if p]
        curr = root
        for p in parts:
            if p not in curr.children:
                curr.children[p] = VFSNode(type="dir", permissions=perms, owner=owner)
            curr = curr.children[p]
        return curr

    def add_file(path: str, content: str, perms: str = "644", owner: str = "root") -> VFSNode:
        parts = [p for p in path.split("/") if p]
        parent_parts = parts[:-1]
        filename = parts[-1]
        parent = root
        for p in parent_parts:
            if p not in parent.children:
                parent.children[p] = VFSNode(type="dir", permissions="755", owner=owner)
            parent = parent.children[p]
        node = VFSNode(type="file", permissions=perms, owner=owner, content=content)
        parent.children[filename] = node
        return node

    # Standard POSIX & FHS Structure
    add_dir("/bin")
    add_dir("/usr/bin")
    add_dir("/var/log")
    add_dir("/etc")
    add_dir("/mnt/recovery/bin")
    add_dir("/opt/phoenix/recovery")
    add_dir("/opt/phoenix/config")
    add_dir("/home/alice/notes")

    # Binaries (Standard in /bin)
    for b in [
        "cat", "cd", "echo", "exit", "ls", "pwd", "sync", "decrypt", "apollo-diagnostics",
        "chmod", "man", "ps", "kill", "ip", "ss", "ping", "head", "tail", "grep", "find",
        "repair_buffer", "phoenix_ctl", "phoenix_daemon"
    ]:
        add_file(f"/bin/{b}", "ELF 64-bit LSB executable", perms="755")

    # Soft-Gated & Diegetic Tool Binaries
    add_file("/opt/phoenix/recovery/tree", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/grep", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/find", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/recovery.sh", "#!/bin/bash\necho 'Restoring core nodes...'", perms="755")
    add_file("/opt/phoenix/phoenix_daemon", "ELF 64-bit LSB executable [PHOENIX-DAEMON v2.5]", perms="755")

    # Recovery Partition Binaries (Permissions zeroed - need chmod)
    add_file("/mnt/recovery/bin/apollo-net", "ELF 64-bit LSB executable [APOLLO-NET v1.0]", perms="000")
    add_file("/mnt/recovery/bin/repair_buffer", "ELF 64-bit LSB executable [REPAIR-BUFFER v1.2]", perms="000")
    add_file("/mnt/recovery/bin/phoenix_ctl", "ELF 64-bit LSB executable [PHOENIX-CTL v2.0]", perms="000")
    add_file("/mnt/recovery/bin/recovery-tool", "ELF 64-bit LSB executable [RECOVERY-TOOL v2.1]", perms="000")

    # Environmental Lore, Configs & Clue Nodes
    add_file(
        "/opt/phoenix/phoenix.conf",
        "# PHOENIX EMERGENCY RESTORATION DAEMON CONFIG\nSERVICE_ENABLED=1\nLISTEN_PORT=8080\nGATEWAY_IP=10.0.42.1\nRECOVERY_KEY=0x7F_PHOENIX_INIT_2042\n",
        perms="644"
    )
    add_file(
        "/opt/phoenix/config/phoenix.conf",
        "# PHOENIX EMERGENCY RESTORATION DAEMON CONFIG\nSERVICE_ENABLED=1\nLISTEN_PORT=8080\nGATEWAY_IP=10.0.42.1\nRECOVERY_KEY=0x7F_PHOENIX_INIT_2042\n",
        perms="644"
    )
    add_file(
        "/home/alice/.bashrc",
        "# Workstation Shell Configuration\n# Corrupted ring-buffer hooks detected.\nexport PATH=$PATH:/opt/phoenix/recovery:/mnt/recovery/bin\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/.bash_history",
        "ps aux | grep miner\nkill -9 104\nip link set apollo0 up\nping -c 4 10.0.42.1\nchmod +x /mnt/recovery/bin/apollo-net\n/opt/phoenix/phoenix_daemon --sync\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/TODO.txt",
        "=== OPERATOR RECOVERY SCRATCHPAD ===\n1. [x] Terminal line buffer patched.\n2. [x] Shell config (.bashrc) restored.\n3. [ ] Audit running processes - runaway miner consuming CPU (check ps / kill).\n4. [ ] Check recovery partition in /mnt/recovery/bin/ (permissions damaged).\n5. [ ] Bring network uplink (apollo0) online and verify gateway (10.0.42.1).\n6. [ ] Reconfigure and restore PHOENIX daemon in /opt/phoenix/.\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/readme.txt",
        "APOLLO WORKSTATION LOGON\n[SYSTEM ADVISORY]: Shell degraded. Diagnostics available via 'decrypt'.\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/notes/mapping_tool.txt",
        "UTILITY RECOVERY NOTE:\nVisual hierarchy utility 'tree' preserved under /opt/phoenix/recovery/tree\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/notes/sysadmin_notes.txt",
        "SYSADMIN LOG - RECOVERY PROTOCOLS:\n1. Use 'grep' to search error streams.\n2. Ensure recovery binaries have execution permissions via 'chmod'.\n3. Bring interfaces up using 'ip link set <dev> up'.\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/var/log/syslog",
        "03:40:01 apollo systemd[1]: Starting System Logging Service...\n03:40:05 apollo kernel: [    0.000000] Linux version 5.15.0-apollo (gcc 11.2.0)\n03:40:12 apollo kernel: [SECURITY FAULT] Interface apollo0 link state degraded: DOWN\n03:41:00 apollo sys_miner[104]: CPU threshold exceeded: 98.2% allocation on core 0\n03:42:19 apollo systemd[1]: phoenix-sync.service: Main process exited, code=killed, status=9/KILL\n03:42:19 apollo systemd[1]: phoenix-sync.service: Failed with result 'signal'.\n",
        perms="644"
    )
    add_file(
        "/var/log/auth.log",
        "03:38:10 apollo sshd[204]: Invalid user operator from 192.168.1.105 port 44218\n03:38:12 apollo sshd[204]: Failed password for invalid user operator from 192.168.1.105 port 44218 ssh2\n03:39:01 apollo sshd[208]: Accepted password for alice from 127.0.0.1 port 51220 ssh2\n03:39:45 apollo sudo: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/systemctl status\n",
        perms="644"
    )
    add_file(
        "/var/log/system.log",
        "03:40:12 apollo kernel: eth0 link down\n03:42:19 apollo systemd: phoenix-sync terminated\n",
        perms="644"
    )

    return root


# =====================================================================
# 4. COMMAND CONTEXT & RESULT SCHEMAS & UTILITIES
# =====================================================================

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


def cmd_tree(ctx: Any, args: List[str]) -> Any:
    # Retained as an in-world discoverable POSIX utility
    start_node = ctx.vfs.resolve_path(ctx.state.current_path)
    if not start_node or not start_node.is_dir():
        return ctx.result_factory(stderr="tree: error reading directory\n", exit_code=1)

    lines = [ctx.state.cwd_str]

    def recurse_tree(node: VFSNode, prefix: str = ""):
        keys = sorted([k for k in node.children.keys() if not k.startswith(".")])
        for idx, key in enumerate(keys):
            child = node.children[key]
            connector = "└── " if idx == len(keys) - 1 else "├── "
            lines.append(f"{prefix}{connector}{key}")
            if child.is_dir():
                next_prefix = prefix + ("    " if idx == len(keys) - 1 else "│   ")
                recurse_tree(child, next_prefix)

    recurse_tree(start_node)
    return ctx.result_factory(stdout="\n".join(lines) + "\n")


# =====================================================================
# STREAM & INSPECTION UTILITIES (cat, head, tail, grep, find, echo)
# =====================================================================

def cmd_echo(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "echo", "args": args}))
    return ctx.result_factory(stdout=" ".join(args) + "\n")


def cmd_cat(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cat", "args": args}))
    if not args:
        if ctx.stdin:
            return ctx.result_factory(stdout=ctx.stdin)
        return ctx.result_factory(stderr="cat: missing file operand\n", exit_code=1)

    output = []
    for filepath in args:
        node, _ = ctx.vfs.get_node(ctx.state.current_path, filepath)
        if not node:
            return ctx.result_factory(stderr=f"cat: {filepath}: No such file or directory\n", exit_code=1)
        if node.is_dir():
            return ctx.result_factory(stderr=f"cat: {filepath}: Is a directory\n", exit_code=1)
        output.append(node.content if node.content is not None else "")

    return ctx.result_factory(stdout="".join(output))


def cmd_head(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "head", "args": args}))
    lines_count = 10
    file_targets = []
    idx = 0
    while idx < len(args):
        if args[idx] == "-n":
            if idx + 1 >= len(args) or not args[idx + 1].isdigit():
                return ctx.result_factory(stderr="head: option requires an integer line count -- 'n'\n", exit_code=1)
            lines_count = int(args[idx + 1])
            idx += 2
        elif args[idx].startswith("-n"):
            val = args[idx][2:]
            if not val.isdigit():
                return ctx.result_factory(stderr="head: invalid line count\n", exit_code=1)
            lines_count = int(val)
            idx += 1
        else:
            file_targets.append(args[idx])
            idx += 1

    if not file_targets:
        if ctx.stdin:
            selected = ctx.stdin.splitlines(keepends=True)[:lines_count]
            return ctx.result_factory(stdout="".join(selected))
        return ctx.result_factory(stderr="head: missing file operand\n", exit_code=1)

    output = []
    for filepath in file_targets:
        node, _ = ctx.vfs.get_node(ctx.state.current_path, filepath)
        if not node:
            return ctx.result_factory(stderr=f"head: cannot open '{filepath}': No such file or directory\n", exit_code=1)
        if node.is_dir():
            return ctx.result_factory(stderr=f"head: error reading '{filepath}': Is a directory\n", exit_code=1)
        lines = (node.content or "").splitlines(keepends=True)[:lines_count]
        output.append("".join(lines))

    return ctx.result_factory(stdout="".join(output))


def cmd_tail(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "tail", "args": args}))
    lines_count = 10
    follow_mode = False
    file_targets = []
    idx = 0
    while idx < len(args):
        if args[idx] == "-f":
            follow_mode = True
            idx += 1
        elif args[idx] == "-n":
            if idx + 1 >= len(args) or not args[idx + 1].isdigit():
                return ctx.result_factory(stderr="tail: option requires an integer line count -- 'n'\n", exit_code=1)
            lines_count = int(args[idx + 1])
            idx += 2
        elif args[idx].startswith("-n"):
            val = args[idx][2:]
            if not val.isdigit():
                return ctx.result_factory(stderr="tail: invalid line count\n", exit_code=1)
            lines_count = int(val)
            idx += 1
        else:
            file_targets.append(args[idx])
            idx += 1

    def generate_simulated_stream() -> str:
        net_online = ctx.state.system_flags.get("NETWORK_ONLINE", False)
        malware_dead = ctx.state.system_flags.get("MALWARE_TERMINATED", False)
        phoenix_online = ctx.state.system_flags.get("PHOENIX_ONLINE", False)

        stream_lines = [
            "[LOG STREAM ACTIVE - Press Ctrl+C to abort]",
            "[STREAM ACTIVE - Press Ctrl+C to exit]"
        ]
        if net_online:
            stream_lines.append("03:45:01 apollo kernel: [NETWORK] Interface apollo0 link state UP - carrier 1000Mbps")
            stream_lines.append("03:45:01 apollo kernel: [SECURITY] Interface apollo0 link state change detected")
        else:
            stream_lines.append("03:45:01 apollo kernel: [SECURITY] Interface apollo0 link state degraded: DOWN")

        if malware_dead:
            stream_lines.append("03:45:02 apollo systemd[1]: Process 104 (sys_miner) terminated - CPU utilization normalized (1.2%)")
        else:
            stream_lines.append("03:45:02 apollo sys_miner[104]: CPU allocation 98.2% on core 0 - hash rate 42.1 MH/s")

        if phoenix_online:
            stream_lines.append("03:45:02 apollo phoenix_daemon[500]: Listening for restoration heartbeat on 127.0.0.1:8080")
            stream_lines.append("03:45:05 apollo systemd[1]: Reached target Phoenix Recovery Subsystem (Online).")
            stream_lines.append("03:45:05 apollo systemd[1]: Reached target Network (Online).")
        else:
            stream_lines.append("03:45:05 apollo systemd[1]: phoenix-sync.service: Service offline. Waiting for operator dispatch.")

        return "\n".join(stream_lines) + "\n"

    if not file_targets:
        if ctx.stdin:
            selected = ctx.stdin.splitlines(keepends=True)[-lines_count:]
            output = "".join(selected)
            if follow_mode:
                output += generate_simulated_stream()
            return ctx.result_factory(stdout=output)
        return ctx.result_factory(stderr="tail: missing file operand\n", exit_code=1)

    output = []
    for filepath in file_targets:
        node, _ = ctx.vfs.get_node(ctx.state.current_path, filepath)
        if not node:
            return ctx.result_factory(stderr=f"tail: cannot open '{filepath}': No such file or directory\n", exit_code=1)
        if node.is_dir():
            return ctx.result_factory(stderr=f"tail: error reading '{filepath}': Is a directory\n", exit_code=1)
        lines = (node.content or "").splitlines(keepends=True)[-lines_count:]
        output.append("".join(lines))

    result_text = "".join(output)
    if follow_mode:
        result_text += generate_simulated_stream()

    return ctx.result_factory(stdout=result_text)


def cmd_grep(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "grep", "args": args}))
    if not args:
        return ctx.result_factory(stderr="Usage: grep [OPTION]... PATTERNS [FILE]...\n", exit_code=2)

    ignore_case = False
    invert_match = False
    line_number = False
    recursive = False
    pattern: Optional[str] = None
    files: List[str] = []

    for arg in args:
        if arg.startswith("-") and pattern is None and arg != "-":
            if "i" in arg: ignore_case = True
            if "v" in arg: invert_match = True
            if "n" in arg: line_number = True
            if "r" in arg or "R" in arg: recursive = True
        elif pattern is None:
            pattern = arg
        else:
            files.append(arg)

    if pattern is None:
        return ctx.result_factory(stderr="grep: missing pattern\n", exit_code=2)

    regex_flags = re.IGNORECASE if ignore_case else 0
    try:
        matcher = re.compile(pattern, regex_flags)
    except re.error:
        matcher = re.compile(re.escape(pattern), regex_flags)

    def evaluate_text(text: str, filename_prefix: str = "") -> List[str]:
        results = []
        for line_idx, line in enumerate(text.splitlines(), start=1):
            matched = bool(matcher.search(line))
            if matched ^ invert_match:
                prefix = ""
                if filename_prefix:
                    prefix += f"{filename_prefix}:"
                if line_number:
                    prefix += f"{line_idx}:"
                results.append(f"{prefix}{line}")
        return results

    if not files:
        if ctx.stdin:
            matched_lines = evaluate_text(ctx.stdin)
            return ctx.result_factory(
                stdout="\n".join(matched_lines) + ("\n" if matched_lines else ""),
                exit_code=0 if matched_lines else 1
            )
        return ctx.result_factory(stderr="grep: missing file operand\n", exit_code=2)

    matched_lines = []
    for target in files:
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, target)
        if not node:
            return ctx.result_factory(stderr=f"grep: {target}: No such file or directory\n", exit_code=2)

        if node.is_dir():
            if not recursive:
                return ctx.result_factory(stderr=f"grep: {target}: Is a directory\n", exit_code=2)
            
            def recurse_grep(dir_node: VFSNode, cur_p: List[str]):
                for name, child in sorted(dir_node.children.items()):
                    child_p = cur_p + [name]
                    rel_p = "/".join(child_p)
                    if child.is_file():
                        matched_lines.extend(evaluate_text(child.content or "", rel_p))
                    elif child.is_dir():
                        recurse_grep(child, child_p)

            recurse_grep(node, resolved_path)
        else:
            display_tag = target if len(files) > 1 else ""
            matched_lines.extend(evaluate_text(node.content or "", display_tag))

    return ctx.result_factory(
        stdout="\n".join(matched_lines) + ("\n" if matched_lines else ""),
        exit_code=0 if matched_lines else 1
    )


def cmd_find(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "find", "args": args}))
    search_path = "."
    pattern: Optional[str] = None
    target_type: Optional[str] = None  # "f" or "d"

    idx = 0
    if args and not args[0].startswith("-"):
        search_path = args[0]
        idx = 1

    while idx < len(args):
        if args[idx] == "-name":
            if idx + 1 >= len(args):
                return ctx.result_factory(stderr="find: missing argument to `-name'\n", exit_code=1)
            pattern = args[idx + 1].strip('"').strip("'")
            idx += 2
        elif args[idx] == "-type":
            if idx + 1 >= len(args):
                return ctx.result_factory(stderr="find: missing argument to `-type'\n", exit_code=1)
            target_type = args[idx + 1]
            idx += 2
        else:
            return ctx.result_factory(stderr=f"find: unknown predicate `{args[idx]}'\n", exit_code=1)

    start_node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, search_path)
    if not start_node:
        return ctx.result_factory(stderr=f"find: ‘{search_path}’: No such file or directory\n", exit_code=1)

    matches = []

    def recurse_find(node: VFSNode, current_str_path: str, filename: str):
        type_match = True
        if target_type == "f" and not node.is_file(): type_match = False
        if target_type == "d" and not node.is_dir(): type_match = False

        name_match = True
        if pattern:
            name_match = fnmatch.fnmatch(filename, pattern)

        if type_match and name_match:
            matches.append(current_str_path)

        if node.is_dir():
            for child_name, child_node in sorted(node.children.items()):
                sub_path = f"{current_str_path}/{child_name}" if current_str_path != "/" else f"/{child_name}"
                recurse_find(child_node, sub_path, child_name)

    base_display = search_path if search_path != "." else "."
    base_name = search_path.split("/")[-1] if search_path != "." else "."
    recurse_find(start_node, base_display, base_name)

    return ctx.result_factory(stdout="\n".join(matches) + ("\n" if matches else ""))


# =====================================================================
# DIEGETIC ADVISORY ENGINE (decrypt / apollo-diagnostics)
# =====================================================================

def cmd_decrypt(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "decrypt", "args": args}))
    last_err = ctx.state.last_stderr.strip()

    if not last_err:
        return ctx.result_factory(
            stdout="[APOLLO-DIAGNOSTIC]: No recent hardware or kernel fault recorded in buffer.\n"
        )

    diag = "[APOLLO-DIAGNOSTIC]: System anomaly detected."
    
    if "No such file or directory" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x1A - PATH NOT FOUND]\n"
            "Target node does not exist in the active directory tree.\n"
            "Action: Run 'ls' or 'pwd' to verify path coordinates before addressing target."
        )
    elif "Is a directory" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x1B - ILLEGAL NODE TYPE]\n"
            "Target path resolves to a directory node, but the requested binary requires a file stream.\n"
            "Action: Use 'cd' to traverse or 'ls' to inspect contents."
        )
    elif "Not a directory" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x1C - INVALID TRAVERSAL]\n"
            "Cannot traverse into a standard data file.\n"
            "Action: Use 'cat', 'head', or 'tail' to read file contents."
        )
    elif "Permission denied" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x2E - ACCESS RESTRICTED]\n"
            "Node execution or read/write bits are disabled.\n"
            "Action: Use 'chmod +x <target>' or 'chmod 755 <target>' to elevate node permissions."
        )
    elif "Network is unreachable" in last_err or "network unreachable" in last_err.lower():
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x3D - NETWORK OFFLINE]\n"
            "Virtual network interface link state is DOWN.\n"
            "Action: Run 'ip link set apollo0 up' to activate the network adapter and verify routing."
        )
    elif "No such process" in last_err or "invalid signal specification" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x5E - PROCESS ANOMALY]\n"
            "Process ID not active or signal invalid.\n"
            "Action: Run 'ps aux' to audit active process table before issuing 'kill -9 <PID>'."
        )
    elif "command not found" in last_err.lower():
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x4F - BINARY UNREGISTERED]\n"
            "Executable not located in standard search paths ($PATH).\n"
            "Action: Check /opt/phoenix/recovery or /mnt/recovery/bin, or inspect $PATH settings."
        )
    elif any(k in last_err.lower() for k in ["missing file operand", "missing pattern", "missing argument", "option requires", "invalid line count", "invalid count", "invalid mode"]):
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x05 - ARITY MISMATCH]\n"
            "Command invoked without mandatory arguments or with malformed options.\n"
            "Action: Run 'man <command>' to inspect supported syntax."
        )
    else:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x99 - GENERAL EXCEPTION]\n"
            "Subsystem failure registered in execution pipeline.\n"
            "Action: Consult system logs in /var/log/syslog or inspect command manual via 'man'."
        )

    output = (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ APOLLO RECOVERY DAEMON v2.4 — ERROR BUFFER TRANSLATION   │\n"
        "└──────────────────────────────────────────────────────────┘\n"
        f"SOURCE FAULT: {last_err}\n"
        f"{diag}\n"
    )
    return ctx.result_factory(stdout=output)


# =====================================================================
# NAVIGATION & DIRECTORY UTILITIES (pwd, cd, ls)
# =====================================================================

def cmd_pwd(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "pwd"}))
    return ctx.result_factory(stdout=ctx.state.cwd_str + "\n")


def cmd_cd(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cd", "args": args}))
    if len(args) > 1:
        return ctx.result_factory(stderr="bash: cd: too many arguments\n", exit_code=1)

    target_dir = args[0] if args else "~"
    target_node, resolved_parts = ctx.vfs.get_node(ctx.state.current_path, target_dir)

    if not target_node:
        return ctx.result_factory(stderr=f"bash: cd: {target_dir}: No such file or directory\n", exit_code=1)
    if not target_node.is_dir():
        return ctx.result_factory(stderr=f"bash: cd: {target_dir}: Not a directory\n", exit_code=1)

    ctx.state.current_path = resolved_parts
    return ctx.result_factory()


def cmd_ls(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ls", "args": args}))
    show_all = False
    long_format = False
    targets = []

    for arg in args:
        if arg.startswith("-"):
            if "a" in arg: show_all = True
            if "l" in arg: long_format = True
        else:
            targets.append(arg)

    if not targets:
        targets = ["."]

    output_blocks = []
    for target in targets:
        node, _ = ctx.vfs.get_node(ctx.state.current_path, target)
        if not node:
            return ctx.result_factory(stderr=f"ls: cannot access '{target}': No such file or directory\n", exit_code=2)

        if node.is_file():
            if long_format:
                output_blocks.append(f"-rwxr-xr-x 1 {node.owner} {node.owner} 4096 {target}")
            else:
                output_blocks.append(target)
            continue

        entries = sorted(node.children.keys())
        if show_all:
            entries = [".", ".."] + entries

        rendered = []
        for name in entries:
            if not show_all and name.startswith("."):
                continue
            if long_format:
                if name in [".", ".."]:
                    child_type = "d"
                    perms = "rwxr-xr-x"
                    owner = "root"
                else:
                    child = node.children[name]
                    child_type = "d" if child.is_dir() else "-"
                    perms = "rwxr-xr-x" if child.permissions == "755" else "rw-r--r--"
                    owner = child.owner
                rendered.append(f"{child_type}{perms} 1 {owner} {owner} 4096 {name}")
            else:
                rendered.append(name)

        if len(targets) > 1:
            output_blocks.append(f"{target}:\n" + "  ".join(rendered))
        else:
            joiner = "\n" if long_format else "  "
            output_blocks.append(joiner.join(rendered))

    return ctx.result_factory(stdout="\n".join(output_blocks) + "\n" if output_blocks else "")


# =====================================================================
# PERMISSIONS & SYSTEM UTILITIES (chmod, man, ps, kill, ip, ss, ping)
# =====================================================================

def cmd_chmod(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "chmod", "args": args}))
    if len(args) < 2:
        return ctx.result_factory(stderr="chmod: missing operand\n", exit_code=1)

    mode_str = args[0]
    target_paths = args[1:]

    for target in target_paths:
        node, _ = ctx.vfs.get_node(ctx.state.current_path, target)
        if not node:
            return ctx.result_factory(stderr=f"chmod: cannot access '{target}': No such file or directory\n", exit_code=1)

        # Numeric mode support (e.g. 755, 644, 700, 777)
        if mode_str.isdigit() and len(mode_str) == 3:
            node.permissions = mode_str
        # Symbolic mode support (+x, -x, u+x, etc.)
        elif "+x" in mode_str:
            node.permissions = "755"
        elif "-x" in mode_str:
            node.permissions = "644"
        else:
            return ctx.result_factory(stderr=f"chmod: invalid mode: '{mode_str}'\n", exit_code=1)

        # Diegetic event triggers for recovery partition binaries
        if "repair_buffer" in target and ("+x" in mode_str or mode_str in ["755", "777", "700"]):
            ctx.state.system_flags["BUFFER_REPAIRED"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "BUFFER_REPAIRED", "value": True}))
        elif ".bashrc" in target:
            ctx.state.system_flags["BASHRC_RESTORED"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "BASHRC_RESTORED", "value": True}))

    return ctx.result_factory()


# =====================================================================
# PROCESS MANAGEMENT SUITE (ps, kill)
# =====================================================================

def cmd_ps(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ps", "args": args}))
    header = "USER       PID %CPU COMMAND\n"
    lines = []
    for proc in ctx.state.process_table:
        if proc.status == "running":
            cmd_str = proc.command if proc.command else proc.name
            lines.append(f"{proc.user:<8} {proc.pid:>5} {proc.cpu:>4.1f} {cmd_str}")

    output = header + "\n".join(lines) + ("\n" if lines else "")
    return ctx.result_factory(stdout=output)


def cmd_kill(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "kill", "args": args}))
    if not args:
        return ctx.result_factory(stderr="kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ...\n", exit_code=1)

    sig = 15
    pid_idx = 0

    if args[0].startswith("-"):
        arg0 = args[0]
        if arg0 in ["-9", "-SIGKILL", "-KILL"]:
            sig = 9
            pid_idx = 1
        elif arg0 in ["-15", "-SIGTERM", "-TERM"]:
            sig = 15
            pid_idx = 1
        elif arg0 == "-s" and len(args) > 1:
            sig_spec = args[1].upper()
            if sig_spec in ["9", "KILL", "SIGKILL"]:
                sig = 9
            elif sig_spec in ["15", "TERM", "SIGTERM"]:
                sig = 15
            else:
                sig = 15
            pid_idx = 2
        elif arg0[1:].isdigit():
            sig = int(arg0[1:])
            pid_idx = 1
        else:
            return ctx.result_factory(stderr=f"kill: {arg0}: invalid signal specification\n", exit_code=1)

    if pid_idx >= len(args):
        return ctx.result_factory(stderr="kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ...\n", exit_code=1)

    pid_str = args[pid_idx]
    if not pid_str.isdigit():
        return ctx.result_factory(stderr=f"kill: {pid_str}: arguments must be process or job IDs\n", exit_code=1)

    pid = int(pid_str)
    target_proc = None
    for p in ctx.state.process_table:
        if p.pid == pid and p.status == "running":
            target_proc = p
            break

    if not target_proc:
        return ctx.result_factory(stderr=f"kill: ({pid}) - No such process\n", exit_code=1)

    proc_name = target_proc.name
    ctx.state.process_table = [p for p in ctx.state.process_table if p.pid != pid]

    if (pid == 104 or proc_name == "sys_miner") and sig in [9, 15]:
        ctx.state.system_flags["MALWARE_TERMINATED"] = True
        ctx.bus.publish(Event("flag_changed", {"flag": "MALWARE_TERMINATED", "value": True}))

    return ctx.result_factory(stdout=f"Process {pid} ({proc_name}) terminated by signal {sig}.\n")


# =====================================================================
# NETWORK OPERATIONS SUITE (ip, ss, ping)
# =====================================================================

def cmd_ip(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ip", "args": args}))
    if not args:
        subcmd = "addr"
        subargs = []
    else:
        subcmd = args[0]
        subargs = args[1:]

    if subcmd in ["addr", "a", "address"]:
        lines = []
        idx = 1
        for iface, if_data in ctx.state.network_interfaces.items():
            ip_val = if_data.get("ip", "")
            st = if_data.get("state", "DOWN")
            mac = if_data.get("mac", "00:00:00:00:00:00")
            if iface == "lo":
                flags = "LOOPBACK,UP,LOWER_UP" if st == "UP" else "LOOPBACK"
                lines.append(f"{idx}: {iface}: <{flags}> mtu 65536 qdisc noqueue state {st} group default qlen 1000")
                lines.append(f"    link/loopback {mac} brd 00:00:00:00:00:00")
                lines.append(f"    inet {ip_val} scope host {iface}")
                lines.append("       valid_lft forever preferred_lft forever")
            else:
                flags = "BROADCAST,MULTICAST,UP,LOWER_UP" if st == "UP" else "BROADCAST,MULTICAST"
                lines.append(f"{idx}: {iface}: <{flags}> mtu 1500 qdisc fq_codel state {st} group default qlen 1000")
                lines.append(f"    link/ether {mac} brd ff:ff:ff:ff:ff:ff")
                lines.append(f"    inet {ip_val} brd 10.0.42.255 scope global {iface}")
                lines.append("       valid_lft forever preferred_lft forever")
            idx += 1
        return ctx.result_factory(stdout="\n".join(lines) + "\n")

    elif subcmd in ["link", "l"]:
        if len(subargs) >= 2 and subargs[0] == "set":
            if subargs[1] == "dev" and len(subargs) >= 4:
                target_iface = subargs[2]
                action = subargs[3].lower()
            else:
                target_iface = subargs[1]
                action = subargs[2].lower() if len(subargs) > 2 else ""

            if target_iface not in ctx.state.network_interfaces:
                return ctx.result_factory(stderr=f'Cannot find device "{target_iface}"\n', exit_code=1)

            if action == "up":
                ctx.state.network_interfaces[target_iface]["state"] = "UP"
                if target_iface == "apollo0":
                    ctx.state.system_flags["NETWORK_ONLINE"] = True
                    ctx.bus.publish(Event("flag_changed", {"flag": "NETWORK_ONLINE", "value": True}))
                return ctx.result_factory()
            elif action == "down":
                ctx.state.network_interfaces[target_iface]["state"] = "DOWN"
                if target_iface == "apollo0":
                    ctx.state.system_flags["NETWORK_ONLINE"] = False
                    ctx.bus.publish(Event("flag_changed", {"flag": "NETWORK_ONLINE", "value": False}))
                return ctx.result_factory()
            else:
                return ctx.result_factory(stderr=f'ip link: unknown action "{action}"\n', exit_code=1)

        lines = []
        idx = 1
        for iface, if_data in ctx.state.network_interfaces.items():
            st = if_data.get("state", "DOWN")
            mac = if_data.get("mac", "00:00:00:00:00:00")
            if iface == "lo":
                flags = "LOOPBACK,UP,LOWER_UP" if st == "UP" else "LOOPBACK"
                lines.append(f"{idx}: {iface}: <{flags}> mtu 65536 qdisc noqueue state {st} mode DEFAULT group default qlen 1000")
                lines.append(f"    link/loopback {mac} brd 00:00:00:00:00:00")
            else:
                flags = "BROADCAST,MULTICAST,UP,LOWER_UP" if st == "UP" else "BROADCAST,MULTICAST"
                lines.append(f"{idx}: {iface}: <{flags}> mtu 1500 qdisc fq_codel state {st} mode DEFAULT group default qlen 1000")
                lines.append(f"    link/ether {mac} brd ff:ff:ff:ff:ff:ff")
            idx += 1
        return ctx.result_factory(stdout="\n".join(lines) + "\n")

    elif subcmd in ["route", "r"]:
        lines = [
            "default via 10.0.42.1 dev apollo0 proto dhcp src 10.0.42.15 metric 100",
            "10.0.42.0/24 dev apollo0 proto kernel scope link src 10.0.42.15 metric 100"
        ]
        return ctx.result_factory(stdout="\n".join(lines) + "\n")

    return ctx.result_factory(stderr=f'Object "{subcmd}" is unknown, try "ip help".\n', exit_code=1)


def cmd_ss(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ss", "args": args}))
    header = "Netid  State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process\n"
    lines = []
    for sock in ctx.state.listening_sockets:
        proto = sock.get("proto", "tcp")
        state = sock.get("state", "LISTEN")
        local = sock.get("local", "")
        peer = sock.get("peer", "")
        pid = sock.get("pid", 0)
        proc = sock.get("proc", "")
        proc_str = f'users:(("{proc}",pid={pid},fd=3))'
        lines.append(f"{proto:<6} {state:<7} 0       128     {local:<20} {peer:<18} {proc_str}")

    output = header + "\n".join(lines) + ("\n" if lines else "")
    return ctx.result_factory(stdout=output)


def cmd_ping(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ping", "args": args}))
    count = 4
    target = None
    idx = 0
    while idx < len(args):
        if args[idx] == "-c":
            if idx + 1 >= len(args) or not args[idx + 1].isdigit():
                return ctx.result_factory(stderr="ping: option requires an integer argument -- 'c'\n", exit_code=1)
            count = int(args[idx + 1])
            idx += 2
        elif args[idx].startswith("-c"):
            val = args[idx][2:]
            if not val.isdigit():
                return ctx.result_factory(stderr="ping: invalid count of packets to transmit\n", exit_code=1)
            count = int(val)
            idx += 1
        elif target is None:
            target = args[idx]
            idx += 1
        else:
            idx += 1

    if not target:
        return ctx.result_factory(stderr="ping: usage error: Destination address required\n", exit_code=1)

    iface_state = ctx.state.network_interfaces.get("apollo0", {}).get("state", "DOWN")
    if iface_state == "DOWN":
        return ctx.result_factory(stderr="ping: connect: Network is unreachable\n", exit_code=2)

    lines = [f"PING {target} ({target}) 56(84) bytes of data."]
    for i in range(1, count + 1):
        lines.append(f"64 bytes from {target}: icmp_seq={i} ttl=64 time=0.042 ms")
    lines.append("")
    lines.append(f"--- {target} ping statistics ---")
    lines.append(f"{count} packets transmitted, {count} received, 0% packet loss, time {count * 1000}ms")
    lines.append("rtt min/avg/max/mdev = 0.038/0.042/0.049/0.004 ms")

    return ctx.result_factory(stdout="\n".join(lines) + "\n")


# =====================================================================
# DIEGETIC RECOVERY PROTOCOL COMMANDS (repair_buffer, phoenix_daemon, phoenix_ctl, apollo-net)
# =====================================================================

def cmd_repair_buffer(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "repair_buffer", "args": args}))
    ctx.state.system_flags["BUFFER_REPAIRED"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "BUFFER_REPAIRED", "value": True}))
    return ctx.result_factory(stdout="[REPAIR PROTOCOL]: Ring buffer synchronized. Command history navigation enabled.\n")


def cmd_phoenix_daemon(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "phoenix_daemon", "args": args}))
    action = args[0] if args else "start"
    if action in ["start", "--sync", "-d", "status"]:
        ctx.state.system_flags["PHOENIX_ONLINE"] = True
        ctx.bus.publish(Event("flag_changed", {"flag": "PHOENIX_ONLINE", "value": True}))
        return ctx.result_factory(
            stdout="[PHOENIX-DAEMON]: Emergency Restoration Protocol activated. Listening on 127.0.0.1:8080. Gateway online.\n"
        )
    return ctx.result_factory(stdout=f"[PHOENIX-DAEMON]: Service status verified for action '{action}'.\n")


def cmd_phoenix_ctl(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "phoenix_ctl", "args": args}))
    return cmd_phoenix_daemon(ctx, args)


def cmd_apollo_net(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "apollo-net", "args": args}))
    iface_state = ctx.state.network_interfaces.get("apollo0", {}).get("state", "DOWN")
    return ctx.result_factory(
        stdout=f"[APOLLO-NET v1.0]: Subnet link state is {iface_state}. Gateway 10.0.42.1\n"
    )


# =====================================================================
# PEDAGOGICAL DEBRIEF MANAGER ("Take It to Linux")
# =====================================================================

class DebriefManager:
    DEBRIEFS: Dict[str, str] = {
        "BUFFER_REPAIRED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Terminal Line Disciplines & Input Buffering        │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You just repaired the input ring buffer to restore command history.   │\n"
            "│ In real Linux systems:                                                 │\n"
            "│ • The kernel TTY line discipline handles cooked vs raw input modes.    │\n"
            "│ • Libraries like GNU Readline manage arrow key navigation and history. │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "BASHRC_RESTORED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Shell Startup Profiles & Environment Variables    │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You restored ~/.bashrc to re-enable tab autocompletion and $PATH.     │\n"
            "│ In real Linux systems:                                                 │\n"
            "│ • ~/.bashrc runs for interactive non-login shells.                     │\n"
            "│ • The $PATH variable defines directory search order for executables.   │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "MALWARE_TERMINATED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Real-World Process Administration & Signals        │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You just used 'kill -9' to terminate a rogue process.                  │\n"
            "│ In production Linux environments:                                      │\n"
            "│ • SIGTERM (-15) allows processes to clean up sockets & open files.     │\n"
            "│ • SIGKILL (-9) immediately revokes kernel resources; use with care!    │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "NETWORK_ONLINE": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Network Interface Management with 'ip'             │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You used 'ip link set apollo0 up' to bring the network online.        │\n"
            "│ In modern Linux distributions:                                         │\n"
            "│ • The 'ip' tool (iproute2) replaced the legacy 'ifconfig' utility.     │\n"
            "│ • 'ip addr' inspects subnets, while 'ip route' controls IP gateways.  │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "PHOENIX_ONLINE": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Daemon Sockets & Service Orchestration             │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You restored the PHOENIX daemon and verified listening sockets.        │\n"
            "│ In enterprise Linux environments:                                      │\n"
            "│ • 'ss -tulpn' audits TCP/UDP sockets and binds to specific interfaces. │\n"
            "│ • Systemd unit files manage auto-restart and target state transitions. │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        )
    }

    def __init__(self, bus: EventBus, output_writer=None):
        self.bus = bus
        self.output_writer = output_writer or sys.stdout.write
        self.bus.subscribe(self.handle_event)

    def handle_event(self, event: Event):
        if event.type == "flag_changed":
            flag = event.data.get("flag")
            value = event.data.get("value")
            if value and flag in self.DEBRIEFS:
                self.output_writer("\n" + self.DEBRIEFS[flag] + "\n")


MAN_PAGES: Dict[str, str] = {
    "ls": "NAME\n    ls - list directory contents\n\nSYNOPSIS\n    ls [-a] [-l] [FILE]...\n\nEXAMPLES\n    ls -la /var/log\n    ls -a ~\n",
    "cd": "NAME\n    cd - change the working directory\n\nSYNOPSIS\n    cd [DIRECTORY]\n\nEXAMPLES\n    cd /opt/phoenix\n    cd ..\n",
    "cat": "NAME\n    cat - concatenate files and print on the standard output\n\nSYNOPSIS\n    cat [FILE]...\n\nEXAMPLES\n    cat /home/alice/readme.txt\n",
    "head": "NAME\n    head - output the first part of files\n\nSYNOPSIS\n    head [-n LINES] [FILE]...\n\nEXAMPLES\n    head -n 5 /var/log/system.log\n",
    "tail": "NAME\n    tail - output the last part of files\n\nSYNOPSIS\n    tail [-n LINES] [-f] [FILE]...\n\nEXAMPLES\n    tail -n 20 /var/log/system.log\n    tail -f /var/log/syslog\n",
    "grep": "NAME\n    grep - print lines that match patterns\n\nSYNOPSIS\n    grep [-i] [-v] [-n] [-r] PATTERN [FILE]...\n\nEXAMPLES\n    grep -i 'error' /var/log/system.log\n    grep -r 'PHOENIX' /opt\n",
    "find": "NAME\n    find - search for files in a directory hierarchy\n\nSYNOPSIS\n    find [PATH] -name PATTERN [-type f|d]\n\nEXAMPLES\n    find / -name '*.sh'\n    find /home/alice -type f\n",
    "chmod": "NAME\n    chmod - change file mode bits\n\nSYNOPSIS\n    chmod MODE FILE...\n\nEXAMPLES\n    chmod +x /opt/phoenix/recovery/recovery.sh\n    chmod 755 /bin/tool\n",
    "decrypt": "NAME\n    decrypt - Apollo diagnostic error translation daemon\n\nSYNOPSIS\n    decrypt\n\nDESCRIPTION\n    Analyzes the last stderr fault and emits plain-language recovery procedures.\n",
    "apollo-diagnostics": "NAME\n    apollo-diagnostics - Apollo diagnostic error translation daemon\n\nSYNOPSIS\n    apollo-diagnostics\n\nDESCRIPTION\n    Analyzes the last stderr fault and emits plain-language recovery procedures.\n",
    "sync": "NAME\n    sync - flush file system buffers\n\nSYNOPSIS\n    sync\n\nDESCRIPTION\n    Flushes in-memory buffers to persistent storage.\n",
    "ps": "NAME\n    ps - report a snapshot of the current processes\n\nSYNOPSIS\n    ps [aux] [-ef]\n\nEXAMPLES\n    ps aux\n    ps aux | grep miner\n",
    "kill": "NAME\n    kill - send a signal to a process\n\nSYNOPSIS\n    kill [-s sigspec | -n signum | -sigspec] pid...\n\nEXAMPLES\n    kill 104\n    kill -9 104\n    kill -15 210\n",
    "ip": "NAME\n    ip - show / manipulate routing, network devices, interfaces and tunnels\n\nSYNOPSIS\n    ip [addr | link | route] [COMMAND]\n\nEXAMPLES\n    ip addr\n    ip link set apollo0 up\n    ip route\n",
    "ss": "NAME\n    ss - another utility to investigate sockets\n\nSYNOPSIS\n    ss [-tulpn] [-t] [-u] [-l]\n\nEXAMPLES\n    ss -tulpn\n    ss -l\n",
    "ping": "NAME\n    ping - send ICMP ECHO_REQUEST to network hosts\n\nSYNOPSIS\n    ping [-c count] destination\n\nEXAMPLES\n    ping 10.0.42.1\n    ping -c 4 10.0.42.1\n",
    "echo": "NAME\n    echo - display a line of text\n\nSYNOPSIS\n    echo [STRING]...\n",
    "repair_buffer": "NAME\n    repair_buffer - patch terminal input ring buffer\n\nSYNOPSIS\n    repair_buffer\n",
    "phoenix_daemon": "NAME\n    phoenix_daemon - PHOENIX emergency restoration daemon\n\nSYNOPSIS\n    phoenix_daemon [start | --sync]\n",
    "phoenix_ctl": "NAME\n    phoenix_ctl - PHOENIX control utility\n\nSYNOPSIS\n    phoenix_ctl [COMMAND]\n",
    "apollo-net": "NAME\n    apollo-net - Apollo network interface diagnostic tool\n\nSYNOPSIS\n    apollo-net\n",
}


def cmd_man(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "man", "args": args}))
    if not args:
        return ctx.result_factory(stderr="What manual page do you want?\n", exit_code=1)

    target_cmd = args[0]
    if target_cmd in MAN_PAGES:
        return ctx.result_factory(stdout=MAN_PAGES[target_cmd])
    return ctx.result_factory(stderr=f"No manual entry for {target_cmd}\n", exit_code=1)


# =====================================================================
# STATE SERIALIZATION & HYDRATION ENGINE
# =====================================================================

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


# =====================================================================
# DIEGETIC SYNC COMMAND & AUTOSAVE OBSERVER
# =====================================================================

def cmd_sync(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "sync"}))
    try:
        save_game_state(ctx.state, "savegame.json")
        return ctx.result_factory(stdout="[SYSTEM]: In-memory buffers flushed to persistent storage.\n")
    except Exception as e:
        return ctx.result_factory(stderr=f"sync: error writing blocks: {str(e)}\n", exit_code=1)


def register_autosave_handler(bus: EventBus, get_state):
    def on_event(event: Event):
        if event.type == "flag_changed":
            state = get_state()
            if state:
                save_game_state(state, "savegame.json")
    bus.subscribe(on_event)


# =====================================================================
# 5. DIEGETIC AUTOCOMPLETER & ERGONOMIC DRIVERS
# =====================================================================

class VFSCompleter(Completer):
    def __init__(self, get_context):
        self.get_context = get_context

    def get_completions(self, document, complete_event):
        ctx: CommandContext = self.get_context()
        if not (ctx.state.unlocked_ergonomics.get("tab_completion", False) or ctx.state.unlocked_ergonomics.get("autocomplete", False)):
            return

        text = document.text_before_cursor
        tokens = text.split()
        word = document.get_word_before_cursor()

        # Command completion (first token)
        if len(tokens) == 0 or (len(tokens) == 1 and not text.endswith(" ")):
            path_var = ctx.state.env.get("PATH", "/bin:/usr/bin")
            for bin_dir in path_var.split(":"):
                node, _ = ctx.vfs.get_node([], bin_dir)
                if node and node.is_dir():
                    for name in node.children.keys():
                        if name.startswith(word):
                            yield Completion(name, start_position=-len(word))

            # Also complete local CWD entries for first token
            dir_node, _ = ctx.vfs.get_node(ctx.state.current_path, ".")
            if dir_node and dir_node.is_dir():
                for child_name, child_node in dir_node.children.items():
                    if child_name.startswith(word):
                        display_name = child_name + ("/" if child_node.is_dir() else "")
                        yield Completion(display_name, start_position=-len(word))
            return

        # Path / Argument completion
        target_path = word if word else "."
        if "/" in target_path:
            parent_path, prefix = target_path.rsplit("/", 1)
            search_dir = "/" if parent_path == "" else parent_path
        else:
            search_dir = "."
            prefix = target_path

        dir_node, _ = ctx.vfs.get_node(ctx.state.current_path, search_dir)
        if dir_node and dir_node.is_dir():
            for child_name, child_node in dir_node.children.items():
                if child_name.startswith(prefix):
                    display_name = child_name + ("/" if child_node.is_dir() else "")
                    yield Completion(display_name, start_position=-len(prefix))


def build_key_bindings(get_context):
    kb = KeyBindings()

    @kb.add("c-c")
    def handle_sigint(event):
        ctx = get_context()
        if not (ctx.state.unlocked_ergonomics.get("sigint_trap", False) or ctx.state.unlocked_ergonomics.get("sigint", False)):
            sys.stdout.write("\n[SIGNAL FAULT]: Process signal traps unconfigured. SIGINT ignored.\n")
            event.app.output.flush()
        else:
            sys.stdout.write("^C\n")
            event.app.output.flush()
            event.app.current_buffer.reset()

    @kb.add("up")
    def handle_up_arrow(event):
        ctx = get_context()
        if not (ctx.state.unlocked_ergonomics.get("history_arrows", False) or ctx.state.unlocked_ergonomics.get("history", False)):
            sys.stdout.write("\n[HARDWARE ERROR]: Input ring buffer corrupted. Navigation history disabled.\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.auto_up()

    @kb.add("down")
    def handle_down_arrow(event):
        ctx = get_context()
        if not (ctx.state.unlocked_ergonomics.get("history_arrows", False) or ctx.state.unlocked_ergonomics.get("history", False)):
            sys.stdout.write("\n[HARDWARE ERROR]: Input ring buffer corrupted. Navigation history disabled.\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.auto_down()

    @kb.add("tab")
    def handle_tab(event):
        ctx = get_context()
        if not (ctx.state.unlocked_ergonomics.get("tab_completion", False) or ctx.state.unlocked_ergonomics.get("autocomplete", False)):
            sys.stdout.write("\n[DRIVER MISSING]: libreadline unit offline. Tab autocompletion unavailable.\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.start_completion()

    return kb


create_key_bindings = build_key_bindings


# =====================================================================
# 6. PIPELINE PARSER & EXECUTION ENGINE
# =====================================================================

def split_unquoted(text: str, delimiter: str) -> List[str]:
    """Splits a string by delimiter only when not enclosed in quotes."""
    parts = []
    current = []
    in_single = False
    in_double = False
    escape = False

    i = 0
    d_len = len(delimiter)
    while i < len(text):
        c = text[i]
        if escape:
            current.append(c)
            escape = False
            i += 1
            continue

        if c == "\\":
            escape = True
            current.append(c)
            i += 1
            continue

        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
            i += 1
            continue

        if c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
            i += 1
            continue

        if not in_single and not in_double and text[i:i + d_len] == delimiter:
            parts.append("".join(current).strip())
            current = []
            i += d_len
            continue

        current.append(c)
        i += 1

    if current or not parts:
        parts.append("".join(current).strip())

    return parts


@dataclass
class ParsedCommand:
    args: List[str] = field(default_factory=list)
    redirect_out: Optional[str] = None
    redirect_append: bool = False
    redirect_in: Optional[str] = None


class PipelineEngine:
    def __init__(self, commands: Dict[str, Any], bus: EventBus):
        self.commands = commands
        self.bus = bus

    def parse_stage(self, stage_text: str) -> Tuple[Optional[ParsedCommand], Optional[str]]:
        stage_text = stage_text.strip()
        if not stage_text:
            return None, "empty command"

        redirect_out = None
        append_mode = False

        # Look for unquoted >> or >
        redirect_parts = split_unquoted(stage_text, ">>")
        if len(redirect_parts) > 1:
            stage_cmd = redirect_parts[0]
            redirect_target = ">>".join(redirect_parts[1:]).strip()
            append_mode = True
        else:
            redirect_parts = split_unquoted(stage_text, ">")
            if len(redirect_parts) > 1:
                stage_cmd = redirect_parts[0]
                redirect_target = ">".join(redirect_parts[1:]).strip()
                append_mode = False
            else:
                stage_cmd = stage_text
                redirect_target = None

        if redirect_target:
            try:
                target_tokens = shlex.split(redirect_target)
                if not target_tokens:
                    return None, "syntax error near unexpected token 'newline'"
                redirect_out = target_tokens[0]
            except ValueError as e:
                return None, str(e)

        try:
            tokens = shlex.split(stage_cmd)
        except ValueError as e:
            return None, str(e)

        if not tokens:
            return None, "missing command"

        return ParsedCommand(args=tokens, redirect_out=redirect_out, redirect_append=append_mode), None

    def execute_binary_or_command(self, cmd_name: str, args: List[str], ctx: CommandContext) -> CommandResult:
        # Direct lookup in registered command table
        if cmd_name in self.commands:
            return self.commands[cmd_name](ctx, args)

        # Check in VFS paths or relative/absolute path execution
        vfs_node, _ = ctx.vfs.get_node(ctx.state.current_path, cmd_name)
        if not vfs_node and "/" not in cmd_name:
            # Check $PATH directories
            path_env = ctx.state.env.get("PATH", "/bin:/usr/bin")
            for p_dir in path_env.split(":"):
                cand_node, _ = ctx.vfs.get_node([], f"{p_dir}/{cmd_name}")
                if cand_node:
                    vfs_node = cand_node
                    break

        if vfs_node and vfs_node.is_file():
            if vfs_node.permissions in ["000", "644", "600", "444"]:
                return ctx.result_factory(stderr=f"bash: {cmd_name}: Permission denied\n", exit_code=126)
            
            # Executable file dispatch
            base_name = cmd_name.split("/")[-1]
            if base_name in self.commands:
                return self.commands[base_name](ctx, args)
            elif base_name == "recovery.sh":
                return ctx.result_factory(stdout="[RECOVERY]: Restoring core nodes...\nSystem synchronization complete.\n")
            else:
                return ctx.result_factory(stdout=f"[EXEC]: Executed binary '{cmd_name}'\n")

        return ctx.result_factory(stderr=f"bash: {cmd_name}: command not found\n", exit_code=127)

    def run(self, raw_input: str, state: TerminalState) -> CommandResult:
        line = raw_input.strip()
        if not line:
            return CommandResult()

        stages_text = split_unquoted(line, "|")
        current_stdin = ""
        last_result = CommandResult()

        for idx, stage_text in enumerate(stages_text):
            parsed, err = self.parse_stage(stage_text)
            if err or not parsed:
                return CommandResult(stderr=f"bash: syntax error: {err}\n", exit_code=2)

            cmd_name = parsed.args[0]
            cmd_args = parsed.args[1:]

            stage_ctx = CommandContext(
                vfs=state.vfs,
                state=state,
                bus=self.bus,
                stdin=current_stdin
            )

            stage_result = self.execute_binary_or_command(cmd_name, cmd_args, stage_ctx)
            last_result = stage_result

            # If any stage fails, abort pipeline
            if stage_result.exit_code != 0:
                return stage_result

            current_stdin = stage_result.stdout

            # Handle file redirection on stage
            if parsed.redirect_out:
                redirect_target = parsed.redirect_out
                parent_dir = redirect_target.rsplit("/", 1)[0] if "/" in redirect_target else "."
                if not parent_dir:
                    parent_dir = "/"
                
                parent_node, _ = state.vfs.get_node(state.current_path, parent_dir)
                if not parent_node or not parent_node.is_dir():
                    return CommandResult(stderr=f"bash: {redirect_target}: No such file or directory\n", exit_code=1)
                
                if parent_node.permissions == "000":
                    return CommandResult(stderr=f"bash: {redirect_target}: Permission denied\n", exit_code=1)

                target_node, _ = state.vfs.get_node(state.current_path, redirect_target)
                if target_node:
                    if target_node.is_dir():
                        return CommandResult(stderr=f"bash: {redirect_target}: Is a directory\n", exit_code=1)
                    if target_node.permissions in ["000", "444"]:
                        return CommandResult(stderr=f"bash: {redirect_target}: Permission denied\n", exit_code=1)
                    if parsed.redirect_append:
                        target_node.content = (target_node.content or "") + stage_result.stdout
                    else:
                        target_node.content = stage_result.stdout
                else:
                    success, w_err = state.vfs.write_file(
                        state.current_path,
                        redirect_target,
                        stage_result.stdout,
                        append=parsed.redirect_append,
                        owner=state.env.get("USER", "alice")
                    )
                    if not success:
                        return CommandResult(stderr=f"bash: {redirect_target}: {w_err}\n", exit_code=1)

                # Output was consumed by file redirection
                current_stdin = ""
                last_result = CommandResult(stdout="", stderr="", exit_code=0)

        return last_result


# =====================================================================
# 7. REPL SHELL RUNNER
# =====================================================================

class TerminalShell:
    def __init__(self, ctx: CommandContext, command_table: Dict[str, Any], **session_kwargs):
        self.ctx = ctx
        self.commands = command_table
        self.pipeline_engine = PipelineEngine(self.commands, self.ctx.bus)
        self.history = InMemoryHistory()
        self.completer = VFSCompleter(lambda: self.ctx)
        self.key_bindings = build_key_bindings(lambda: self.ctx)
        try:
            self.session = PromptSession(
                history=self.history,
                completer=self.completer,
                key_bindings=self.key_bindings,
                complete_while_typing=False,
                **session_kwargs
            )
        except Exception:
            from prompt_toolkit.input import DummyInput
            from prompt_toolkit.output import DummyOutput
            self.session = PromptSession(
                history=self.history,
                completer=self.completer,
                key_bindings=self.key_bindings,
                complete_while_typing=False,
                input=session_kwargs.get("input", DummyInput()),
                output=session_kwargs.get("output", DummyOutput())
            )

    def get_prompt(self) -> ANSI:
        user = self.ctx.state.env.get("USER", "alice")
        host = self.ctx.state.env.get("HOST", "apollo")
        cwd = self.ctx.state.cwd_str
        return ANSI(f"\033[1;32m{user}@{host}\033[0m:\033[1;34m{cwd}\033[0m$ ")

    def execute_command_line(self, raw_input: str) -> CommandResult:
        result = self.pipeline_engine.run(raw_input, self.ctx.state)
        if result.exit_code != 0 and result.stderr:
            self.ctx.state.last_stderr = result.stderr.strip()
        return result

    def execute_line(self, line: str):
        line = line.strip()
        if not line:
            return
        result = self.execute_command_line(line)
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)

    def run(self):
        print("=== APOLLO WORKSTATION TERMINAL [RECOVERY MODE] ===")
        print("Type 'exit' to disconnect.\n")
        while True:
            try:
                with patch_stdout():
                    text = self.session.prompt(self.get_prompt())
                if text.strip() == "exit":
                    break
                self.execute_line(text)
            except EOFError:
                break
            except KeyboardInterrupt:
                continue


COMMAND_TABLE = {
    "pwd": cmd_pwd,
    "cd": cmd_cd,
    "ls": cmd_ls,
    "cat": cmd_cat,
    "head": cmd_head,
    "tail": cmd_tail,
    "grep": cmd_grep,
    "find": cmd_find,
    "chmod": cmd_chmod,
    "man": cmd_man,
    "decrypt": cmd_decrypt,
    "apollo-diagnostics": cmd_decrypt,
    "sync": cmd_sync,
    "tree": cmd_tree,
    "ps": cmd_ps,
    "kill": cmd_kill,
    "ip": cmd_ip,
    "ss": cmd_ss,
    "ping": cmd_ping,
    "echo": cmd_echo,
    "repair_buffer": cmd_repair_buffer,
    "phoenix_ctl": cmd_phoenix_ctl,
    "phoenix_daemon": cmd_phoenix_daemon,
    "apollo-net": cmd_apollo_net,
}


def main():
    bus = EventBus()
    state = load_game_state("savegame.json", bus)
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