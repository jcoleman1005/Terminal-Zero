from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import fnmatch
import os
import shlex
import sys

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
# 4. DIEGETIC TREE UTILITY HANDLER
# =====================================================================

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
# 4. COMMAND IMPLEMENTATION LAYER
# =====================================================================

@dataclass
class CommandContext:
    state: TerminalState
    vfs: VirtualFilesystem
    engine: MissionEngine
    bus: EventBus
    stdin: str = ""

@dataclass
class CommandResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

def cmd_pwd(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "pwd"}))
    return CommandResult(stdout=ctx.state.cwd_str + "\n")

def cmd_echo(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "echo"}))
    return CommandResult(stdout=" ".join(args) + "\n")

def cmd_ls(ctx: CommandContext, args: List[str]) -> CommandResult:
    show_all = False
    targets = []
    for arg in args:
        if arg.startswith("-"):
            if arg in ["-a", "-la", "-al"]:
                show_all = True
            else:
                return CommandResult(stderr=f"ls: unrecognized option '{arg}'\n", exit_code=1)
        else:
            targets.append(arg)

    ctx.bus.publish(Event("command_executed", {"command": "ls", "show_all": show_all}))
    target = targets[0] if targets else "."
    tokens = ctx.vfs.resolve_path(ctx.state.current_path, target)
    
    entries = ctx.vfs.list_dir(tokens, show_all=show_all)
    if entries is None:
        return CommandResult(stderr=f"ls: cannot access '{target}': No such file or directory\n", exit_code=1)

    ctx.bus.publish(Event("directory_listed", {"path": "/" + "/".join(tokens), "show_all": show_all}))
    return CommandResult(stdout="  ".join(entries) + "\n" if entries else "")

