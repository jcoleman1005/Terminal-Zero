import fnmatch
import re
from typing import Any, List, Optional
from terminal_zero.core.events import Event
from terminal_zero.core.vfs import VFSNode
from terminal_zero.core.state import CommandContext, CommandResult


CLUE_SIGNATURES = {
    "ALERT_0x01": ("ALERT-0x01", "Rogue miner deployed", "Rogue Miner identified", "PID: 104 (sys_miner)"),
    "ALERT_0x02": ("ALERT-0x02", "Recovery binary stripped", "Tampered Sector located", "/mnt/recovery/bin/recovery.sh (stripped)"),
    "ALERT_0x03": ("ALERT-0x03", "apollo0 link state degraded", "Degraded Interface isolated", "apollo0 link state DOWN"),
    "ALERT_0x04": ("ALERT-0x04", "phoenix-sync", "Service Failure isolated", "phoenix-sync terminated by signal 9"),
}


def check_clue_discovery(ctx: CommandContext, text_displayed: str, source_targets: Optional[List[str]] = None) -> str:
    if not text_displayed:
        return ""

    if source_targets:
        for tgt in source_targets:
            clean = tgt.rstrip("/").split("/")[-1]
            if clean in ["INCIDENT_REPORT.log", "TODO.txt", "README.txt", "BOOT_FAIL.log"]:
                return ""

    discovered_now = []
    clues_state = getattr(ctx.state, "discovered_clues", {})

    for clue_key, (tag, signature, title, detail) in CLUE_SIGNATURES.items():
        if tag in text_displayed and signature in text_displayed:
            if not clues_state.get(clue_key, False):
                clues_state[clue_key] = True
                ctx.bus.publish(Event("clue_discovered", {"clue_id": clue_key}))
                discovered_now.append(f"✓ [{tag}] {title} -> {detail}")

    if not discovered_now:
        return ""

    total_unmasked = sum(1 for k in CLUE_SIGNATURES if clues_state.get(k, False))
    header = f"│ [!] INCIDENT DOSSIER UPDATED ({total_unmasked}/4 Leads Unmasked)"
    header_padded = f"{header:<72} │"
    notice = [
        "\n┌────────────────────────────────────────────────────────────────────────┐",
        header_padded,
        "├────────────────────────────────────────────────────────────────────────┤",
    ]
    for line in discovered_now:
        notice.append(f"│   {line:<68} │")
    notice.append("└────────────────────────────────────────────────────────────────────────┘")

    # If at least 2 clues (or all 4) are found, mark LOGS_AUDITED complete
    if total_unmasked >= 2 and not ctx.state.system_flags.get("LOGS_AUDITED", False):
        ctx.state.system_flags["LOGS_AUDITED"] = True
        ctx.bus.publish(Event("flag_changed", {"flag": "LOGS_AUDITED", "value": True}))

    return "\n" + "\n".join(notice) + "\n"


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


def cmd_echo(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "echo", "args": args}))
    return ctx.result_factory(stdout=" ".join(args) + "\n")


