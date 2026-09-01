import sys
import os
import shlex
import fnmatch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

# =====================================================================
# 1. EVENT SYSTEM & BUS
# =====================================================================

@dataclass
class Event:
    type: str
    data: Dict[str, Any] = field(default_factory=dict)

class EventBus:
    def __init__(self):
        self._listeners = []

    def subscribe(self, listener):
        self._listeners.append(listener)

    def publish(self, event: Event):
        for listener in self._listeners:
            listener(event)

# =====================================================================
# 2. VIRTUAL FILESYSTEM & STATE LAYER
# =====================================================================

class VirtualFilesystem:
    def __init__(self, raw_fs: dict):
        self.fs = raw_fs

    def resolve_path(self, current_path: List[str], target: str) -> List[str]:
        if target.startswith("/"):
            tokens = [t for t in target.strip("/").split("/") if t]
        else:
            tokens = current_path.copy()
            for part in target.split("/"):
                if not part or part == ".":
                    continue
                elif part == "..":
                    if tokens:
                        tokens.pop()
                else:
                    tokens.append(part)
        return tokens

    def get_node(self, path: List[str]) -> Optional[Any]:
        node = self.fs["/"]
        for segment in path:
            if isinstance(node, dict) and segment in node:
                node = node[segment]
            else:
                return None
        return node

    def list_dir(self, path: List[str], show_all: bool = False) -> Optional[List[str]]:
        node = self.get_node(path)
        if not isinstance(node, dict):
            return None
        entries = sorted(node.keys())
        out = []
        for name in entries:
            if not show_all and name.startswith("."):
                continue
            is_dir = isinstance(node[name], dict)
            out.append(name + ("/" if is_dir else ""))
        return out

    def read_file(self, path: List[str]) -> Optional[str]:
        if not path:
            return None
        parent = self.get_node(path[:-1])
        file_name = path[-1]
        if isinstance(parent, dict) and file_name in parent:
            item = parent[file_name]
            if isinstance(item, str):
                return item
        return None

    def write_file(self, path: List[str], content: str, append: bool = False) -> bool:
        if not path:
            return False
        parent = self.get_node(path[:-1])
        file_name = path[-1]
        if isinstance(parent, dict):
            if file_name in parent and isinstance(parent[file_name], dict):
                return False
            if append and file_name in parent and isinstance(parent[file_name], str):
                parent[file_name] += content
            else:
                parent[file_name] = content
            return True
        return False

    def traverse(self, start_tokens: List[str]):
        node = self.get_node(start_tokens)
        if node is None:
            return

        base_prefix = "" if not start_tokens else ("/" + "/".join(start_tokens))

        def _walk(curr_node, curr_dir):
            for k, v in curr_node.items():
                full = f"{curr_dir}/{k}"
                if isinstance(v, dict):
                    yield (full, True)
                    yield from _walk(v, full)
                else:
                    yield (full, False)

        if isinstance(node, dict):
            yield from _walk(node, base_prefix)
        else:
            yield (base_prefix, False)

class TerminalState:
    def __init__(self, vfs: VirtualFilesystem, event_bus: EventBus, initial_path: List[str]):
        self.vfs = vfs
        self.bus = event_bus
        self.current_path = initial_path
        self.env: Dict[str, str] = {
            "USER": "alice",
            "HOME": "/home/alice",
            "HOST": "apollo",
            "TERM": "xterm-256color"
        }
        self.visited_paths: Set[str] = set()
        self._record_visit(self.current_path)

    @property
    def cwd_str(self) -> str:
        return "/" + "/".join(self.current_path)

    def _record_visit(self, path_tokens: List[str]):
        accum = ""
        for seg in path_tokens:
            accum += "/" + seg
            self.visited_paths.add(accum)
        if not path_tokens:
            self.visited_paths.add("/")

    def change_directory(self, target: Optional[str] = None) -> Tuple[bool, str]:
        if not target:
            self.current_path = ["home", "alice"]
            self._record_visit(self.current_path)
            self.bus.publish(Event("directory_changed", {"path": self.cwd_str}))
            return True, ""

        new_path = self.vfs.resolve_path(self.current_path, target)
        node = self.vfs.get_node(new_path)

        if node is None:
            return False, f"cd: {target}: No such file or directory\n[LEARNING TIP] Use 'ls' to check names. Folders end with a slash '/'."
        if not isinstance(node, dict):
            return False, f"cd: {target}: Not a directory\n[LEARNING TIP] '{target}' is a file, not a directory. Use 'cat {target}' to read files."

        self.current_path = new_path
        self._record_visit(self.current_path)
        self.bus.publish(Event("directory_changed", {"path": self.cwd_str, "target": target}))
        return True, ""

# =====================================================================
# 3. MISSION & EVENT OBSERVER LAYER
# =====================================================================