def cmd_cd(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cd"}))
    if len(args) > 1:
        return CommandResult(stderr="cd: too many arguments\n", exit_code=1)

    target = args[0] if args else None
    success, err = ctx.state.change_directory(target)
    if not success:
        return CommandResult(stderr=err + "\n", exit_code=1)
    return CommandResult()

def cmd_cat(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cat"}))
    if not args:
        if ctx.stdin:
            return CommandResult(stdout=ctx.stdin)
        return CommandResult(stderr="cat: missing file operand\n", exit_code=1)

    out = []
    for target in args:
        tokens = ctx.vfs.resolve_path(ctx.state.current_path, target)
        node = ctx.vfs.get_node(tokens)
        if node is None:
            return CommandResult(stderr=f"cat: {target}: No such file or directory\n", exit_code=1)
        elif isinstance(node, dict):
            return CommandResult(stderr=f"cat: {target}: Is a directory\n", exit_code=1)
        else:
            out.append(node)
            full_path_str = "/" + "/".join(tokens)
            ctx.bus.publish(Event("file_read", {"path": full_path_str, "file_name": tokens[-1]}))

    return CommandResult(stdout="\n".join(out) + "\n")

def cmd_cp(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cp"}))
    if len(args) == 0:
        return CommandResult(stderr="cp: missing file operand\n", exit_code=1)
    if len(args) == 1:
        return CommandResult(stderr=f"cp: missing destination file operand after '{args[0]}'\n", exit_code=1)

    src_path_str = args[0]
    dest_path_str = args[1]

    src_tokens = ctx.vfs.resolve_path(ctx.state.current_path, src_path_str)
    src_node = ctx.vfs.get_node(src_tokens)

    if src_node is None:
        return CommandResult(stderr=f"cp: cannot stat '{src_path_str}': No such file or directory\n", exit_code=1)
    if isinstance(src_node, dict):
        return CommandResult(stderr=f"cp: -r not specified; omitting directory '{src_path_str}'\n", exit_code=1)
    if not isinstance(src_node, str):
        return CommandResult(stderr=f"cp: cannot stat '{src_path_str}': No such file or directory\n", exit_code=1)

    dest_tokens = ctx.vfs.resolve_path(ctx.state.current_path, dest_path_str)
    dest_node = ctx.vfs.get_node(dest_tokens)

    if isinstance(dest_node, dict):
        src_filename = src_tokens[-1] if src_tokens else src_path_str.strip("/").split("/")[-1]
        dest_tokens = dest_tokens + [src_filename]

    success = ctx.vfs.write_file(dest_tokens, src_node)
    if not success:
        return CommandResult(stderr=f"cp: cannot create regular file '{dest_path_str}': No such file or directory\n", exit_code=1)

    return CommandResult()

def cmd_grep(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "grep"}))
    if not args:
        return CommandResult(stderr="Usage: grep [PATTERN] [FILE]\n", exit_code=1)

    pattern = args[0]
    file_targets = args[1:]
    source_lines = []
    source_name = "stdin"

    if not file_targets:
        if not ctx.stdin:
            return CommandResult(stderr="grep: no input provided\n", exit_code=1)
        source_lines = ctx.stdin.splitlines()
    else:
        target = file_targets[0]
        tokens = ctx.vfs.resolve_path(ctx.state.current_path, target)
        content = ctx.vfs.read_file(tokens)
        if content is None:
            return CommandResult(stderr=f"grep: {target}: No such file or directory\n", exit_code=1)
        source_lines = content.splitlines()
        source_name = "/" + "/".join(tokens)

    matches = [line for line in source_lines if pattern.lower() in line.lower()]
    
    # PASS FULL MATCH PAYLOAD TO THE EVENT BUS
    ctx.bus.publish(Event("pattern_searched", {
        "pattern": pattern,
        "file": source_name,
        "matches": matches,
        "match_count": len(matches)
    }))

    if not matches:
        return CommandResult(exit_code=1)
    return CommandResult(stdout="\n".join(matches) + "\n")

def cmd_find(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "find"}))
    if not args:
        return CommandResult(stderr="Usage: find [PATH] -name [PATTERN]\n", exit_code=1)

    start_path_str = args[0]
    name_pattern = None
    if len(args) > 1:
        if args[1] == "-name" and len(args) > 2:
            name_pattern = args[2]

    target_tokens = ctx.vfs.resolve_path(ctx.state.current_path, start_path_str)
    if ctx.vfs.get_node(target_tokens) is None:
        return CommandResult(stderr=f"find: '{start_path_str}': No such file or directory\n", exit_code=1)

    matched_paths = []
    for path_str, _ in ctx.vfs.traverse(target_tokens):
        filename = path_str.split("/")[-1]
        if name_pattern:
            if fnmatch.fnmatch(filename, name_pattern):
                matched_paths.append(path_str)
        else:
            matched_paths.append(path_str)

    # PASS FULL LIST OF PATHS LOCATED TO EVENT BUS
    ctx.bus.publish(Event("files_searched", {
        "target_path": start_path_str,
        "pattern": name_pattern,
        "matches": matched_paths
    }))

    return CommandResult(stdout="\n".join(matched_paths) + ("\n" if matched_paths else ""))

# =====================================================================
# 5. APOLLO SHELL PARSER & EXECUTION PIPELINE
# =====================================================================

@dataclass
class AtomicCommand:
    args: List[str] = field(default_factory=list)
    redirect_out: Optional[str] = None
    redirect_append: bool = False
    redirect_in: Optional[str] = None

class ShellPipeline:
    def __init__(self, commands: List[AtomicCommand]):
        self.commands = commands

