import fnmatch
import re
from typing import Any, List, Optional
from terminal_zero.core.events import Event
from terminal_zero.core.vfs import VFSNode
from terminal_zero.core.state import CommandContext, CommandResult


CLUE_SIGNATURES = {
    "ALERT_0x01": ("ALERT-0x01", "Rogue miner deployed", "Rogue Miner identified", "PID: 104 (sys_miner)"),
    "ALERT_0x02": ("ALERT-0x02", "Recovery binary stripped", "Tampered Sector located", "/mnt/recovery/bin/recovery.sh (stripped)"),
    "ALERT_0x03": ("ALERT-0x03", "osiris0 link state degraded", "Degraded Interface isolated", "osiris0 link state DOWN"),
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


def cmd_stty(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "stty", "args": args}))
    raw_args = " ".join(args).lower().strip()
    if "sane" in raw_args or ("icanon" in raw_args and "echo" in raw_args):
        ctx.state.unlocked_ergonomics["history"] = True
        ctx.state.unlocked_ergonomics["history_arrows"] = True
        ctx.state.system_flags["BUFFER_REPAIRED"] = True
        ctx.bus.publish(Event("flag_changed", {"flag": "BUFFER_REPAIRED", "value": True}))
        return ctx.result_factory(stdout="[stty]: Line discipline reset to sane defaults. Cooked mode and input buffer active.\n")
    elif not args or args == ["-a"]:
        mode_status = "icanon echo" if ctx.state.system_flags.get("BUFFER_REPAIRED", False) else "-icanon -echo (raw/degraded)"
        return ctx.result_factory(stdout=f"speed 38400 baud; rows 24; columns 80; line = 0;\nmode: {mode_status}\n")
    else:
        return ctx.result_factory(stdout=f"[stty]: Settings applied: {' '.join(args)}\n")


def cmd_rm(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "rm", "args": args}))
    if not args:
        return ctx.result_factory(stderr="rm: missing operand\n", exit_code=1)

    recursive = False
    force = False
    targets = []
    for arg in args:
        if arg.startswith("-") and len(arg) > 1:
            if "r" in arg or "R" in arg:
                recursive = True
            if "f" in arg:
                force = True
        else:
            targets.append(arg)

    if not targets:
        return ctx.result_factory(stderr="rm: missing operand\n", exit_code=1)

    user = ctx.state.current_user
    for target in targets:
        target_node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, target)
        if not target_node:
            if force:
                continue
            return ctx.result_factory(stderr=f"rm: cannot remove '{target}': No such file or directory\n", exit_code=1)

        if target_node.is_dir() and not recursive:
            return ctx.result_factory(stderr=f"rm: cannot remove '{target}': Is a directory\n", exit_code=1)

        parent_parts = resolved_path[:-1]
        parent_node = ctx.vfs.root if not parent_parts else ctx.vfs.resolve_path(parent_parts)

        # Deletion Protection Check: containing directory permissions or root-owned read-only target
        if parent_node and (not ctx.vfs.can_write(parent_node, user) or not ctx.vfs.can_execute(parent_node, user)):
            return ctx.result_factory(
                stderr=f"rm: cannot remove '{target}': Permission denied\n",
                exit_code=1
            )
        if target_node.owner == "root" and not ctx.vfs.can_write(target_node, user):
            return ctx.result_factory(
                stderr=f"rm: cannot remove '{target}': Permission denied\n",
                exit_code=1
            )

        success, err = ctx.vfs.delete_node(ctx.state.current_path, target, recursive=recursive, user=user)
        if not success:
            if force and "No such file or directory" in err:
                continue
            return ctx.result_factory(stderr=f"rm: {err}\n", exit_code=1)

    return ctx.result_factory()


