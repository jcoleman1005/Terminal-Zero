import os
from typing import List
from terminal_zero.core.events import Event
from terminal_zero.core.state import CommandContext, CommandResult
from terminal_zero.core.persistence import save_game_state
from terminal_zero.content.narrative import get_primary_goal
from terminal_zero.content.man_pages import MAN_PAGES
from terminal_zero.content.initial_vfs import build_default_vfs


def cmd_decrypt(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "decrypt", "args": args}))
    last_err = ctx.state.last_stderr.strip()
    if not last_err:
        return ctx.result_factory(
            stdout="[APOLLO-DIAGNOSTIC]: No recent hardware or kernel fault recorded in buffer.\n"
        )

    if "command not found" in last_err:
        return ctx.result_factory(
            stdout="[DECRYPT ADVISORY]: The command entered does not exist.\n"
                   "• Check spelling or type 'ls' to see available local files.\n"
                   "• Type 'help' for guidance or inspect 'README.txt'.\n"
                   "• Standard utilities: pwd, ls, cd, cat, man, sync.\n"
        )

    diag = "[APOLLO-DIAGNOSTIC]: System anomaly detected."
    
    if "<" in last_err or ">" in last_err or any(k in last_err for k in ["proile_src", "profile_src", "target_path"]):
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x1F - PLACEHOLDER SYNTAX]\n"
            "Notice: The '<' and '>' in Morgan's notes represent placeholder names, not literal characters.\n"
            "Action: Replace '<profile_src>' with 'alice.bashrc' and '<target_path>' with '/home/alice/.bashrc'.\n"
            "Exact command: cat alice.bashrc > /home/alice/.bashrc"
        )
    elif "cannot execute text file" in last_err or ("Permission denied" in last_err and any(ext in last_err for ext in [".txt", ".log", ".conf", ".key"])):
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x1E - NON-EXECUTABLE STREAM]\n"
            "Target is a plain-text document, not an executable program.\n"
            "Action: Use 'cat <file>' or 'head <file>' to view file contents."
        )
    elif "Authentication token missing" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x5B - AUTHENTICATION REQUIRED]\n"
            "Daemon initialization aborted: Missing cryptographic authentication key in configuration.\n"
            "Action: Retrieve key from /mnt/recovery/keys/phoenix.key and append to /etc/phoenix/phoenix.conf via '>>'."
        )
    elif "Insecure permissions" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x2E - ACCESS RESTRICTED]\n"
            "Configuration file permissions rejected by daemon security audit (mode must be 0644).\n"
            "Action: Run 'chmod 644 /etc/phoenix/phoenix.conf' to secure configuration permissions."
        )
    elif "Missing configuration file" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x0A - NODE NOT FOUND]\n"
            "Required service configuration file missing from /etc/phoenix/.\n"
            "Action: Restore fallback template from /etc/phoenix/phoenix.conf.default or /opt/backup/phoenix.conf."
        )
    elif "Operation not permitted" in last_err and "phoenix" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x2D - ACCESS RESTRICTED]\n"
            "/opt/phoenix is locked by root system services.\n"
            "Action: Investigate incident logs in /var/log/ to trace the breach before accessing system services."
        )
    elif "No such file or directory" in last_err:
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
    elif "Network is unreachable" in last_err or "network unreachable" in last_err.lower() or "network gateway unreachable" in last_err.lower():
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x3D - NETWORK OFFLINE]\n"
            "Virtual network interface link state is DOWN.\n"
            "Action: Run 'ip link set apollo0 up' to activate the network adapter and verify routing."
        )
    elif "No such process" in last_err or "invalid signal specification" in last_err or "invalid pid" in last_err:
        diag = (
            "[APOLLO-DIAGNOSTIC: FAULT 0x5E - PROCESS ANOMALY]\n"
            "Process ID not active or signal invalid.\n"
            "Action: Run 'ps aux' to audit active process table before issuing 'kill -9 <PID>'."
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


def cmd_repair_buffer(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "repair_buffer", "args": args}))
    ctx.state.system_flags["BUFFER_REPAIRED"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "BUFFER_REPAIRED", "value": True}))
    return ctx.result_factory(
        stdout="[!] ABILITY UNLOCKED: Command Memory Recall\nYou can now press [UP] and [DOWN] arrow keys to cycle through previous commands.\n"
    )