class ShellParser:
    @staticmethod
    def expand_variables(tokens: List[str], env: Dict[str, str]) -> List[str]:
        expanded = []
        for token in tokens:
            for k, v in env.items():
                token = token.replace(f"${k}", v)
            expanded.append(token)
        return expanded

    @staticmethod
    def expand_wildcards(tokens: List[str], ctx: CommandContext) -> List[str]:
        expanded = []
        for token in tokens:
            if any(char in token for char in ["*", "?", "["]):
                dirname = os.path.dirname(token)
                pattern = os.path.basename(token)
                target_dir = dirname if dirname else "."
                resolved_dir = ctx.vfs.resolve_path(ctx.state.current_path, target_dir)
                node = ctx.vfs.get_node(resolved_dir)
                if isinstance(node, dict):
                    matches = [
                        (f"{dirname}/{name}" if dirname else name)
                        for name in sorted(node.keys())
                        if fnmatch.fnmatch(name, pattern)
                    ]
                    if matches:
                        expanded.extend(matches)
                        continue
            expanded.append(token)
        return expanded

    @classmethod
    def parse_line(cls, raw_line: str, ctx: CommandContext) -> Optional[List[ShellPipeline]]:
        if not raw_line.strip():
            return None

        try:
            tokens = shlex.split(raw_line)
        except ValueError as err:
            print(f"apollo-sh: syntax error: {err}")
            return None

        tokens = cls.expand_variables(tokens, ctx.state.env)
        tokens = cls.expand_wildcards(tokens, ctx)

        and_chunks: List[List[str]] = []
        current_chunk: List[str] = []
        for t in tokens:
            if t == "&&":
                if current_chunk:
                    and_chunks.append(current_chunk)
                    current_chunk = []
            else:
                current_chunk.append(t)
        if current_chunk:
            and_chunks.append(current_chunk)

        pipelines: List[ShellPipeline] = []
        for chunk in and_chunks:
            pipe_cmds: List[AtomicCommand] = []
            curr_cmd = AtomicCommand()
            i = 0
            while i < len(chunk):
                token = chunk[i]
                if token == "|":
                    pipe_cmds.append(curr_cmd)
                    curr_cmd = AtomicCommand()
                elif token == ">":
                    if i + 1 < len(chunk):
                        curr_cmd.redirect_out = chunk[i + 1]
                        curr_cmd.redirect_append = False
                        i += 1
                elif token == ">>":
                    if i + 1 < len(chunk):
                        curr_cmd.redirect_out = chunk[i + 1]
                        curr_cmd.redirect_append = True
                        i += 1
                elif token == "<":
                    if i + 1 < len(chunk):
                        curr_cmd.redirect_in = chunk[i + 1]
                        i += 1
                else:
                    curr_cmd.args.append(token)
                i += 1
            if curr_cmd.args or curr_cmd.redirect_in or curr_cmd.redirect_out:
                pipe_cmds.append(curr_cmd)
            pipelines.append(ShellPipeline(pipe_cmds))

        return pipelines


class ShellExecutor:
    def __init__(self, ctx: CommandContext, command_table: Dict[str, Any]):
        self.ctx = ctx
        self.commands = command_table

    def execute_pipeline(self, pipeline: ShellPipeline) -> int:
        pipeline_input = ""

        for idx, atomic in enumerate(pipeline.commands):
            if not atomic.args:
                continue

            cmd_name, cmd_args = atomic.args[0], atomic.args[1:]

            # [--- STRICT VFS GATE ---]
            is_valid_binary = False
            
            # 1. Check if user provided an explicit path (e.g., /opt/phoenix/grep)
            if "/" in cmd_name:
                target_tokens = self.ctx.vfs.resolve_path(self.ctx.state.current_path, cmd_name)
                is_valid_binary = (self.ctx.vfs.get_node(target_tokens) is not None)
            else:
                # 2. Scan $PATH directories
                if "PATH" in self.ctx.state.env:
                    for path_dir in self.ctx.state.env["PATH"].split(":"):
                        dir_tokens = self.ctx.vfs.resolve_path(self.ctx.state.current_path, path_dir)
                        dir_node = self.ctx.vfs.get_node(dir_tokens)
                        if isinstance(dir_node, dict) and cmd_name in dir_node:
                            is_valid_binary = True
                            break

            if not is_valid_binary:
                print(f"apollo-sh: {cmd_name}: command not found")
                return 127
            # [--- END STRICT VFS GATE ---]

            if atomic.redirect_in:
                tokens = self.ctx.vfs.resolve_path(self.ctx.state.current_path, atomic.redirect_in)
                content = self.ctx.vfs.read_file(tokens)
                if content is None:
                    print(f"apollo-sh: {atomic.redirect_in}: No such file")
                    return 1
                pipeline_input = content

            self.ctx.stdin = pipeline_input

            exec_name = cmd_name.split("/")[-1] if "/" in cmd_name else cmd_name
            if exec_name in self.commands:
                result: CommandResult = self.commands[exec_name](self.ctx, cmd_args)
            elif cmd_name in self.commands:
                result: CommandResult = self.commands[cmd_name](self.ctx, cmd_args)
            else:
                print(f"apollo-sh: {cmd_name}: command not found")
                return 127

            if result.stderr:
                sys.stderr.write(result.stderr)
                if result.exit_code != 0 and idx == len(pipeline.commands) - 1:
                    return result.exit_code

            if atomic.redirect_out:
                tokens = self.ctx.vfs.resolve_path(self.ctx.state.current_path, atomic.redirect_out)
                success = self.ctx.vfs.write_file(tokens, result.stdout, append=atomic.redirect_append)
                if not success:
                    print(f"apollo-sh: cannot redirect output to {atomic.redirect_out}")
                    return 1
                pipeline_input = ""
            else:
                if idx == len(pipeline.commands) - 1:
                    if result.stdout:
                        sys.stdout.write(result.stdout)
                else:
                    pipeline_input = result.stdout

            if result.exit_code != 0:
                return result.exit_code

        return 0

