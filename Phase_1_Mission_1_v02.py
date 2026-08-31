import sys
import fnmatch

# ---------------------------------------------------------
# 1. SIMULATED ENVIRONMENT & NARRATIVE FILESYSTEM
# ---------------------------------------------------------

filesystem = {
    "/": {
        "home": {
            "alice": {
                ".mission": {
                    "briefing.txt": (
                        "=== CLASSIFIED EMERGENCY BRIEFING ===\n"
                        "Incident: Global telemetry severed at 03:42 UTC.\n"
                        "Lead: Incident logs show unusual service failures.\n"
                        "Next Step: Check system logs under /var/log/ for failed services.\n"
                        "====================================="
                    )
                },
                "notes": {
                    "sysadmin_notes.txt": (
                        "SYSADMIN SURVIVAL GUIDE:\n\n"
                        "[DIRECTORY NAVIGATION]\n"
                        "Linux paths start at root '/'. You can jump across top-level branches\n"
                        "directly (e.g., 'cd /opt' or 'cd /var') rather than stepping backward one by one.\n\n"
                        "[TEXT SEARCHING]\n"
                        "When files are too long to read line-by-line, use pattern matching:\n"
                        "    grep <pattern> <file_path>\n"
                        "Search logs for known service names or keywords to isolate errors.\n\n"
                        "[FILE SEARCHING]\n"
                        "When files are scattered across unknown directories, search trees from root or sub-roots:\n"
                        "    find <start_path> -name \"<pattern>\"\n"
                        "Example: search /opt or root / for config files using wildcard patterns like \"*.conf\".\n"
                    ),
                    "mapping_tool.txt": (
                        "UTILITY DISCOVERY NOTE:\n"
                        "To view a graphical branch map of directories you've explored, use:\n\n"
                        "    tree\n\n"
                        "This helps visualize the directory hierarchy as you discover new paths.\n"
                    )
                },
                "readme.txt": (
                    "APOLLO WORKSTATION LOGON\n\n"
                    "Some critical files are hidden by default.\n"
                    "Type 'ls -a' instead of 'ls' to reveal all entries (including dotted names).\n\n"
                    "Type 'objectives' to check current operational goals.\n"
                    "Type 'help' to review your known command list.\n"
                )
            }
        },
        "etc": {
            "motd": "EMERGENCY PROTOCOL ACTIVE. Check your operator manual using 'help' and type 'objectives' to begin."
        },
        "opt": {
            "phoenix": {
                "README.txt": "PHOENIX Recovery Subsystem v4.2. Run recovery scripts to restore routing.",
                "config": {
                    "phoenix.conf": (
                        "PORT=8080\n"
                        "STATUS=DEGRADED\n"
                        "AUTH_KEY=PX-9042-ALPHA\n"
                        "LOG_TARGET=/var/log/system.log\n"
                    )
                },
                "recovery": {
                    "recovery.sh": "#!/bin/bash\necho 'Restoring core nodes...'"
                }
            }
        },
        "var": {
            "log": {
                "system.log": (
                    "03:40:12 apollo kernel: Network interface eth0 link down\n"
                    "03:41:05 apollo auth: Successful login for alice from 127.0.0.1\n"
                    "03:42:19 apollo systemd: phoenix-sync service terminated unexpectedly.\n"
                    "03:42:20 apollo alert: telemetry failure detected across core nodes\n"
                    "03:42:22 apollo alert: Global telemetry link severed\n"
                    "03:43:01 apollo systemd: service watchdog timeout on phoenix-core"
                ),
                "auth.log": "User alice session opened."
            }
        }
    }
}

current_path = ["home", "alice"]
visited_paths = {"/home/alice", "/home", "/"}

# ---------------------------------------------------------
# 2. SEQUENTIAL SKILL-BUILDING MISSIONS
# ---------------------------------------------------------

current_mission = 1