def cmd_cp(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cp", "args": args}))
    if not args:
        return ctx.result_factory(stderr="cp: missing file operand\n", exit_code=1)

    recursive = False
    clean_args = []
    for arg in args:
        if arg.startswith("-") and len(arg) > 1:
            if "r" in arg or "R" in arg or "a" in arg:
                recursive = True
        else:
            clean_args.append(arg)

    if len(clean_args) < 2:
        return ctx.result_factory(stderr="cp: missing destination file operand\n", exit_code=1)

    src_path = clean_args[0]
    dest_path = clean_args[1]

    src_node, _ = ctx.vfs.get_node(ctx.state.current_path, src_path)
    if not src_node:
        return ctx.result_factory(stderr=f"cp: cannot stat '{src_path}': No such file or directory\n", exit_code=1)

    user = ctx.state.current_user
    if not ctx.vfs.can_read(src_node, user):
        return ctx.result_factory(stderr=f"cp: cannot open '{src_path}' for reading: Permission denied\n", exit_code=1)

    if src_node.is_dir() and not recursive:
        return ctx.result_factory(stderr=f"cp: -r not specified; omitting directory '{src_path}'\n", exit_code=1)

    dest_node, resolved_dest = ctx.vfs.get_node(ctx.state.current_path, dest_path)
    if dest_node and dest_node.is_dir():
        src_filename = src_path.rstrip("/").split("/")[-1]
        final_dest = f"{dest_path.rstrip('/')}/{src_filename}"
    else:
        final_dest = dest_path

    # Check permission to write at destination
    actual_dest_node, actual_resolved_dest = ctx.vfs.get_node(ctx.state.current_path, final_dest)
    if actual_dest_node:
        if not ctx.vfs.can_write(actual_dest_node, user):
            return ctx.result_factory(stderr=f"cp: cannot create regular file '{final_dest}': Permission denied\n", exit_code=1)
    else:
        parent_parts = actual_resolved_dest[:-1]
        parent_node = ctx.vfs.root if not parent_parts else ctx.vfs.resolve_path(parent_parts)
        if not parent_node or not parent_node.is_dir():
            return ctx.result_factory(stderr=f"cp: cannot create regular file '{final_dest}': No such file or directory\n", exit_code=1)
        if not ctx.vfs.can_write(parent_node, user):
            return ctx.result_factory(stderr=f"cp: cannot create regular file '{final_dest}': Permission denied\n", exit_code=1)

    if src_node.is_dir():
        def _copy_tree(src: VFSNode, dst_parent: VFSNode, dirname: str):
            new_dir = VFSNode(type="dir", permissions="755", owner=user, group=user)
            dst_parent.children[dirname] = new_dir
            for c_name, c_node in src.children.items():
                if c_node.is_dir():
                    _copy_tree(c_node, new_dir, c_name)
                else:
                    d_mode = "0644"
                    try:
                        m = int(c_node.permissions, 8) if (c_node.permissions and c_node.permissions.isdigit()) else 0
                        if m & 0o111:
                            d_mode = "0755"
                    except ValueError:
                        pass
                    new_dir.children[c_name] = VFSNode(type="file", permissions=d_mode, owner=user, group=user, content=c_node.content)

        dest_parent_parts = actual_resolved_dest[:-1]
        dest_parent_node = ctx.vfs.root if not dest_parent_parts else ctx.vfs.resolve_path(dest_parent_parts)
        if not dest_parent_node or not dest_parent_node.is_dir():
            return ctx.result_factory(stderr=f"cp: cannot create directory '{final_dest}': No such file or directory\n", exit_code=1)
        _copy_tree(src_node, dest_parent_node, actual_resolved_dest[-1])
        return ctx.result_factory()

    dest_perms = "0644"
    try:
        src_mode = int(src_node.permissions, 8) if (src_node.permissions and src_node.permissions.isdigit()) else 0
        if src_mode & 0o111:
            dest_perms = "0755"
    except ValueError:
        pass

    success, err = ctx.vfs.write_file(
        ctx.state.current_path,
        final_dest,
        src_node.content or "",
        append=False,
        owner=user,
        permissions=dest_perms,
        group=user,
        user=user
    )
    if not success:
        return ctx.result_factory(stderr=f"cp: cannot create regular file '{final_dest}': {err}\n", exit_code=1)

    written_node, _ = ctx.vfs.get_node(ctx.state.current_path, final_dest)
    if written_node:
        written_node.owner = user
        written_node.group = user

    return ctx.result_factory()


def cmd_touch(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "touch", "args": args}))
    if not args:
        return ctx.result_factory(stderr="touch: missing file operand\n", exit_code=1)

    user = ctx.state.current_user
    for target in args:
        if target.startswith("-"):
            continue
        node, _ = ctx.vfs.get_node(ctx.state.current_path, target)
        if node:
            continue
        success, err = ctx.vfs.write_file(
            ctx.state.current_path,
            target,
            "",
            append=False,
            owner=user,
            permissions="644",
            group=user,
            user=user
        )
        if not success:
            return ctx.result_factory(stderr=f"touch: cannot touch '{target}': {err}\n", exit_code=1)

    return ctx.result_factory()


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

        user = ctx.state.current_user
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1], user)
        if not allowed or not ctx.vfs.can_read(node, user):
            return ctx.result_factory(stderr=f"cat: {filepath}: Permission denied\n", exit_code=1)

        if filepath.endswith("README.txt") or filepath == "README.txt":
            if not ctx.state.system_flags.get("README_INSPECTED", False):
                ctx.state.system_flags["README_INSPECTED"] = True
                ctx.bus.publish(Event("flag_changed", {"flag": "README_INSPECTED", "value": True}))
        full_path_str = "/" + "/".join(resolved_path)
        if hasattr(ctx.state, "discovered_manuals"):
            ctx.state.discovered_manuals[full_path_str] = True
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

        user = ctx.state.current_user
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1], user)
        if not allowed or not ctx.vfs.can_read(node, user):
            return ctx.result_factory(stderr=f"head: cannot open '{filepath}': Permission denied\n", exit_code=1)

        if node.is_dir():
            return ctx.result_factory(stderr=f"head: error reading '{filepath}': Is a directory\n", exit_code=1)
        if filepath.endswith("README.txt") or filepath == "README.txt":
            if not ctx.state.system_flags.get("README_INSPECTED", False):
                ctx.state.system_flags["README_INSPECTED"] = True
                ctx.bus.publish(Event("flag_changed", {"flag": "README_INSPECTED", "value": True}))
        full_path_str = "/" + "/".join(resolved_path)
        if hasattr(ctx.state, "discovered_manuals"):
            ctx.state.discovered_manuals[full_path_str] = True
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
                    "03:45:01 osiris kernel: [SECURITY] Interface osiris0 link state change detected: Interface osiris0 link state UP\n"
                    "03:45:01 osiris kernel: Process 104 (sys_miner) terminated\n"
                    "03:45:02 osiris phoenix_daemon[500]: Listening for restoration heartbeat on 127.0.0.1:8080\n"
                    "03:45:05 osiris systemd[1]: Reached target Network (Online).\n"
                )
            return ctx.result_factory(stdout=output)
        return ctx.result_factory(stderr="tail: missing file operand\n", exit_code=1)

    output = []
    for filepath in file_targets:
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, filepath)
        if not node:
            return ctx.result_factory(stderr=f"tail: cannot open '{filepath}': No such file or directory\n", exit_code=1)
        user = ctx.state.current_user
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1], user)
        if not allowed or not ctx.vfs.can_read(node, user):
            return ctx.result_factory(stderr=f"tail: cannot open '{filepath}': Permission denied\n", exit_code=1)
        if node.is_dir():
            return ctx.result_factory(stderr=f"tail: error reading '{filepath}': Is a directory\n", exit_code=1)
        full_path_str = "/" + "/".join(resolved_path)
        if hasattr(ctx.state, "discovered_manuals"):
            ctx.state.discovered_manuals[full_path_str] = True
        lines = (node.content or "").splitlines(keepends=True)[-lines_count:]
        output.append("".join(lines))

    result_text = "".join(output)
    if follow_mode:
        result_text += (
            "\n[LOG STREAM ACTIVE - Press Ctrl+C to abort]\n"
            "[STREAM ACTIVE - Press Ctrl+C to exit]\n"
            "03:45:01 osiris kernel: [SECURITY] Interface osiris0 link state change detected: Interface osiris0 link state UP\n"
            "03:45:01 osiris kernel: Process 104 (sys_miner) terminated\n"
            "03:45:02 osiris phoenix_daemon[500]: Listening for restoration heartbeat on 127.0.0.1:8080\n"
            "03:45:05 osiris systemd[1]: Reached target Network (Online).\n"
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

        user = ctx.state.current_user
        allowed, _ = ctx.vfs.check_permissions(resolved_path[:-1] if node.is_file() else resolved_path, user)
        if not allowed or not ctx.vfs.can_read(node, user):
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
    idx = 0
    if args and not args[0].startswith("-"):
        search_path = args[0]
        idx = 1

    # Split remaining tokens into clauses separated by -o or -or
    clauses: List[List[str]] = [[]]
    while idx < len(args):
        tok = args[idx]
        if tok in ["-o", "-or"]:
            clauses.append([])
        else:
            clauses[-1].append(tok)
        idx += 1

    start_node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, search_path)
    if not start_node:
        return ctx.result_factory(stderr=f"find: '{search_path}': No such file or directory\n", exit_code=1)

    user = ctx.state.env.get("USER", "alice")
    allowed, _ = ctx.vfs.check_permissions(resolved_path, user)
    if not allowed or (start_node.is_dir() and start_node.permissions in ["000", "700", "0700"] and start_node.owner != user):
        return ctx.result_factory(stderr=f"find: '{search_path}': Permission denied\n", exit_code=1)

    if search_path.startswith("/"):
        display_prefix = "/" + "/".join(resolved_path) if resolved_path else "/"
    else:
        display_prefix = search_path.rstrip("/")
        if not display_prefix:
            display_prefix = "."

    all_nodes = ctx.vfs.find_nodes(start_node, display_prefix, resolved_path[-1] if resolved_path else "")

    parsed_clauses = []
    for clause in clauses:
        if not clause:
            continue
        predicates = []
        c_idx = 0
        while c_idx < len(clause):
            flag = clause[c_idx]
            if flag in ["-name", "-iname"]:
                if c_idx + 1 >= len(clause):
                    return ctx.result_factory(stderr=f"find: missing argument to `{flag}'\n", exit_code=1)
                pat = clause[c_idx + 1].strip('"').strip("'")
                case_fold = (flag == "-iname")
                if case_fold:
                    predicates.append(lambda n, p, name, pat=pat.lower(): fnmatch.fnmatch(name.lower(), pat))
                else:
                    predicates.append(lambda n, p, name, pat=pat: fnmatch.fnmatch(name, pat))
                c_idx += 2
            elif flag == "-type":
                if c_idx + 1 >= len(clause):
                    return ctx.result_factory(stderr="find: missing argument to `-type'\n", exit_code=1)
                t = clause[c_idx + 1]
                if t == "f":
                    predicates.append(lambda n, p, name: n.is_file())
                elif t == "d":
                    predicates.append(lambda n, p, name: n.is_dir())
                c_idx += 2
            else:
                return ctx.result_factory(stderr=f"find: unknown predicate `{flag}'\n", exit_code=1)
        parsed_clauses.append(predicates)

    results = []
    for node, path_str, name in all_nodes:
        if not parsed_clauses:
            matches = True
        else:
            matches = False
            for preds in parsed_clauses:
                if all(pred(node, path_str, name) for pred in preds):
                    matches = True
                    break
        if matches:
            if "phoenix.key" in path_str:
                ctx.state.system_flags["KEY_DISCOVERED"] = True
                ctx.bus.publish(Event("flag_changed", {"flag": "KEY_DISCOVERED", "value": True}))
            results.append(path_str)

    results.sort()
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