# =====================================================================
# 6. ENVIRONMENT SETUP & REPL
# =====================================================================

def create_environment():
    raw_fs = {
        "/": {
            "bin": {
                "cat": "ELF 64-bit LSB executable",
                "cd": "ELF 64-bit LSB executable",
                "cp": "ELF 64-bit LSB executable",
                "echo": "ELF 64-bit LSB executable",
                "exit": "ELF 64-bit LSB executable",
                "goals": "ELF 64-bit LSB executable",
                "help": "ELF 64-bit LSB executable",
                "ls": "ELF 64-bit LSB executable",
                "objectives": "ELF 64-bit LSB executable",
                "pwd": "ELF 64-bit LSB executable"
            },
            "home": {
                "alice": {
                    ".mission": {
                        "briefing.txt": "=== CLASSIFIED EMERGENCY BRIEFING ===\nIncident: Global telemetry severed at 03:42 UTC.\nLead: Check system logs under /var/log/ for failed services.\n====================================="
                    },
                    "notes": {
                        "sysadmin_notes.txt": "SYSADMIN SURVIVAL GUIDE:\n\n[DIRECTORY NAVIGATION]\nLinux paths start at root '/'. You can jump across branches:\n    cd /var/log\n\n[TEXT SEARCHING & PIPELINES]\nChain commands using pipes or search files directly:\n    cat /var/log/system.log | grep phoenix\n    grep phoenix /var/log/*.log\n\n[FILE SEARCHING]\nSearch trees using wildcard patterns:\n    find <start_path> -name \"<pattern>\"\nExample: find / -name \"*.conf\"\n",
                        "mapping_tool.txt": "UTILITY DISCOVERY NOTE:\nTo view a graphical branch map of directories you've explored, use:\n\n    tree\n"
                    },
                    "readme.txt": "APOLLO WORKSTATION LOGON\n\n[SYSTEM ORIENTATION CLUES]\n1. Confirm your exact location using 'pwd'.\n2. Hidden system entries exist. Use 'ls -a' to reveal entries starting with '.'.\n\nType 'objectives' to check current operational goals.\nType 'help' to review your known command list.\n"
                }
            },
            "etc": {
                "motd": "EMERGENCY PROTOCOL ACTIVE. Check your operator manual using 'help' and type 'objectives' to begin."
            },
            "opt": {
                "phoenix": {
                    "README.txt": "PHOENIX Recovery Subsystem v4.2. Run recovery scripts to restore routing.",
                    "config": {
                        "phoenix.conf": "PORT=8080\nSTATUS=DEGRADED\nAUTH_KEY=PX-9042-ALPHA\nLOG_TARGET=/var/log/system.log\n"
                    },
                    "recovery": {
                        "find": "ELF 64-bit LSB executable",
                        "grep": "ELF 64-bit LSB executable",
                        "recovery.sh": "#!/bin/bash\necho 'Restoring core nodes...'",
                        "tree": "ELF 64-bit LSB executable"
                    }
                }
            },
            "var": {
                "log": {
                    "system.log": "03:40:12 apollo kernel: Network interface eth0 link down\n03:41:05 apollo auth: Successful login for alice from 127.0.0.1\n03:42:19 apollo systemd: phoenix-sync service terminated unexpectedly.\n03:42:20 apollo alert: telemetry failure detected across core nodes\n03:42:22 apollo alert: Global telemetry link severed\n03:43:01 apollo systemd: service watchdog timeout on phoenix-core\n",
                    "auth.log": "User alice session opened.\n"
                }
            }
        }
    }

    raw_missions = {
        1: {
            "title": "MISSION 1: Terminal Orientation",
            "description": "Initialize documentation, inspect workspace, and read starting instructions.",
            "tasks": {
                "open_help": {"desc": "Consult your active operator manual", "done": False},
                "list_contents": {"desc": "Inspect files and folders in current directory", "done": False},
                "read_file": {"desc": "Read the workstation instructions file", "done": False}
            }
        },
        2: {
            "title": "MISSION 2: Location & Navigation",
            "description": "Determine your working path, move into notes, and inspect the guide.",
            "tasks": {
                "run_pwd": {"desc": "Determine your exact location in the filesystem using 'pwd'", "done": False},
                "cd_folder": {"desc": "Navigate into the 'notes' directory using 'cd'", "done": False},
                "read_new_file": {"desc": "Read 'sysadmin_notes.txt' to learn core syntax", "done": False}
            }
        },
        3: {
            "title": "MISSION 3: Subsystem Navigation",
            "description": "Navigate to the root log directory and inspect its files.",
            "tasks": {
                "nav_logs": {"desc": "Navigate to the system log directory (/var/log)", "done": False},
                "list_logs": {"desc": "List the contents of the log directory", "done": False}
            }
        },
        4: {
            "title": "MISSION 4: Log Analysis",
            "description": "Search system logs using pattern matching to isolate failed services.",
            "tasks": {
                "grep_logs": {"desc": "Filter log data for 'phoenix' via grep or pipelines", "done": False}
            }
        },
        5: {
            "title": "MISSION 5: Root Subsystem Scan",
            "description": "Scan from root or /opt to find configuration files matching '*.conf'.",
            "tasks": {
                "find_configs": {"desc": "Locate configuration files using a wildcard search pattern", "done": False}
            }
        }
    }

    bus = EventBus()
    vfs = VirtualFilesystem(raw_fs)
    state = TerminalState(vfs, bus, initial_path=["home", "alice"])
    engine = MissionEngine(raw_missions, bus)
    ctx = CommandContext(state=state, vfs=vfs, engine=engine, bus=bus)
    return ctx