MISSIONS = {
    1: {
        "title": "MISSION 1: Terminal Orientation",
        "description": "Initialize your system documentation, inspect your workspace, and read your starting instructions.",
        "tasks": {
            "open_help": {"desc": "Consult your active operator manual", "done": False},
            "list_contents": {"desc": "Inspect the files and folders in your current directory", "done": False},
            "read_file": {"desc": "Read the workstation instructions file", "done": False}
        }
    },
    2: {
        "title": "MISSION 2: Location & Navigation",
        "description": "Determine your current working path, move into a local folder, and inspect its contents.",
        "tasks": {
            "run_pwd": {"desc": "Determine your exact location in the filesystem using 'pwd'", "done": False},
            "cd_folder": {"desc": "Navigate into the 'notes' directory using 'cd'", "done": False},
            "read_new_file": {"desc": "Read 'sysadmin_notes.txt' to learn core navigation and diagnostic syntax", "done": False}
        }
    },
    3: {
        "title": "MISSION 3: Subsystem Navigation",
        "description": "Navigate to the root log directory mentioned in the briefing and inspect its files.",
        "tasks": {
            "nav_logs": {"desc": "Navigate to the system log directory (/var/log)", "done": False},
            "list_logs": {"desc": "List the contents of the log directory", "done": False}
        }
    },
    4: {
        "title": "MISSION 4: Log Analysis",
        "description": "Search the system logs using pattern matching to isolate the failed emergency service.",
        "tasks": {
            "grep_logs": {"desc": "Search system.log for service failure entries matching 'phoenix'", "done": False}
        }
    },
    5: {
        "title": "MISSION 5: Root Subsystem Scan",
        "description": "Scan from root / or /opt to find recovery configuration files matching '*.conf'.",
        "tasks": {
            "find_configs": {"desc": "Locate configuration files using a wildcard search pattern", "done": False}
        }
    }
}

COMMAND_DOCS = {
    "ls": "ls                       List visible files in the directory",
    "cat": "cat <file>               Display the contents of a text file",
    "pwd": "pwd                      Print current working directory path",
    "cd": "cd <path>                Navigate between directories (use 'cd ..' to go back)",
    "tree": "tree                     Visual tree map of explored directories",
    "grep": "grep <pattern> <file>    Search lines in a file matching a pattern",
    "find": "find <path> -name <ptn>  Search for files by pattern across directory trees",
    "help": "help                     Display this discovered commands manual",
    "objectives": "objectives               Display active mission goals and status"
}

discovered_commands = {"help", "ls", "cat", "objectives"}

COMMAND_CARDS = {
    "pwd": (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ NEW COMMAND DISCOVERED: pwd                              │\n"
        "│ 'Print Working Directory' — Shows your current location  │\n"
        "│ in the filesystem hierarchy.                             │\n"
        "└──────────────────────────────────────────────────────────┘"
    ),
    "ls_all": (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ NEW OPTION DISCOVERED: ls -a                             │\n"
        "│ Displays all entries, including hidden files and folders │\n"
        "│ that begin with a dot (.).                               │\n"
        "└──────────────────────────────────────────────────────────┘"
    ),
    "cd": (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ NEW COMMAND DISCOVERED: cd                               │\n"
        "│ 'Change Directory' — Move into folders.                  │\n"
        "│ Syntax: cd <folder> | cd .. (moves up one level)         │\n"
        "└──────────────────────────────────────────────────────────┘"
    ),
    "tree": (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ NEW COMMAND DISCOVERED: tree                             │\n"
        "│ Displays a graphical tree of your discovered filesystem. │\n"
        "│ It maps out directories as you explore them.             │\n"
        "└──────────────────────────────────────────────────────────┘"
    ),
    "grep": (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ NEW COMMAND DISCOVERED: grep                             │\n"
        "│ 'Global Regular Expression Print' — Searches text inside │\n"
        "│ files for matching words or patterns.                    │\n"
        "│ Syntax: grep <pattern> <filename>                        │\n"
        "└──────────────────────────────────────────────────────────┘"
    ),
    "find": (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ NEW COMMAND DISCOVERED: find                             │\n"
        "│ Searches directory trees for files matching criteria.    │\n"
        "│ Syntax: find <path> -name \"<pattern>\"                    │\n"
        "│ Example: find / -name \"*.log\"                           │\n"
        "└──────────────────────────────────────────────────────────┘"
    )
}

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------

