import sys

# 1. Virtual Filesystem (Nested Dictionaries)
filesystem = {
    "/": {
        "home": {
            "alice": {
                ".mission": {
                    "briefing.txt": "OBJECTIVE: Locate the compromised service logs in /var/log."
                },
                "notes": {
                    "todo.txt": "Check system logs. Update firewall."
                },
                "readme.txt": "Welcome to APOLLO Incident Terminal."
            }
        },
        "var": {
            "log": {
                "system.log": "PHOENIX service alert: Node offline."
            }
        }
    }
}

# 2. Player State
current_path = ["home", "alice"]

def get_node(path):
    """Traverse the filesystem dict to return the folder/file at path."""
    node = filesystem["/"]
    for segment in path:
        if segment in node and isinstance(node[segment], dict):
            node = node[segment]
        else:
            return None
    return node

def resolve_path(target):
    """Handle absolute, relative, and parent directory paths."""
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

# 3. Command Handlers
def cmd_pwd(args):
    print("/" + "/".join(current_path))

def cmd_ls(args):
    node = get_node(current_path)
    show_all = "-a" in args
    for name in sorted(node.keys()):
        if not show_all and name.startswith("."):
            continue
        print(name)

def cmd_cd(args):
    global current_path
    if not args:
        current_path = ["home", "alice"]
        return
    new_path = resolve_path(args[0])
    if get_node(new_path) is not None:
        current_path = new_path
    else:
        print(f"cd: no such file or directory: {args[0]}")

def cmd_cat(args):
    if not args:
        print("cat: missing file operand")
        return
    target = args[0]
    path_tokens = resolve_path(target)
    file_name = path_tokens[-1]
    parent_dir = get_node(path_tokens[:-1])
    
    if parent_dir and file_name in parent_dir and isinstance(parent_dir[file_name], str):
        print(parent_dir[file_name])
    else:
        print(f"cat: {target}: No such file or directory")

# 4. Main Game Loop
def main():
    commands = {
        "pwd": cmd_pwd,
        "ls": cmd_ls,
        "cd": cmd_cd,
        "cat": cmd_cat,
        "exit": lambda args: sys.exit(0)
    }

    print("APOLLO TERMINAL v1.0 — Type 'pwd', 'ls', 'cd', 'cat', or 'exit'\n")

    while True:
        prompt_path = "~" if current_path == ["home", "alice"] else "/" + "/".join(current_path)
        raw_input = input(f"alice@apollo:{prompt_path}$ ").strip()
        if not raw_input:
            continue

        parts = raw_input.split()
        cmd, args = parts[0], parts[1:]

        if cmd in commands:
            commands[cmd](args)
        else:
            print(f"{cmd}: command not found")

if __name__ == "__main__":
    main()