def main():
    ctx = create_environment()

    command_table = {
        "pwd": cmd_pwd,
        "echo": cmd_echo,
        "ls": cmd_ls,
        "cd": cmd_cd,
        "cat": cmd_cat,
        "cp": cmd_cp,
        "tree": cmd_tree,
        "grep": cmd_grep,
        "find": cmd_find,
        "objectives": lambda c, a: (c.engine.print_objectives(), CommandResult())[1],
        "goals": lambda c, a: (c.engine.print_objectives(), CommandResult())[1],
        "help": lambda c, a: (
            c.bus.publish(Event("command_executed", {"command": "help"})),
            c.engine.print_help(),
            CommandResult()
        )[2],
        "exit": lambda c, a: sys.exit(0)
    }

    executor = ShellExecutor(ctx, command_table)

    print("=" * 60)
    print("           APOLLO INCIDENT RESPONSE TERMINAL v2.5")
    print("=" * 60)
    print("HOST: apollo | USER: alice | SECURITY STATE: DEGRADED")
    print("MESSAGE OF THE DAY:")
    print("  " + ctx.vfs.fs["/"]["etc"]["motd"])
    print("=" * 60)
    print("Type 'help' to consult your manual or 'objectives' to check tasks.\n")

    while True:
        prompt_path = "~" if ctx.state.current_path == ["home", "alice"] else ctx.state.cwd_str
        try:
            raw_input = input(f"alice@apollo:{prompt_path}$ ")
        except (KeyboardInterrupt, EOFError):
            print("\nSession terminated.")
            break

        pipelines = ShellParser.parse_line(raw_input, ctx)
        if not pipelines:
            continue

        for pipeline in pipelines:
            exit_code = executor.execute_pipeline(pipeline)
            if exit_code != 0:
                break

if __name__ == "__main__":
    main()