def cmd_phoenix_daemon(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "phoenix_daemon", "args": args}))

    # 1. Validate Network State
    if not ctx.state.system_flags.get("NETWORK_ONLINE", False):
        return ctx.result_factory(
            stderr="[PHOENIX ERROR]: Network gateway unreachable. Interface 'apollo0' is DOWN.\n", 
            exit_code=1
        )

    # 2. Resolve Config Node
    conf_node, _ = ctx.vfs.get_node([], "/etc/phoenix/phoenix.conf")
    if not conf_node or not conf_node.is_file():
        return ctx.result_factory(
            stderr="[PHOENIX ERROR]: Missing configuration file /etc/phoenix/phoenix.conf\n", 
            exit_code=1
        )

    # 3. Check File Permissions (Must be 0644 / 644)
    if conf_node.permissions not in ["644", "0644"]:
        return ctx.result_factory(
            stderr=f"[PHOENIX ERROR]: Insecure permissions on /etc/phoenix/phoenix.conf (mode: {conf_node.permissions}). Required: 0644\n", 
            exit_code=1
        )

    # 4. Check Cryptographic Token Presence
    if "PX-KEY-7701-ALPHA" not in (conf_node.content or ""):
        return ctx.result_factory(
            stderr="[PHOENIX ERROR]: Authentication token missing or invalid in /etc/phoenix/phoenix.conf\n", 
            exit_code=1
        )

    # Success State Transition
    ctx.state.system_flags["PHOENIX_ONLINE"] = True

    # Dynamically bind port 8080 upon launch (if not already present)
    if not any(s.get("local") == "127.0.0.1:8080" for s in ctx.state.listening_sockets):
        ctx.state.listening_sockets.append({
            "proto": "tcp", "local": "127.0.0.1:8080", "peer": "0.0.0.0:*", 
            "state": "LISTEN", "pid": 500, "proc": "phoenix_daemon"
        })

    ctx.bus.publish(Event("flag_changed", {"flag": "PHOENIX_ONLINE", "value": True}))
    return ctx.result_factory(
        stdout="[PHOENIX-DAEMON]: Emergency Restoration Protocol activated. Listening on 127.0.0.1:8080. Gateway ONLINE.\n"
    )


def cmd_phoenix_ctl(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "phoenix_ctl", "args": args}))
    return cmd_phoenix_daemon(ctx, args)


def cmd_apollo_net(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "apollo-net", "args": args}))
    iface_state = ctx.state.network_interfaces.get("apollo0", {}).get("state", "DOWN")
    return ctx.result_factory(
        stdout=f"[APOLLO-NET v1.0]: Subnet link state is {iface_state}. Gateway 10.0.42.1\n"
    )


def cmd_sync(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "sync"}))
    try:
        save_game_state(ctx.state, "savegame.json")
        return ctx.result_factory(stdout="[SYSTEM]: In-memory buffers flushed to persistent storage.\n")
    except Exception as e:
        return ctx.result_factory(stderr=f"sync: error writing blocks: {str(e)}\n", exit_code=1)


def cmd_reboot(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "reboot", "args": args}))

    if os.path.exists("savegame.json"):
        try:
            os.remove("savegame.json")
        except Exception:
            pass

    fresh_root = build_default_vfs()
    ctx.vfs.root = fresh_root

    from terminal_zero.core.state import TerminalState
    fresh_state = TerminalState(ctx.vfs, ctx.bus, ["home", "alice"])
    ctx.state.current_path = list(fresh_state.current_path)
    ctx.state.env = dict(fresh_state.env)
    ctx.state.unlocked_ergonomics = dict(fresh_state.unlocked_ergonomics)
    ctx.state.system_flags = dict(fresh_state.system_flags)
    ctx.state.process_table = list(fresh_state.process_table)
    ctx.state.network_interfaces = dict(fresh_state.network_interfaces)
    ctx.state.listening_sockets = list(fresh_state.listening_sockets)
    ctx.state.last_stderr = ""

    reboot_banner = (
        "\nBroadcast message from root@apollo (tty1) (system reboot):\n\n"
        "The system is going down for reboot NOW!\n"
        "Restarting system...\n\n"
        "=== APOLLO WORKSTATION TERMINAL [RECOVERY MODE] ===\n"
        "System degraded. Type 'help' for guidance or inspect 'README.txt'.\n"
        "Type 'exit' to disconnect.\n"
    )
    return ctx.result_factory(stdout=reboot_banner)


def cmd_man(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "man", "args": args}))
    if not args:
        return ctx.result_factory(stderr="What manual page do you want?\n", exit_code=1)

    target_cmd = args[0]
    if target_cmd in MAN_PAGES:
        return ctx.result_factory(stdout=MAN_PAGES[target_cmd])
    return ctx.result_factory(stderr=f"No manual entry for {target_cmd}\n", exit_code=1)


def cmd_restore(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "restore", "args": args}))
    return ctx.result_factory(
        stderr=(
            "[SHELL ADVISORY]: 'restore' is an incident objective, not a shell command.\n"
            "• To restore shell profiles, copy a template using output redirection:\n"
            "    cat /opt/backup/profiles/alice.bashrc > ~/.bashrc\n"
            "• Use 'ls -a' to inspect hidden dotfiles in your current directory.\n"
        ),
        exit_code=1
    )