def check_mission_progress():
    global current_mission
    if current_mission not in MISSIONS:
        return

    mission = MISSIONS[current_mission]
    all_done = all(task["done"] for task in mission["tasks"].values())
    
    if all_done:
        print("\n" + "=" * 60)
        print(f" ★ LEVEL COMPLETE: {mission['title']} ★")
        print("=" * 60)
        current_mission += 1
        if current_mission in MISSIONS:
            print(f"\n[NEXT OBJECTIVE UNLOCKED] -> {MISSIONS[current_mission]['title']}")
            print(f"Goal: {MISSIONS[current_mission]['description']}")
            print("Type 'objectives' to review current goals.\n")
        else:
            print("\n★★★ ALL CAMPAIGN MISSIONS COMPLETE — GLOBAL NETWORK RESTORED! ★★★\n")

def get_node(path):
    node = filesystem["/"]
    for segment in path:
        if isinstance(node, dict) and segment in node:
            node = node[segment]
        else:
            return None
    return node

def resolve_path(target):
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

def trigger_card(card_key, base_cmd=None):
    if card_key in COMMAND_CARDS and card_key not in discovered_commands:
        print("\n" + COMMAND_CARDS[card_key] + "\n")
        discovered_commands.add(card_key)
    
    reg_cmd = base_cmd or card_key
    discovered_commands.add(reg_cmd)

def traverse_filesystem(node, current_dir=""):
    for key, val in node.items():
        full_path = f"{current_dir}/{key}"
        if isinstance(val, dict):
            yield (full_path, True)
            yield from traverse_filesystem(val, full_path)
        else:
            yield (full_path, False)