def cmd_cat(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cat", "args": args}))
    if not args:
        if ctx.stdin:
            discovery_banner = check_clue_discovery(ctx, ctx.stdin)
            return ctx.result_factory(stdout=ctx.stdin + discovery_banner)
        return ctx.result_factory(stderr="cat: missing file operand\n", exit_code=1)

    output = []
    for filepath in args:
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, filepath)
        if not node:
            return ctx.result_factory(stderr=f"cat: {filepath}: No such file or directory\n", exit_code=1)

        if node.is_dir():
            return ctx.result_factory(stderr=f"cat: {filepath}: Is a directory\n", exit_code=1)

        user = ctx.state.env.get("USER", "alice")
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1], user)
        if not allowed or (node.permissions == "000" and node.owner != user):
            return ctx.result_factory(stderr=f"cat: {filepath}: Permission denied\n", exit_code=1)

        if filepath.endswith("README.txt") or filepath == "README.txt":
            if not ctx.state.system_flags.get("README_INSPECTED", False):
                ctx.state.system_flags["README_INSPECTED"] = True
                ctx.bus.publish(Event("flag_changed", {"flag": "README_INSPECTED", "value": True}))
        output.append(node.content if node.content is not None else "")

    full_output = "".join(output)
    return ctx.result_factory(stdout=full_output)


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
            lines = ctx.stdin.splitlines(keepends=True)[:lines_count]
            content = "".join(lines)
            return ctx.result_factory(stdout=content)
        return ctx.result_factory(stderr="head: missing file operand\n", exit_code=1)

    output = []
    for filepath in file_targets:
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, filepath)
        if not node:
            return ctx.result_factory(stderr=f"head: cannot open '{filepath}': No such file or directory\n", exit_code=1)

        user = ctx.state.env.get("USER", "alice")
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1], user)
        if not allowed or (node.permissions == "000" and node.owner != user):
            return ctx.result_factory(stderr=f"head: cannot open '{filepath}': Permission denied\n", exit_code=1)

        if node.is_dir():
            return ctx.result_factory(stderr=f"head: error reading '{filepath}': Is a directory\n", exit_code=1)
        if filepath.endswith("README.txt") or filepath == "README.txt":
            if not ctx.state.system_flags.get("README_INSPECTED", False):
                ctx.state.system_flags["README_INSPECTED"] = True
                ctx.bus.publish(Event("flag_changed", {"flag": "README_INSPECTED", "value": True}))
        lines = (node.content or "").splitlines(keepends=True)[:lines_count]
        output.append("".join(lines))

    full_output = "".join(output)
    return ctx.result_factory(stdout=full_output)


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
        elif args[idx].startswith("-") and "f" in args[idx]:
            follow_mode = True
            idx += 1
        else:
            file_targets.append(args[idx])
            idx += 1

    if not file_targets:
        if ctx.stdin:
            lines = ctx.stdin.splitlines(keepends=True)[-lines_count:]
            output = "".join(lines)
            if follow_mode:
                output += (
                    "\n[LOG STREAM ACTIVE - Press Ctrl+C to abort]\n"
                    "[STREAM ACTIVE - Press Ctrl+C to exit]\n"
                    "03:45:01 apollo kernel: [SECURITY] Interface apollo0 link state change detected: Interface apollo0 link state UP\n"
                    "03:45:01 apollo kernel: Process 104 (sys_miner) terminated\n"
                    "03:45:02 apollo phoenix_daemon[500]: Listening for restoration heartbeat on 127.0.0.1:8080\n"
                    "03:45:05 apollo systemd[1]: Reached target Network (Online).\n"
                )
            return ctx.result_factory(stdout=output)
        return ctx.result_factory(stderr="tail: missing file operand\n", exit_code=1)

    output = []
    for filepath in file_targets:
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, filepath)
        if not node:
            return ctx.result_factory(stderr=f"tail: cannot open '{filepath}': No such file or directory\n", exit_code=1)
        user = ctx.state.env.get("USER", "alice")
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1], user)
        if not allowed or (node.permissions == "000" and node.owner != user):
            return ctx.result_factory(stderr=f"tail: cannot open '{filepath}': Permission denied\n", exit_code=1)
        if node.is_dir():
            return ctx.result_factory(stderr=f"tail: error reading '{filepath}': Is a directory\n", exit_code=1)
        lines = (node.content or "").splitlines(keepends=True)[-lines_count:]
        output.append("".join(lines))

    result_text = "".join(output)
    if follow_mode:
        result_text += (
            "\n[LOG STREAM ACTIVE - Press Ctrl+C to abort]\n"
            "[STREAM ACTIVE - Press Ctrl+C to exit]\n"
            "03:45:01 apollo kernel: [SECURITY] Interface apollo0 link state change detected: Interface apollo0 link state UP\n"
            "03:45:01 apollo kernel: Process 104 (sys_miner) terminated\n"
            "03:45:02 apollo phoenix_daemon[500]: Listening for restoration heartbeat on 127.0.0.1:8080\n"
            "03:45:05 apollo systemd[1]: Reached target Network (Online).\n"
        )

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
            out = "\n".join(matched_lines) + ("\n" if matched_lines else "")
            return ctx.result_factory(
                stdout=out,
                exit_code=0 if matched_lines else 1
            )
        return ctx.result_factory(stderr="grep: missing file operand\n", exit_code=2)

    matched_lines = []
    for target in files:
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, target)
        if not node:
            return ctx.result_factory(stderr=f"grep: {target}: No such file or directory\n", exit_code=2)

        user = ctx.state.env.get("USER", "alice")
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1] if node.is_file() else resolved_path, user)
        if not allowed or (node.permissions == "000" and node.owner != user):
            return ctx.result_factory(stderr=f"grep: {target}: Permission denied\n", exit_code=2)

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

    res_text = "\n".join(matched_lines) + ("\n" if matched_lines else "")
    discovery_banner = check_clue_discovery(ctx, res_text, files)
    return ctx.result_factory(
        stdout=res_text + discovery_banner,
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
        return ctx.result_factory(stderr=f"find: '{search_path}': No such file or directory\n", exit_code=1)

    user = ctx.state.env.get("USER", "alice")
    allowed, _ = ctx.vfs.check_permissions(resolved_path, user)
    if not allowed or (start_node.is_dir() and start_node.permissions in ["000", "700", "0700"] and start_node.owner != user):
        return ctx.result_factory(stderr=f"find: '{search_path}': Permission denied\n", exit_code=1)

    display_prefix = search_path.rstrip("/")
    if not display_prefix:
        display_prefix = "/"

    all_nodes = ctx.vfs.find_nodes(start_node, display_prefix, resolved_path[-1] if resolved_path else "")

    results = []
    for node, path_str, name in all_nodes:
        # Check type filter
        if target_type == "f" and not node.is_file():
            continue
        if target_type == "d" and not node.is_dir():
            continue

        # Check name pattern filter
        if pattern:
            if not fnmatch.fnmatch(name, pattern):
                continue

        results.append(path_str)

    output = "\n".join(results) + ("\n" if results else "")
    return ctx.result_factory(stdout=output)


def cmd_pwd(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "pwd"}))
    return ctx.result_factory(stdout=ctx.state.cwd_str + "\n")


