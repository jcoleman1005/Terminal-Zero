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
        for listener in self._listeners:
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
            "PATH": "/bin"
        }
        self.unlocked_ergonomics: Dict[str, bool] = {
            "history": False,
            "autocomplete": False,
            "sigint": False
        }
        self.system_flags: Dict[str, bool] = {
            "BUFFER_REPAIRED": False,
            "BASHRC_RESTORED": False,
            "MALWARE_TERMINATED": False,
            "PHOENIX_ONLINE": False
        }
        self.process_table: List[ProcessEntry] = [
            ProcessEntry(pid=1, name="systemd", user="root", cpu=0.1, command="/sbin/init"),
            ProcessEntry(pid=104, name="sys_miner", user="root", cpu=98.2, command="/tmp/.miner --stealth"),
            ProcessEntry(pid=210, name="sshd", user="root", cpu=0.0, command="/usr/sbin/sshd -D")
        ]
        self.last_stderr: str = ""

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
    add_dir("/opt/phoenix/recovery")
    add_dir("/home/alice/notes")

    # Binaries (Standard in /bin)
    for b in ["cat", "cd", "echo", "exit", "ls", "pwd", "sync", "decrypt", "chmod", "man"]:
        add_file(f"/bin/{b}", "ELF 64-bit LSB executable", perms="755")

    # Soft-Gated & Diegetic Tool Binaries
    add_file("/opt/phoenix/recovery/tree", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/grep", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/find", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/recovery.sh", "#!/bin/bash\necho 'Restoring core nodes...'", perms="755")

    # Environmental Lore & Clue Nodes
    add_file(
        "/home/alice/.bashrc",
        "# Workstation Shell Configuration\n# Corrupted ring-buffer hooks detected.\nexport PATH=$PATH:/opt/phoenix/recovery\n",
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
# STREAM & INSPECTION UTILITIES (cat, head, tail, grep, find)
# =====================================================================

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
    file_targets = []
    idx = 0
    while idx < len(args):
        if args[idx] == "-n":
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

    if not file_targets:
        if ctx.stdin:
            selected = ctx.stdin.splitlines(keepends=True)[-lines_count:]
            return ctx.result_factory(stdout="".join(selected))
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

    return ctx.result_factory(stdout="".join(output))


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
        if arg.startswith("-") and pattern is None:
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
            return ctx.result_factory(stdout="\n".join(matched_lines) + ("\n" if matched_lines else ""))
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
# DIEGETIC ADVISORY ENGINE (decrypt)
# =====================================================================

def cmd_decrypt(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "decrypt", "args": args}))
    last_err = ctx.state.last_stderr.strip()

    if not last_err:
        return ctx.result_factory(
            stdout="[APOLLO-DIAGNOSTIC]: No recent hardware or kernel fault recorded in buffer.\n"
        )

    # Diagnostic Rule Mapping
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
            "Node execution or read bits are disabled.\n"
            "Action: Use 'chmod +x <target>' or 'chmod 755 <target>' to elevate node permissions."
        )
    elif "command not found" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x4F - BINARY UNREGISTERED]\n"
            "Executable not located in standard search paths ($PATH).\n"
            "Action: Check /opt/phoenix/recovery or inspect $PATH settings."
        )
    elif "missing file operand" in last_err or "missing pattern" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x05 - ARITY MISMATCH]\n"
            "Command invoked without mandatory arguments.\n"
            "Action: Run 'man <command>' to inspect supported syntax."
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
# PERMISSIONS & SYSTEM UTILITIES (chmod, man)
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

        # Numeric mode support (e.g. 755, 644)
        if mode_str.isdigit() and len(mode_str) == 3:
            node.permissions = mode_str
        # Symbolic mode support (+x, -x, u+x, etc.)
        elif "+x" in mode_str:
            node.permissions = "755"
        elif "-x" in mode_str:
            node.permissions = "644"
        else:
            return ctx.result_factory(stderr=f"chmod: invalid mode: '{mode_str}'\n", exit_code=1)

    return ctx.result_factory()