def mode_to_rwx(mode_str: str, is_dir: bool = False) -> str:
    try:
        mode = int(mode_str, 8) if (mode_str and mode_str.isdigit()) else 0
    except ValueError:
        mode = 0
    chars = []
    # User
    chars.append("r" if mode & 0o400 else "-")
    chars.append("w" if mode & 0o200 else "-")
    chars.append("x" if mode & 0o100 else "-")
    # Group
    chars.append("r" if mode & 0o040 else "-")
    chars.append("w" if mode & 0o020 else "-")
    chars.append("x" if mode & 0o010 else "-")
    # Other
    chars.append("r" if mode & 0o004 else "-")
    chars.append("w" if mode & 0o002 else "-")
    chars.append("x" if mode & 0o001 else "-")
    return "".join(chars)


def cmd_ls(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ls", "args": args}))
    show_all = False
    long_format = False
    targets = []

    for arg in args:
        if arg.startswith("-") and len(arg) > 1:
            if "a" in arg:
                show_all = True
            if "l" in arg:
                long_format = True
        else:
            targets.append(arg)

    if not targets:
        targets = ["."]

    output_blocks = []
    for target in targets:
        node, resolved_path = ctx.vfs.get_node(ctx.state.current_path, target)
        if not node:
            return ctx.result_factory(stderr=f"ls: cannot access '{target}': No such file or directory\n", exit_code=2)

        user = ctx.state.current_user
        allowed, _ = ctx.vfs.check_permissions(resolved_path, user)
        if not allowed or (node.is_dir() and node.permissions in ["000", "700", "0700"] and node.owner != user):
            return ctx.result_factory(stderr=f"ls: cannot open directory '{target}': Permission denied\n", exit_code=2)

        if node.is_file():
            if long_format:
                rwx = mode_to_rwx(node.permissions, False)
                grp = getattr(node, "group", node.owner)
                output_blocks.append(f"-{rwx} 1 {node.owner} {grp} 4096 {target}")
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
                    group = "root"
                else:
                    child = node.children[name]
                    child_type = "d" if child.is_dir() else "-"
                    perms = mode_to_rwx(child.permissions, child.is_dir())
                    owner = child.owner
                    group = getattr(child, "group", owner)
                rendered.append(f"{child_type}{perms} 1 {owner} {group} 4096 {name}")
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

    messages = []
    for target in target_paths:
        target_node, _ = ctx.vfs.get_node(ctx.state.current_path, target)
        if not target_node:
            return ctx.result_factory(stderr=f"chmod: cannot access '{target}': No such file or directory\n", exit_code=1)

        # POSIX Ownership Check:
        if ctx.state.current_user != "root" and target_node.owner != ctx.state.current_user:
            return ctx.result_factory(
                stderr=f"chmod: changing permissions of '{target}': Operation not permitted\n",
                exit_code=1
            )

        # Numeric mode support (e.g. 755, 644, 700, 777, 600, 0000, 0444, 0755)
        if mode_str.isdigit() and len(mode_str) in [3, 4]:
            target_node.permissions = mode_str
        # Symbolic mode support (+x, -x, u+x, etc.)
        elif "+x" in mode_str:
            try:
                cur_mode = int(target_node.permissions, 8) if (target_node.permissions and target_node.permissions.isdigit()) else 0
            except ValueError:
                cur_mode = 0
            if cur_mode == 0:
                target_node.permissions = "755"
            else:
                target_node.permissions = oct(cur_mode | 0o111)[2:]
        elif "-x" in mode_str:
            try:
                cur_mode = int(target_node.permissions, 8) if (target_node.permissions and target_node.permissions.isdigit()) else 0
            except ValueError:
                cur_mode = 0
            target_node.permissions = oct(cur_mode & ~0o111)[2:]
        else:
            return ctx.result_factory(stderr=f"chmod: invalid mode: '{mode_str}'\n", exit_code=1)

        # Diegetic event triggers for recovery partition binaries
        if "repair_buffer" in target and ("+x" in mode_str or mode_str in ["755", "777", "700", "0755"]):
            ctx.state.system_flags["BUFFER_REPAIRED"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "BUFFER_REPAIRED", "value": True}))
        elif ".bashrc" in target:
            ctx.state.system_flags["BASHRC_RESTORED"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "BASHRC_RESTORED", "value": True}))

        messages.append(f"[chmod]: mode of '{target}' changed to {target_node.permissions}\n")

    return ctx.result_factory(stdout="".join(messages))