def cmd_help(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "help", "args": args}))
    flags = ctx.state.system_flags

    if args:
        target = args[0].lower()
        if target in MAN_PAGES:
            return ctx.result_factory(stdout=MAN_PAGES[target])
        return ctx.result_factory(stderr=f"help: no help topics match `{target}'. Try 'man {target}'.\n", exit_code=1)

    lines = [
        "┌────────────────────────────────────────────────────────────────────────┐",
        "│ APOLLO WORKSTATION // EMERGENCY OPERATOR SURVIVAL CARD                 │",
        "├────────────────────────────────────────────────────────────────────────┤",
        "│ BASIC SURVIVAL TOOLKIT:                                                │",
        "│   • ls             : Look around (list visible files in current folder)│",
        "│   • cat <file>     : Open and read a file's contents                   │",
        "│   • pwd            : Check what folder you are currently standing in   │",
        "│   • decrypt        : Ask APOLLO AI to diagnose your last error         │",
        "│   • sync           : Save your game progress to persistent storage     │",
        "│   • reboot / reset : Restart the game from cold boot                   │",
    ]

    if not flags.get("BASHRC_RESTORED", False):
        lines.append("│   • ls -a          : Reveal hidden files (starting with a dot .)       │")
    lines.append("└────────────────────────────────────────────────────────────────────────┘")

    # Progressive / Discoverable entries unlocked as player restores subsystems
    discovered = []
    if flags.get("BUFFER_REPAIRED") or flags.get("BASHRC_RESTORED"):
        discovered.append("  • cd <folder>    : Walk into a folder (e.g. 'cd /opt/backup/profiles').")
        discovered.append("  • man <command>  : Read complete utility manual.")

    if flags.get("LOGS_AUDITED"):
        discovered.append("  • head / tail    : Read the start or end of log streams (e.g. 'tail -n 10 auth.log').")
        discovered.append("  • grep <pattern> : Search for keywords across files (e.g. 'grep -i breach auth.log').")

    if flags.get("RECOVERY_LOCATED") or flags.get("PERMISSIONS_RESTORED"):
        discovered.append("  • find <path>    : Scan filesystem trees (e.g. 'find /mnt/recovery -name \"*.sh\"').")
        discovered.append("  • chmod <mode>   : Update file security modes (e.g. 'chmod +x <file>').")

    if flags.get("MALWARE_TERMINATED") or flags.get("SIGINT_UNLOCKED"):
        discovered.append("  • ps aux         : Scan active background processes.")
        discovered.append("  • kill -9 <PID>  : Terminate a runaway rogue process by PID.")

    if flags.get("NETWORK_ONLINE"):
        discovered.append("  • ip addr / link : Manage network interface hardware (e.g. 'ip link set apollo0 up').")
        discovered.append("  • ss -tulpn      : Inspect active listening network sockets.")
        discovered.append("  • ping <host>    : Send ICMP echo packets to test gateway reachability.")

    if flags.get("PHOENIX_ONLINE"):
        discovered.append("  • phoenix_daemon : PHOENIX emergency restoration cluster service.")

    if discovered:
        lines.append("\nRECOVERED SUBSYSTEM UTILITIES:")
        lines.extend(discovered)

    # Hidden / Locked entries indicator
    hidden_count = 0
    if not (flags.get("BUFFER_REPAIRED") or flags.get("BASHRC_RESTORED")):
        hidden_count += 1
    if not flags.get("LOGS_AUDITED"):
        hidden_count += 1
    if not (flags.get("RECOVERY_LOCATED") or flags.get("PERMISSIONS_RESTORED")):
        hidden_count += 1
    if not (flags.get("MALWARE_TERMINATED") or flags.get("SIGINT_UNLOCKED")):
        hidden_count += 1
    if not flags.get("NETWORK_ONLINE"):
        hidden_count += 1
    if not flags.get("PHOENIX_ONLINE"):
        hidden_count += 1

    if hidden_count > 0:
        lines.append(f"\n[?] {hidden_count} subsystem toolset(s) offline / hidden until restored.")

    # Location-aware extra tip if in /opt/backup/profiles
    if ctx.state.cwd_str == "/opt/backup/profiles" and not flags.get("BASHRC_RESTORED", False):
        lines.append("\nLOCATION TIP: You found the backup profiles! Read 'NOTE_FROM_MORGAN.txt' with 'cat NOTE_FROM_MORGAN.txt' to restore your shell.")

    lines.append(f"\n{get_primary_goal(flags, getattr(ctx.state, 'discovered_clues', {}))}")
    return ctx.result_factory(stdout="\n".join(lines) + "\n")
