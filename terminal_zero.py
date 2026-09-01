from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import fnmatch
import os
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
    for b in ["cat", "cd", "echo", "exit", "ls", "pwd", "sync", "decrypt"]:
        add_file(f"/bin/{b}", "ELF 64-bit LSB executable", perms="755")

    # Soft-Gated & Diegetic Tool Binaries
    add_file("/opt/phoenix/recovery/tree", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/grep", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/find", "ELF 64-bit LSB executable", perms="755")

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

        try:
            tokens = shlex.split(line)
        except ValueError as e:
            self.ctx.state.last_stderr = f"bash: syntax error: {str(e)}\n"
            sys.stderr.write(self.ctx.state.last_stderr)
            return

        cmd_name = tokens[0]
        args = tokens[1:]

        if cmd_name in self.commands:
            result: CommandResult = self.commands[cmd_name](self.ctx, args)
            if result.stdout:
                sys.stdout.write(result.stdout)
            if result.stderr:
                self.ctx.state.last_stderr = result.stderr
                sys.stderr.write(result.stderr)
            else:
                self.ctx.state.last_stderr = ""
        else:
            err = f"bash: {cmd_name}: command not found\n"
            self.ctx.state.last_stderr = err
            sys.stderr.write(err)

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
        }
    shell = TerminalShell(ctx, command_table)
    shell.run()


def main():
    run_repl()


if __name__ == "__main__":
    main()