def cmd_ps(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ps", "args": args}))
    ctx.state.system_flags["PROCESS_CHECKED"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "PROCESS_CHECKED", "value": True}))
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
        arg = args[idx]
        if arg in ["-s", "-n"] and idx + 1 < len(args):
            sig = args[idx + 1]
            idx += 2
        elif arg.startswith("-s") and len(arg) > 2:
            sig = arg[2:]
            idx += 1
        elif arg.startswith("-n") and len(arg) > 2:
            sig = arg[2:]
            idx += 1
        elif arg.startswith("-") and not arg.lstrip("-").isdigit() and len(arg) > 1:
            sig = arg.lstrip("-")
            idx += 1
        elif arg.startswith("-") and arg[1:].isdigit():
            sig = arg[1:]
            idx += 1
        else:
            pid_str = arg
            idx += 1

    if not pid_str or not pid_str.isdigit():
        return ctx.result_factory(
            stderr="kill: invalid pid or signal specification (use numeric PID from 'ps aux', e.g. 'kill -9 104')\n",
            exit_code=1
        )

    target_pid = int(pid_str)
    sig_normalized = sig.upper()
    is_sigkill = sig_normalized in ["9", "KILL", "SIGKILL"]

    # Locate Process
    proc = next((p for p in ctx.state.process_table if p.pid == target_pid and p.status == "running"), None)
    if not proc:
        return ctx.result_factory(stderr=f"kill: ({target_pid}) - No such process\n", exit_code=1)

    # PID 102 (task_audit)
    if target_pid == 102 or proc.name == "task_audit":
        proc.status = "terminated"
        ctx.state.process_table = [p for p in ctx.state.process_table if p.pid != target_pid]
        audit_content = (
            "================================================================================\n"
            "                 TASK AUDIT SUBSYSTEM INCIDENT REPORT\n"
            "================================================================================\n"
            "Timestamp: 03:42:15 UTC\n"
            "Status: Process PID 102 halted.\n\n"
            "CRITICAL FINDING: Rogue daemon PID 104 (/tmp/sys_miner) has hooked Signal 15 (SIGTERM)\n"
            "using custom sigaction exception vectors. Standard kill (SIGTERM) will be trapped\n"
            "and rejected by the process line discipline.\n\n"
            "DIRECTIVE: Forceful kernel termination required. Use non-maskable SIGKILL:\n"
            "    kill -9 104\n"
            "================================================================================\n"
        )
        ctx.vfs.write_file([], "/tmp/audit_report.txt", audit_content, append=False, owner="root", permissions="644")
        return ctx.result_factory(stdout=f"Process {target_pid} (task_audit) terminated. Audit log written to /tmp/audit_report.txt\n")

    # PID 104 (sys_miner)
    if target_pid == 104 or proc.name == "sys_miner":
        if is_sigkill:
            if any(p.pid == 102 for p in ctx.state.process_table):
                return ctx.result_factory(
                    stderr="[KERNEL]: Process 104 terminated, but supervisor (PID 102) immediately respawned worker.\n"
                           "[ACTION]: Terminate parent supervisor task (PID 102) first.\n",
                    exit_code=1
                )
            proc.status = "terminated"
            ctx.state.process_table = [p for p in ctx.state.process_table if p.pid != target_pid]
            ctx.state.system_flags["MALWARE_TERMINATED"] = True
            ctx.state.system_flags["CPU_NORMAL"] = True
            ctx.bus.publish(Event("flag_changed", {"flag": "MALWARE_TERMINATED", "value": True}))
            ctx.bus.publish(Event("flag_changed", {"flag": "CPU_NORMAL", "value": True}))
            return ctx.result_factory(stdout="[KERNEL]: Process 104 (sys_miner) forcefully killed by SIGKILL.\n")
        else:
            return ctx.result_factory(
                stderr="[SIGNAL WARN]: PID 104 caught signal 15 (SIGTERM). Process locked; request discarded.\n",
                exit_code=1
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
                if target_iface == "osiris0":
                    ctx.state.system_flags["NET_LINK_UP"] = True
                    ctx.bus.publish(Event("flag_changed", {"flag": "NET_LINK_UP", "value": True}))
                return ctx.result_factory()
            elif action == "down":
                ctx.state.network_interfaces[target_iface]["state"] = "DOWN"
                if target_iface == "osiris0":
                    ctx.state.system_flags["NET_LINK_UP"] = False
                    ctx.state.system_flags["NETWORK_ONLINE"] = False
                    ctx.bus.publish(Event("flag_changed", {"flag": "NET_LINK_UP", "value": False}))
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
            "default via 10.0.42.1 dev osiris0 proto dhcp src 10.0.42.15 metric 100",
            "10.0.42.0/24 dev osiris0 proto kernel scope link src 10.0.42.15 metric 100"
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
    count = None
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

    iface_state = ctx.state.network_interfaces.get("osiris0", {}).get("state", "DOWN")
    if iface_state == "DOWN":
        return ctx.result_factory(stderr="ping: connect: Network is unreachable\n", exit_code=2)

    has_ctrl_c = ctx.state.unlocked_ergonomics.get("ctrl_c", False)
    if count is None:
        pkt_count = 5
        extra_msg = "" if has_ctrl_c else "[TIMEOUT ADVISORY]: Foreground probe auto-terminated after 5 cycles (SIGINT unmapped).\n"
    else:
        pkt_count = count
        extra_msg = ""

    lines = [f"PING {target} ({target}) 56(84) bytes of data."]
    for i in range(1, pkt_count + 1):
        lines.append(f"64 bytes from {target}: icmp_seq={i} ttl=64 time=0.042 ms")
    lines.append("")
    lines.append(f"--- {target} ping statistics ---")
    lines.append(f"{pkt_count} packets transmitted, {pkt_count} received, 0% packet loss, time {pkt_count * 1000}ms")
    lines.append("rtt min/avg/max/mdev = 0.038/0.042/0.049/0.004 ms")
    if extra_msg:
        lines.append(extra_msg.strip())

    ctx.state.system_flags["NETWORK_ONLINE"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "NETWORK_ONLINE", "value": True}))

    return ctx.result_factory(stdout="\n".join(lines) + "\n")


def cmd_ll(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "ll", "args": args}))
    if not (ctx.state.system_flags.get("BASHRC_RESTORED", False) or ctx.state.unlocked_ergonomics.get("autocomplete", False)):
        return ctx.result_factory(stderr="bash: ll: command not found\n", exit_code=127)
    return cmd_ls(ctx, ["-la"] + args)


def cmd_append(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "append", "args": args}))
    return ctx.result_factory(
        stderr=(
            "bash: append: command not found\n"
            "(Tip: in Linux/Unix shells, use stream redirection '>>' to append data without overwriting)\n"
            "Example: cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf\n"
        ),
        exit_code=127
    )