class MissionEngine:
    def __init__(self, missions: dict, event_bus: EventBus):
        self.missions = missions
        self.current_mission = 1
        self.discovered_commands: Set[str] = {"help", "ls", "cat", "echo", "objectives"}
        self.command_docs = {
            "ls": "ls [-a]                  List visible files (-a reveals hidden files)",
            "cat": "cat <file>               Display or pass text file contents",
            "echo": "echo <text>              Print text or variables ($USER, $HOME)",
            "pwd": "pwd                      Print current working directory path",
            "cd": "cd <path>                Navigate between directories (use 'cd ..' to go back)",
            "tree": "tree                     Visual tree map of explored directories",
            "grep": "grep <pattern> [file]    Filter input or files matching a pattern",
            "find": "find <path> -name <ptn>  Search for files by pattern across directory trees",
            "help": "help                     Display this discovered commands manual",
            "objectives": "objectives               Display active mission goals and status"
        }
        self.command_cards = {
            "pwd": "┌──────────────────────────────────────────────────────────┐\n│ NEW COMMAND DISCOVERED: pwd                              │\n│ 'Print Working Directory' — Shows your current location. │\n└──────────────────────────────────────────────────────────┘",
            "ls_all": "┌──────────────────────────────────────────────────────────┐\n│ NEW OPTION DISCOVERED: ls -a                             │\n│ Displays all entries, including hidden files/folders (.).│\n└──────────────────────────────────────────────────────────┘",
            "cd": "┌──────────────────────────────────────────────────────────┐\n│ NEW COMMAND DISCOVERED: cd                               │\n│ 'Change Directory' — Move into folders or up (cd ..).    │\n└──────────────────────────────────────────────────────────┘",
            "tree": "┌──────────────────────────────────────────────────────────┐\n│ NEW COMMAND DISCOVERED: tree                             │\n│ Displays a graphical tree of explored directories.       │\n└──────────────────────────────────────────────────────────┘",
            "grep": "┌──────────────────────────────────────────────────────────┐\n│ NEW COMMAND DISCOVERED: grep                             │\n│ 'Global Regular Expression Print' — Filters text streams │\n│ or files for lines containing matching patterns.         │\n└──────────────────────────────────────────────────────────┘",
            "find": "┌──────────────────────────────────────────────────────────┐\n│ NEW COMMAND DISCOVERED: find                             │\n│ Searches directory trees for files matching criteria.    │\n└──────────────────────────────────────────────────────────┘"
        }
        event_bus.subscribe(self.handle_event)

    def trigger_card(self, card_key: str, base_cmd: Optional[str] = None):
        if card_key in self.command_cards and card_key not in self.discovered_commands:
            print("\n" + self.command_cards[card_key] + "\n")
            self.discovered_commands.add(card_key)
        reg_cmd = base_cmd or card_key
        self.discovered_commands.add(reg_cmd)

    def handle_event(self, event: Event):
        # Auto-discover cards
        if event.type == "command_executed":
            cmd = event.data.get("command")
            if cmd in self.command_cards:
                self.trigger_card(cmd)
            if cmd == "ls" and event.data.get("show_all"):
                self.trigger_card("ls_all", base_cmd="ls")
        if event.type == "file_read" and event.data.get("path") == "/home/alice/notes/mapping_tool.txt":
            self.trigger_card("tree")

        # OUTCOME-BASED OBJECTIVE EVALUATION
        if self.current_mission == 1:
            if event.type == "command_executed" and event.data.get("command") == "help":
                self.missions[1]["tasks"]["open_help"]["done"] = True
            elif event.type == "directory_listed":
                self.missions[1]["tasks"]["list_contents"]["done"] = True
            elif event.type == "file_read" and event.data.get("path") == "/home/alice/readme.txt":
                self.missions[1]["tasks"]["read_file"]["done"] = True

        elif self.current_mission == 2:
            if event.type == "command_executed" and event.data.get("command") == "pwd":
                self.missions[2]["tasks"]["run_pwd"]["done"] = True
            elif event.type == "directory_changed" and event.data.get("path") == "/home/alice/notes":
                self.missions[2]["tasks"]["cd_folder"]["done"] = True
            elif event.type == "file_read" and event.data.get("path") == "/home/alice/notes/sysadmin_notes.txt":
                self.missions[2]["tasks"]["read_new_file"]["done"] = True

        elif self.current_mission == 3:
            if event.type == "directory_changed" and event.data.get("path") == "/var/log":
                self.missions[3]["tasks"]["nav_logs"]["done"] = True
            elif event.type == "directory_listed" and event.data.get("path") == "/var/log":
                self.missions[3]["tasks"]["list_logs"]["done"] = True

        elif self.current_mission == 4:
            if event.type == "pattern_searched":
                file_path = event.data.get("file", "")
                matches = event.data.get("matches", [])
                
                # Check Outcome: Did they successfully isolate the target failure line?
                # This works for `grep phoenix`, `grep terminated`, `grep systemd`, etc.
                target_found = any("phoenix-sync service terminated" in line for line in matches)
                
                # Ensure they actually filtered (didn't just return all 6 log lines)
                if file_path == "/var/log/system.log" and target_found and len(matches) < 5:
                    self.missions[4]["tasks"]["grep_logs"]["done"] = True

        elif self.current_mission == 5:
            if event.type == "files_searched":
                matches = event.data.get("matches", [])
                # Check Outcome: Did their scan locate the specific emergency config file?
                if "/opt/phoenix/config/phoenix.conf" in matches:
                    self.missions[5]["tasks"]["find_configs"]["done"] = True

        self.check_completion()

    def check_completion(self):
        if self.current_mission not in self.missions:
            return
        m = self.missions[self.current_mission]
        if all(task["done"] for task in m["tasks"].values()):
            print("\n" + "=" * 60)
            print(f" ★ LEVEL COMPLETE: {m['title']} ★")
            print("=" * 60)
            self.current_mission += 1
            if self.current_mission in self.missions:
                next_m = self.missions[self.current_mission]
                print(f"\n[NEXT OBJECTIVE UNLOCKED] -> {next_m['title']}")
                print(f"Goal: {next_m['description']}")
                print("Type 'objectives' to review current goals.\n")
            else:
                print("\n★★★ ALL CAMPAIGN MISSIONS COMPLETE — GLOBAL NETWORK RESTORED! ★★★\n")

    def print_objectives(self):
        if self.current_mission not in self.missions:
            print("All system objectives restored.")
            return
        m = self.missions[self.current_mission]
        print("\n" + "=" * 60)
        print(f" {m['title']}")
        print(f" {m['description']}")
        print("-" * 60)
        print(" STATUS:")
        for task in m["tasks"].values():
            status = "[X]" if task["done"] else "[ ]"
            print(f"   {status} {task['desc']}")
        print("=" * 60 + "\n")

    def print_help(self):
        print("DISCOVERED COMMANDS:")
        for cmd in sorted(self.discovered_commands):
            if cmd in self.command_docs:
                print(f"  {self.command_docs[cmd]}")
        print("  exit                     Terminate the terminal session")

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