def print_explored_tree(node, current_dir="", prefix=""):
    items = sorted(node.keys())
    visible_items = []
    for item in items:
        item_path = f"{current_dir}/{item}" if current_dir != "/" else f"/{item}"
        if isinstance(node[item], dict):
            has_visited_descendant = any(vp == item_path or vp.startswith(item_path + "/") for vp in visited_paths)
            if has_visited_descendant:
                visible_items.append(item)
        else:
            if current_dir in visited_paths:
                visible_items.append(item)

    for i, item in enumerate(visible_items):
        is_last = (i == len(visible_items) - 1)
        connector = "└── " if is_last else "├── "
        val = node[item]
        item_path = f"{current_dir}/{item}" if current_dir != "/" else f"/{item}"
        
        if isinstance(val, dict):
            print(f"{prefix}{connector}{item}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_explored_tree(val, item_path, new_prefix)
        else:
            print(f"{prefix}{connector}{item}")

# ---------------------------------------------------------
# 4. COMMAND HANDLERS
# ---------------------------------------------------------

def cmd_tree(args):
    trigger_card("tree")
    print("/")
    print_explored_tree(filesystem["/"], current_dir="/")

def cmd_objectives(args):
    if current_mission not in MISSIONS:
        print("All system objectives restored.")
        return

    m = MISSIONS[current_mission]
    print("\n" + "=" * 60)
    print(f" {m['title']}")
    print(f" {m['description']}")
    print("-" * 60)
    print(" STATUS:")
    for task_id, task in m["tasks"].items():
        status = "[X]" if task["done"] else "[ ]"
        print(f"   {status} {task['desc']}")
    print("=" * 60 + "\n")

def cmd_help(args):
    print("DISCOVERED COMMANDS:")
    for cmd in sorted(discovered_commands):
        if cmd in COMMAND_DOCS:
            print(f"  {COMMAND_DOCS[cmd]}")
    print("  exit                     Terminate the terminal session")
    
    if current_mission == 1:
        MISSIONS[1]["tasks"]["open_help"]["done"] = True
        check_mission_progress()

def cmd_pwd(args):
    trigger_card("pwd")
    print("/" + "/".join(current_path))
    
    if current_mission == 2:
        MISSIONS[2]["tasks"]["run_pwd"]["done"] = True
        check_mission_progress()

def cmd_ls(args):
    node = get_node(current_path)
    
    for arg in args:
        if arg.startswith("-") and arg not in ["-a", "-la", "-al"]:
            print(f"ls: unrecognized option '{arg}'")
            print("[LEARNING TIP] Check readme.txt for notes on viewing hidden files.")
            return

    show_all = "-a" in args or "-la" in args or "-al" in args
    
    if show_all:
        trigger_card("ls_all", base_cmd="ls")
        COMMAND_DOCS["ls"] = "ls [-a]                  List files in directory (-a shows hidden files)"
    else:
        trigger_card("ls")

    entries = sorted(node.keys())
    output = []
    for name in entries:
        if not show_all and name.startswith("."):
            continue
        output.append(name + ("/" if isinstance(node[name], dict) else ""))
    
    if output:
        print("  ".join(output))

    if current_mission == 1:
        MISSIONS[1]["tasks"]["list_contents"]["done"] = True
        check_mission_progress()
    elif current_mission == 3 and current_path == ["var", "log"]:
        MISSIONS[3]["tasks"]["list_logs"]["done"] = True
        check_mission_progress()

def cmd_cd(args):
    global current_path
    trigger_card("cd")
    
    if not args:
        current_path = ["home", "alice"]
        return
    
    if len(args) > 1:
        print("cd: too many arguments")
        print("[LEARNING TIP] 'cd' takes a single directory path: cd <path>")
        return

    target = args[0]
    new_path = resolve_path(target)
    node = get_node(new_path)
    
    if node is None:
        print(f"cd: {target}: No such file or directory")
        print("[LEARNING TIP] Use 'ls' to check names. Folders end with a slash '/' while files usually have a dot extension like '.txt'.")
    elif not isinstance(node, dict):
        print(f"cd: {target}: Not a directory")
        print(f"[LEARNING TIP] '{target}' is a file (has an extension like .txt), not a directory folder (which ends with '/').")
        print(f"               Use 'cat {target}' to read files, and use 'cd' only for folders.")
    else:
        current_path = new_path
        
        accum = ""
        for seg in current_path:
            accum += "/" + seg
            visited_paths.add(accum)
        if not current_path:
            visited_paths.add("/")

        if current_mission == 2 and current_path == ["home", "alice", "notes"]:
            MISSIONS[2]["tasks"]["cd_folder"]["done"] = True
            check_mission_progress()
        elif current_mission == 3 and current_path == ["var", "log"]:
            MISSIONS[3]["tasks"]["nav_logs"]["done"] = True
            check_mission_progress()

def cmd_cat(args):
    if not args:
        print("cat: missing file operand")
        print("[LEARNING TIP] 'cat' requires a file name with its extension. Example: cat readme.txt")
        return
    
    target = args[0]
    path_tokens = resolve_path(target)
    file_name = path_tokens[-1] if path_tokens else ""
    parent_dir = get_node(path_tokens[:-1])
    
    if parent_dir and file_name in parent_dir:
        item = parent_dir[file_name]
        if isinstance(item, str):
            print(item)
            
            if file_name == "mapping_tool.txt":
                trigger_card("tree")

            if current_mission == 1 and file_name == "readme.txt":
                MISSIONS[1]["tasks"]["read_file"]["done"] = True
                check_mission_progress()
            elif current_mission == 2 and file_name == "sysadmin_notes.txt":
                MISSIONS[2]["tasks"]["read_new_file"]["done"] = True
                check_mission_progress()
        else:
            print(f"cat: {target}: Is a directory")
            print(f"[LEARNING TIP] '{target}' is a directory folder (ends with '/'), not a file.")
            print(f"               Use 'cd {target}' to move into folders, and use 'cat' for files with extensions (like .txt).")
    else:
        print(f"cat: {target}: No such file or directory")
        print("[LEARNING TIP] Verify the exact name with 'ls'. Files typically end with an extension like '.txt' or '.conf'.")

def cmd_grep(args):
    trigger_card("grep")
    if not args:
        print("Usage: grep [PATTERN] [FILE]")
        return
    
    if len(args) == 1:
        print("grep: missing target file")
        return

    pattern = args[0].strip("\"'")
    target = args[1]
    
    path_tokens = resolve_path(target)
    file_name = path_tokens[-1] if path_tokens else ""
    parent_dir = get_node(path_tokens[:-1])

    if parent_dir and file_name in parent_dir:
        item = parent_dir[file_name]
        if isinstance(item, str):
            lines = item.split("\n")
            matches = [line for line in lines if pattern.lower() in line.lower()]
            for match in matches:
                print(match)
            
            if current_mission == 4 and "phoenix" in pattern.lower() and "system.log" in file_name and matches:
                MISSIONS[4]["tasks"]["grep_logs"]["done"] = True
                check_mission_progress()
        else:
            print(f"grep: {target}: Is a directory")
    else:
        print(f"grep: {target}: No such file or directory")

def cmd_find(args):
    trigger_card("find")
    if not args:
        print("Usage: find [PATH] -name [PATTERN]")
        return

    start_path_str = args[0]
    name_pattern = None

    if len(args) > 1:
        if args[1] == "-name" and len(args) > 2:
            name_pattern = args[2].strip("\"'")
        else:
            print("find: invalid argument syntax")
            return

    target_tokens = resolve_path(start_path_str)
    start_node = get_node(target_tokens)

    if start_node is None:
        print(f"find: '{start_path_str}': No such file or directory")
        return

    base_prefix = "" if start_path_str == "/" else ("/" + "/".join(target_tokens))
    
    if isinstance(start_node, dict):
        for path_str, _ in traverse_filesystem(start_node, base_prefix):
            filename = path_str.split("/")[-1]
            if name_pattern:
                if fnmatch.fnmatch(filename, name_pattern):
                    print(path_str)
                    if current_mission == 5 and (start_path_str in ["/", "/opt", "opt"]) and "*.conf" in name_pattern:
                        MISSIONS[5]["tasks"]["find_configs"]["done"] = True
                        check_mission_progress()
            else:
                print(path_str)
    else:
        print(base_prefix)

# ---------------------------------------------------------
# 5. MAIN LOOP
# ---------------------------------------------------------

def main():
    commands = {
        "pwd": cmd_pwd,
        "ls": cmd_ls,
        "cd": cmd_cd,
        "cat": cmd_cat,
        "tree": cmd_tree,
        "grep": cmd_grep,
        "find": cmd_find,
        "objectives": cmd_objectives,
        "goals": cmd_objectives,
        "help": cmd_help,
        "exit": lambda args: sys.exit(0)
    }

    print("=" * 60)
    print("           APOLLO INCIDENT RESPONSE TERMINAL v1.0")
    print("=" * 60)
    print("HOST: apollo | USER: alice | SECURITY STATE: DEGRADED")
    print("MESSAGE OF THE DAY:")
    print("  " + filesystem["/"]["etc"]["motd"])
    print("=" * 60)
    print("Type 'help' to consult your manual or 'objectives' to check tasks.\n")

    while True:
        prompt_path = "~" if current_path == ["home", "alice"] else "/" + "/".join(current_path)
        try:
            raw_input = input(f"alice@apollo:{prompt_path}$ ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession terminated.")
            break

        if not raw_input:
            continue

        parts = raw_input.split()
        cmd, args = parts[0], parts[1:]

        if cmd in ["list", "dir"]:
            print(f"{cmd}: command not found")
            print("[LEARNING TIP] Linux uses 'ls' to list files instead of 'dir' or 'list'.")
        elif cmd in ["type", "read", "open"]:
            print(f"{cmd}: command not found")
            print("[LEARNING TIP] Linux uses 'cat' to display text files instead of 'type' or 'open'.")
        elif cmd in ["search", "locate"]:
            print(f"{cmd}: command not found")
            print("[LEARNING TIP] Use 'grep' to search inside text files, or 'find' to search for file names.")
        elif cmd in commands:
            commands[cmd](args)
        else:
            print(f"{cmd}: command not found")
            print("[LEARNING TIP] Type 'help' to review your discovered commands.")

if __name__ == "__main__":
    main()