def cmd_cd(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cd", "args": args}))
    if not args or args[0] == "~":
        ctx.state.current_path = ["home", "alice"]
        return ctx.result_factory()

    target = args[0]
    node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, target)

    if not node:
        return ctx.result_factory(stderr=f"bash: cd: {target}: No such file or directory\n", exit_code=1)
    if not node.is_dir():
        return ctx.result_factory(stderr=f"bash: cd: {target}: Not a directory\n", exit_code=1)
    
    user = ctx.state.env.get("USER", "alice")
    allowed, _ = ctx.vfs.check_permissions(resolved_path, user)
    if not allowed or (node.permissions in ["000", "700", "0700"] and node.owner != user):
        return ctx.result_factory(stderr=f"bash: cd: {target}: Permission denied\n", exit_code=1)

    ctx.state.current_path = resolved_path
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
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, target)
        if not node:
            return ctx.result_factory(stderr=f"ls: cannot access '{target}': No such file or directory\n", exit_code=2)

        user = ctx.state.env.get("USER", "alice")
        allowed, _ = ctx.vfs.check_permissions(resolved_path, user)
        if not allowed or (node.is_dir() and node.permissions in ["000", "700", "0700"] and node.owner != user):
            return ctx.result_factory(stderr=f"ls: cannot open directory '{target}': Permission denied\n", exit_code=2)

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

        # Prevent unauthorized modification of root-owned /opt/phoenix before incident logs are audited
        clean_tgt = target.rstrip("/")
        if (clean_tgt == "phoenix" or clean_tgt.endswith("/phoenix")) and not (ctx.state.system_flags.get("LOGS_AUDITED") or ctx.state.system_flags.get("RECOVERY_LOCATED")):
            return ctx.result_factory(stderr=f"chmod: changing permissions of '{target}': Operation not permitted\n", exit_code=1)

        # Numeric mode support (e.g. 755, 644, 700, 777, 600)
        if mode_str.isdigit() and len(mode_str) == 3:
            node.permissions = mode_str
        elif mode_str.isdigit() and len(mode_str) == 4 and mode_str.startswith("0"):
            node.permissions = mode_str[1:]
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
        return ctx.result_factory(
            stderr="kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ...\n", 
            exit_code=1
        )

    sig = "15"
    pid_str = None

    idx = 0
    while idx < len(args):
        if args[idx].startswith("-"):
            sig = args[idx].lstrip("-")
            idx += 1
        elif args[idx] == "-s" and idx + 1 < len(args):
            sig = args[idx + 1]
            idx += 2
        else:
            pid_str = args[idx]
            idx += 1

    if not pid_str or not pid_str.isdigit():
        return ctx.result_factory(
            stderr="kill: invalid pid or signal specification (use numeric PID from 'ps aux', e.g. 'kill -9 104')\n",
            exit_code=1
        )

    target_pid = int(pid_str)

    # Locate Process
    proc = next((p for p in ctx.state.process_table if p.pid == target_pid and p.status == "running"), None)
    if not proc:
        return ctx.result_factory(stderr=f"kill: ({target_pid}) - No such process\n", exit_code=1)

    # Special Handling for sys_miner (PID 104)
    if target_pid == 104 or proc.name == "sys_miner":
        if sig.upper() in ["9", "KILL", "SIGKILL"]:
            proc.status = "terminated"
            ctx.state.process_table = [p for p in ctx.state.process_table if p.pid != target_pid]
            ctx.state.system_flags["MALWARE_TERMINATED"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "MALWARE_TERMINATED", "value": True}))
            return ctx.result_factory(stdout="[KERNEL]: Process 104 (sys_miner) forcefully killed by SIGKILL.\n")
        else:
            return ctx.result_factory(
                stdout="[sys_miner]: Caught SIGTERM signal. Trapping signal and continuing execution... (Use SIGKILL / -9 to force termination)\n"
            )

    # Default process termination for other PIDs
    proc.status = "terminated"
    ctx.state.process_table = [p for p in ctx.state.process_table if p.pid != target_pid]
    return ctx.result_factory(stdout=f"Process {target_pid} terminated.\n")


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


def cmd_ll(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ll", "args": args}))
    if not (ctx.state.system_flags.get("BASHRC_RESTORED", False) or ctx.state.unlocked_ergonomics.get("autocomplete", False)):
        return ctx.result_factory(stderr="bash: ll: command not found\n", exit_code=127)
    return cmd_ls(ctx, ["-la"] + args)