MAN_PAGES: Dict[str, str] = {
    "ls": "NAME\n    ls - list directory contents\n\nSYNOPSIS\n    ls [-a] [-l] [FILE]...\n\nEXAMPLES\n    ls -la /var/log\n    ls -a ~\n",
    "cd": "NAME\n    cd - change the working directory\n\nSYNOPSIS\n    cd [DIRECTORY]\n\nEXAMPLES\n    cd /opt/phoenix\n    cd ..\n",
    "cat": "NAME\n    cat - concatenate files and print on the standard output\n\nSYNOPSIS\n    cat [FILE]...\n\nEXAMPLES\n    cat /home/alice/readme.txt\n",
    "head": "NAME\n    head - output the first part of files\n\nSYNOPSIS\n    head [-n LINES] [FILE]...\n\nEXAMPLES\n    head -n 5 /var/log/system.log\n",
    "tail": "NAME\n    tail - output the last part of files\n\nSYNOPSIS\n    tail [-n LINES] [FILE]...\n\nEXAMPLES\n    tail -n 20 /var/log/system.log\n",
    "grep": "NAME\n    grep - print lines that match patterns\n\nSYNOPSIS\n    grep [-i] [-v] [-n] [-r] PATTERN [FILE]...\n\nEXAMPLES\n    grep -i 'error' /var/log/system.log\n    grep -r 'PHOENIX' /opt\n",
    "find": "NAME\n    find - search for files in a directory hierarchy\n\nSYNOPSIS\n    find [PATH] -name PATTERN [-type f|d]\n\nEXAMPLES\n    find / -name '*.sh'\n    find /home/alice -type f\n",
    "chmod": "NAME\n    chmod - change file mode bits\n\nSYNOPSIS\n    chmod MODE FILE...\n\nEXAMPLES\n    chmod +x /opt/phoenix/recovery/recovery.sh\n    chmod 755 /bin/tool\n",
    "decrypt": "NAME\n    decrypt - Apollo diagnostic error translation daemon\n\nSYNOPSIS\n    decrypt\n\nDESCRIPTION\n    Analyzes the last stderr fault and emits plain-language recovery procedures.\n",
    "sync": "NAME\n    sync - flush file system buffers\n\nSYNOPSIS\n    sync\n\nDESCRIPTION\n    Flushes in-memory buffers to persistent storage.\n"
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
    payload = {
        "version": "2.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "player": {
            "current_directory": state.cwd_str,
            "env": state.env,
            "unlocked_ergonomics": state.unlocked_ergonomics
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
    state.unlocked_ergonomics = data.get("player", {}).get("unlocked_ergonomics", state.unlocked_ergonomics)
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
        if not ctx.state.unlocked_ergonomics.get("autocomplete", False):
            return

        text = document.text_before_cursor
        tokens = text.split()
        word = document.get_word_before_cursor()

        # Command completion (first token)
        if len(tokens) == 0 or (len(tokens) == 1 and not text.endswith(" ")):
            path_var = ctx.state.env.get("PATH", "/bin")
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
        if not ctx.state.unlocked_ergonomics.get("sigint", False):
            sys.stdout.write("\n[HARDWARE ADVISORY: Signal trapping subsystem offline.]\n")
            event.app.output.flush()
        else:
            sys.stdout.write("^C\n")
            event.app.output.flush()
            event.app.current_buffer.reset()

    @kb.add("up")
    def handle_up_arrow(event):
        ctx = get_context()
        if not ctx.state.unlocked_ergonomics.get("history", False):
            sys.stdout.write("\n[HARDWARE ADVISORY: Input driver corrupted. Missing ring buffer hooks.]\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.auto_up()

    @kb.add("down")
    def handle_down_arrow(event):
        ctx = get_context()
        if not ctx.state.unlocked_ergonomics.get("history", False):
            sys.stdout.write("\n[HARDWARE ADVISORY: Input driver corrupted. Missing ring buffer hooks.]\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.auto_down()

    @kb.add("tab")
    def handle_tab(event):
        ctx = get_context()
        if not ctx.state.unlocked_ergonomics.get("autocomplete", False):
            sys.stdout.write("\n[HARDWARE ADVISORY: Input driver corrupted. Missing libreadline hooks.]\n")
            event.app.output.flush()
        else:
            event.app.current_buffer.start_completion()

    return kb


create_key_bindings = build_key_bindings


# =====================================================================
# 6. REPL SHELL RUNNER
# =====================================================================

@dataclass
class ParsedCommand:
    args: List[str] = field(default_factory=list)
    redirect_out: Optional[str] = None
    redirect_append: bool = False
    redirect_in: Optional[str] = None


class TerminalShell:
    def __init__(self, ctx: CommandContext, command_table: Dict[str, Any], **session_kwargs):
        self.ctx = ctx
        self.commands = command_table
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

    def execute_line(self, line: str):
        line = line.strip()
        if not line:
            return

        # Check for redirection (> or >>)
        redirect_target = None
        append_mode = False
        if ">>" in line:
            line, redirect_target = line.split(">>", 1)
            append_mode = True
            line, redirect_target = line.strip(), redirect_target.strip()
        elif ">" in line:
            line, redirect_target = line.split(">", 1)
            append_mode = False
            line, redirect_target = line.strip(), redirect_target.strip()

        # Check for single pipe (|)
        stages = line.split("|")
        pipe_input = ""

        for i, stage in enumerate(stages):
            stage = stage.strip()
            if not stage:
                continue
            try:
                tokens = shlex.split(stage)
            except ValueError as e:
                self.ctx.state.last_stderr = f"bash: syntax error: {str(e)}\n"
                sys.stderr.write(self.ctx.state.last_stderr)
                return

            cmd_name = tokens[0]
            args = tokens[1:]

            if cmd_name not in self.commands:
                err = f"bash: {cmd_name}: command not found\n"
                self.ctx.state.last_stderr = err
                sys.stderr.write(err)
                return

            # Execute stage with piped input if applicable
            self.ctx.stdin = pipe_input
            result = self.commands[cmd_name](self.ctx, args)

            if result.stderr:
                self.ctx.state.last_stderr = result.stderr
                sys.stderr.write(result.stderr)
                return
            else:
                self.ctx.state.last_stderr = ""

            pipe_input = result.stdout

        # Handle output redirection or final stdout
        if redirect_target:
            parts = [p for p in redirect_target.split("/") if p]
            parent_dir = redirect_target.rsplit("/", 1)[0] if "/" in redirect_target else "."
            if not parent_dir:
                parent_dir = "/"
            parent_node, _ = self.ctx.vfs.get_node(self.ctx.state.current_path, parent_dir)
            if parent_node and parent_node.is_dir():
                fname = parts[-1]
                if fname in parent_node.children and parent_node.children[fname].is_file():
                    if append_mode:
                        parent_node.children[fname].content = (parent_node.children[fname].content or "") + pipe_input
                    else:
                        parent_node.children[fname].content = pipe_input
                else:
                    parent_node.children[fname] = VFSNode(type="file", permissions="644", owner="alice", content=pipe_input)
            else:
                err = f"bash: {redirect_target}: No such file or directory\n"
                self.ctx.state.last_stderr = err
                sys.stderr.write(err)
        elif pipe_input:
            sys.stdout.write(pipe_input)

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


def run_repl(ctx: Optional[CommandContext] = None, command_table: Optional[Dict[str, Any]] = None):
    if ctx is None:
        root_node = build_default_vfs()
        vfs = VirtualFilesystem(root_node)
        bus = EventBus()
        state = TerminalState(vfs, bus, ["home", "alice"])
        ctx = CommandContext(vfs=vfs, state=state, bus=bus)
    if command_table is None:
        command_table = {
            "tree": cmd_tree,
            "cat": cmd_cat,
            "head": cmd_head,
            "tail": cmd_tail,
            "grep": cmd_grep,
            "find": cmd_find,
            "pwd": cmd_pwd,
            "cd": cmd_cd,
            "ls": cmd_ls,
            "chmod": cmd_chmod,
            "man": cmd_man,
            "decrypt": cmd_decrypt,
            "sync": cmd_sync,
        }
    shell = TerminalShell(ctx, command_table)
    shell.run()


def main():
    run_repl()


if __name__ == "__main__":
    main()