def cmd_tree(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "tree"}))
    lines = ["/"]

    def _render(node, curr_dir="", prefix=""):
        items = sorted(node.keys())
        visible = []
        for it in items:
            it_path = f"{curr_dir}/{it}" if curr_dir != "/" else f"/{it}"
            if isinstance(node[it], dict):
                if any(vp == it_path or vp.startswith(it_path + "/") for vp in ctx.state.visited_paths):
                    visible.append(it)
            else:
                if curr_dir in ctx.state.visited_paths:
                    visible.append(it)

        for i, it in enumerate(visible):
            is_last = (i == len(visible) - 1)
            connector = "└── " if is_last else "├── "
            val = node[it]
            it_path = f"{curr_dir}/{it}" if curr_dir != "/" else f"/{it}"
            if isinstance(val, dict):
                lines.append(f"{prefix}{connector}{it}/")
                _render(val, it_path, prefix + ("    " if is_last else "│   "))
            else:
                lines.append(f"{prefix}{connector}{it}")

    _render(ctx.vfs.fs["/"], curr_dir="/")
    return CommandResult(stdout="\n".join(lines) + "\n")

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

            if atomic.redirect_in:
                tokens = self.ctx.vfs.resolve_path(self.ctx.state.current_path, atomic.redirect_in)
                content = self.ctx.vfs.read_file(tokens)
                if content is None:
                    print(f"apollo-sh: {atomic.redirect_in}: No such file")
                    return 1
                pipeline_input = content

            self.ctx.stdin = pipeline_input

            if cmd_name in self.commands:
                result: CommandResult = self.commands[cmd_name](self.ctx, cmd_args)
            elif cmd_name in ["list", "dir"]:
                print(f"{cmd_name}: command not found\n[LEARNING TIP] Linux uses 'ls' to list files.")
                return 127
            elif cmd_name in ["type", "read", "open"]:
                print(f"{cmd_name}: command not found\n[LEARNING TIP] Linux uses 'cat' to display text files.")
                return 127
            elif cmd_name in ["search", "locate"]:
                print(f"{cmd_name}: command not found\n[LEARNING TIP] Use 'grep' or 'find'.")
                return 127
            else:
                print(f"{cmd_name}: command not found\n[LEARNING TIP] Type 'help' to review discovered commands.")
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
                        "recovery.sh": "#!/bin/bash\necho 'Restoring core nodes...'"
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