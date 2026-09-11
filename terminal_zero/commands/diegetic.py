import datetime
import os
from typing import List
from terminal_zero.core.events import Event
from terminal_zero.core.state import CommandContext, CommandResult
from terminal_zero.core.persistence import save_game_state
from terminal_zero.content.narrative import get_primary_goal, get_todo_content, get_victory_screen
from terminal_zero.content.man_pages import MAN_PAGES
from terminal_zero.content.initial_vfs import build_default_vfs


def cmd_decrypt(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "decrypt", "args": args}))
    last_err = ctx.state.last_stderr.strip()
    if not last_err:
        return ctx.result_factory(
            stdout="[OSIRIS-DIAGNOSTIC]: No recent hardware or kernel fault recorded in buffer.\n"
        )

    if "command not found" in last_err:
        cmd_candidate = last_err.split(":")[1].strip().split()[0] if ":" in last_err else ""
        if cmd_candidate == "append":
            diag = (
                "[OSIRIS-DIAGNOSTIC: FAULT 0x1D - SHELL REDIRECTION ADVISORY]\n"
                "'append' is an action, not a standalone shell command.\n"
                "In Linux shells, use double-arrow redirection '>>' to append data to a file.\n"
                "Example: cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf"
            )
        else:
            diag = (
                f"[OSIRIS-DIAGNOSTIC: FAULT 0x02 - UTILITY UNAVAILABLE]\n"
                f"Binary '{cmd_candidate or 'command'}' was corrupted or stripped during the incident.\n"
                f"Action: Type 'help' or inspect 'TODO.txt' to review active recovery tools."
            )
    elif "<" in last_err or ">" in last_err or any(k in last_err for k in ["proile_src", "profile_src", "target_path"]):
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x1F - PLACEHOLDER SYNTAX]\n"
            "Notice: The '<' and '>' in Morgan's notes represent placeholder names, not literal characters.\n"
            "Action: Replace '<profile_src>' with 'alice.bashrc' and '<target_path>' with '/home/alice/.bashrc'.\n"
            "Exact command: cat alice.bashrc > /home/alice/.bashrc"
        )
    elif "cannot execute text file" in last_err or ("Permission denied" in last_err and any(ext in last_err for ext in [".txt", ".log", ".conf", ".key"])):
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x1E - NON-EXECUTABLE STREAM]\n"
            "Target is a plain-text document, not an executable program.\n"
            "Action: Use 'cat <file>' or 'head <file>' to view file contents."
        )
    elif "Authentication token missing" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x5B - AUTHENTICATION REQUIRED]\n"
            "Daemon initialization aborted: Missing cryptographic authentication key in configuration.\n"
            "Action: Retrieve key from /mnt/recovery/keys/phoenix.key and append to /etc/phoenix/phoenix.conf via '>>'."
        )
    elif "Insecure permissions" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x2E - ACCESS RESTRICTED]\n"
            "Configuration file permissions rejected by daemon security audit (mode must be 0644).\n"
            "Action: Run 'chmod 644 /etc/phoenix/phoenix.conf' to secure configuration permissions."
        )
    elif "Missing configuration file" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x0A - NODE NOT FOUND]\n"
            "Required service configuration file missing from /etc/phoenix/.\n"
            "Action: Restore fallback template from /etc/phoenix/phoenix.conf.default or /opt/backup/phoenix.conf."
        )
    elif "Operation not permitted" in last_err and "phoenix" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x2D - ACCESS RESTRICTED]\n"
            "/opt/phoenix is locked by root system services.\n"
            "Action: Investigate incident logs in /var/log/ to trace the breach before accessing system services."
        )
    elif "No such file or directory" in last_err:
        missing_target = ""
        if "cannot open '" in last_err:
            missing_target = last_err.split("cannot open '")[1].split("'")[0]
        elif "cannot access '" in last_err:
            missing_target = last_err.split("cannot access '")[1].split("'")[0]
        elif ":" in last_err:
            parts = last_err.split(":")
            if len(parts) >= 2:
                missing_target = parts[1].strip()

        basename = missing_target.split("/")[-1] if missing_target else ""
        if basename and not basename.startswith("."):
            dotname = "." + basename
            node, _ = ctx.vfs.get_node(ctx.state.current_path, dotname)
            if node:
                diag = (
                    f"[OSIRIS-DIAGNOSTIC: FAULT 0x1A - HIDDEN NODE MATCH]\n"
                    f"File '{basename}' not found, but hidden file '{dotname}' exists in this directory.\n"
                    f"Action: Type 'cat {dotname}' to view it. (Remember hidden dotfiles start with a dot '.')"
                )
            else:
                diag = (
                    "[OSIRIS-DIAGNOSTIC: FAULT 0x1A - PATH NOT FOUND]\n"
                    "Target node does not exist in the active directory tree.\n"
                    "Action: Run 'ls' or 'pwd' to verify path coordinates before addressing target."
                )
        else:
            diag = (
                "[OSIRIS-DIAGNOSTIC: FAULT 0x1A - PATH NOT FOUND]\n"
                "Target node does not exist in the active directory tree.\n"
                "Action: Run 'ls' or 'pwd' to verify path coordinates before addressing target."
            )
    elif "Is a directory" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x1B - ILLEGAL NODE TYPE]\n"
            "Target path resolves to a directory node, but the requested binary requires a file stream.\n"
            "Action: Use 'cd' to traverse or 'ls' to inspect contents."
        )
    elif "Not a directory" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x1C - INVALID TRAVERSAL]\n"
            "Cannot traverse into a standard data file.\n"
            "Action: Use 'cat', 'head', or 'tail' to read file contents."
        )
    elif "Permission denied" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x2E - ACCESS RESTRICTED]\n"
            "Node execution or read/write bits are disabled.\n"
            "Action: Use 'chmod +x <target>' or 'chmod 755 <target>' to elevate node permissions."
        )
    elif "Network is unreachable" in last_err or "network unreachable" in last_err.lower() or "network gateway unreachable" in last_err.lower():
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x3D - NETWORK OFFLINE]\n"
            "Virtual network interface link state is DOWN.\n"
            "Action: Run 'ip link set osiris0 up' to activate the network adapter and verify routing."
        )
    elif "No such process" in last_err or "invalid signal specification" in last_err or "invalid pid" in last_err or "kill:" in last_err:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x5E - NUMERIC PID REQUIRED]\n"
            "Notice: 'kill' requires a numeric Process ID (PID), not a process name or command string.\n"
            "Action: Run 'ps aux' to find the rogue miner's numeric PID in the PID column, then terminate it with 'kill -9 104'."
        )
    elif any(k in last_err.lower() for k in ["missing file operand", "missing pattern", "missing argument", "option requires", "invalid line count", "invalid count", "invalid mode"]):
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x05 - ARITY MISMATCH]\n"
            "Command invoked without mandatory arguments or with malformed options.\n"
            "Action: Run 'man <command>' to inspect supported syntax."
        )
    else:
        diag = (
            "[OSIRIS-DIAGNOSTIC: FAULT 0x99 - GENERAL EXCEPTION]\n"
            "Subsystem failure registered in execution pipeline.\n"
            "Action: Consult system logs in /var/log/syslog or inspect command manual via 'man'."
        )

    output = (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│ OSIRIS RECOVERY DAEMON v2.4 — ERROR BUFFER TRANSLATION   │\n"
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
            stderr="[PHOENIX ERROR]: Network gateway unreachable. Interface 'osiris0' is DOWN.\n", 
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
    victory = get_victory_screen()
    return ctx.result_factory(
        stdout=(
            "[PHOENIX-DAEMON]: Emergency Restoration Protocol activated. Listening on 127.0.0.1:8080. Gateway ONLINE.\n"
            + victory
        )
    )


def cmd_phoenix_ctl(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "phoenix_ctl", "args": args}))
    return cmd_phoenix_daemon(ctx, args)


def cmd_osiris_net(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "osiris-net", "args": args}))
    iface_state = ctx.state.network_interfaces.get("osiris0", {}).get("state", "DOWN")
    return ctx.result_factory(
        stdout=f"[OSIRIS-NET v1.0]: Subnet link state is {iface_state}. Gateway 10.0.42.1\n"
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

    from terminal_zero.engine.repl import get_boot_screen
    reboot_banner = (
        "\nBroadcast message from root@osiris (tty1) (system reboot):\n\n"
        "The system is going down for reboot NOW!\n"
        "Restarting system...\n\n"
        + get_boot_screen(ctx.state.system_flags)
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

    if not flags.get("README_INSPECTED", False):
        standby_msg = (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [!] SURVIVAL MANUAL STANDBY:                                           │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ Emergency Operator Survival Card is offline.                           │\n"
            "│ Inspect 'README.txt' using 'cat README.txt' to initialize instructions.│\n"
            "└────────────────────────────────────────────────────────────────────────┘\n"
        )
        return ctx.result_factory(stdout=standby_msg)

    lines = [
        "┌────────────────────────────────────────────────────────────────────────┐",
        "│ OSIRIS WORKSTATION // EMERGENCY OPERATOR SURVIVAL CARD                 │",
        "├────────────────────────────────────────────────────────────────────────┤",
        "│ BASIC SURVIVAL TOOLKIT:                                                │",
        "│   • ls             : Look around (list visible files in current folder)│",
        "│   • cat <file>     : Open and read a file's contents                   │",
        "│   • pwd            : Check what folder you are currently standing in   │",
        "│   • decrypt        : Ask OSIRIS AI to diagnose your last error         │",
        "│   • manuals        : Browse collected field manuals and cheat sheets   │",
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

    if flags.get("RECOVERY_LOCATED") or flags.get("PERMISSIONS_RESTORED") or flags.get("FIND_UNLOCKED"):
        discovered.append("  • find <path>    : Scan filesystem trees (e.g. 'find /mnt/recovery -name \"*.key\"').")
        discovered.append("  • chmod <mode>   : Update file security modes (e.g. 'chmod +x <file>').")

    if flags.get("MALWARE_TERMINATED"):
        discovered.append("  • ps aux         : Scan active background processes.")
        discovered.append("  • kill -9 <PID>  : Terminate a runaway rogue process by PID.")

    if flags.get("NETWORK_ONLINE"):
        discovered.append("  • ip addr / link : Manage network interface hardware (e.g. 'ip link set osiris0 up').")
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
    if not (flags.get("RECOVERY_LOCATED") or flags.get("PERMISSIONS_RESTORED") or flags.get("FIND_UNLOCKED")):
        hidden_count += 1
    if not flags.get("MALWARE_TERMINATED"):
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


def cmd_note(ctx: CommandContext, args: List[str]) -> CommandResult:
    if not args:
        return ctx.result_factory(
            stdout="[PLAYTEST NOTE]: Usage: note <your feedback here without quotes>\n"
        )
    message = " ".join(args)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sector = ctx.state.cwd_str
    completed = sum(1 for v in ctx.state.system_flags.values() if v)
    total = len(ctx.state.system_flags)
    log_entry = f"[{ts}] [{sector}] [Flags: {completed}/{total}] {message}\n"
    try:
        with open("playtest_notes.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass
    return ctx.result_factory(stdout=f'[NOTE RECORDED]: "{message}"\n')


def cmd_feedback(ctx: CommandContext, args: List[str]) -> CommandResult:
    return cmd_note(ctx, args)


def cmd_taskctl(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "taskctl", "args": args}))
    ctx.state.system_flags["TODO_LINKED"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "TODO_LINKED", "value": True}))
    banner = (
        "[taskctl]: Linking '/home/alice/TODO.txt' to shell command vector...\n"
        "[!] SHORTCUT REGISTERED: Global commands 'todo' and 'tasks' are now active!\n"
        "Type 'todo' from any directory to inspect your recovery progress.\n"
    )
    return ctx.result_factory(stdout=banner)


def cmd_todo(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "todo", "args": args}))
    if not ctx.state.system_flags.get("TODO_LINKED", False):
        return ctx.result_factory(
            stderr="bash: todo: command not found (Tip: inspect '/home/alice/TODO.txt' for instructions)\n",
            exit_code=127
        )
    content = get_todo_content(ctx.state.system_flags, getattr(ctx.state, 'discovered_clues', {}))
    return ctx.result_factory(stdout=content)


def cmd_tasks(ctx: CommandContext, args: List[str]) -> CommandResult:
    return cmd_todo(ctx, args)


def _check_all_triage_complete(ctx: CommandContext) -> str:
    clues = getattr(ctx.state, "discovered_clues", {})
    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))
    if count == 4 and not ctx.state.system_flags.get("LOGS_AUDITED", False):
        ctx.state.system_flags["LOGS_AUDITED"] = True
        ctx.bus.publish(Event("flag_changed", {"flag": "LOGS_AUDITED", "value": True}))
        return (
            "\n"
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [!] ALL INCIDENT LEADS VERIFIED (4/4 Complete)                         │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ Milestone 2 Complete: Security breach triaged & incident dossier locked!│\n"
            "│ Next Step: Head to /mnt/recovery/bin/ to restore tool permissions.     │\n"
            "└────────────────────────────────────────────────────────────────────────┘\n"
        )
    return ""


def cmd_triage_process(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "triage_process", "args": args}))
    if not args:
        return ctx.result_factory(
            stderr="[ERROR]: Missing argument. Usage: triage_process <PID>\n"
                   "Tip: Audit /var/log/auth.log for the red [ALERT-0x01] rogue miner process ID.\n",
            exit_code=1
        )
    val = args[0].strip()
    if val == "104":
        ctx.state.discovered_clues["ALERT_0x01"] = True
        ctx.bus.publish(Event("clue_discovered", {"clue_id": "ALERT_0x01"}))
        banner = "\033[1;32m[SUCCESS]: Intruder process verified!\033[0m PID 104 (sys_miner) logged in incident dossier.\n"
        banner += _check_all_triage_complete(ctx)
        return ctx.result_factory(stdout=banner)
    else:
        return ctx.result_factory(
            stderr=f"\033[1;31m[ERROR]: PID '{val}' incorrect.\033[0m Audit /var/log/auth.log for the red [ALERT-0x01] rogue miner process ID.\n",
            exit_code=1
        )


def cmd_triage_sector(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "triage_sector", "args": args}))
    if not args:
        return ctx.result_factory(
            stderr="[ERROR]: Missing argument. Usage: triage_sector <FILE_PATH>\n"
                   "Tip: Audit /var/log/auth.log for the yellow [ALERT-0x02] stripped recovery script.\n",
            exit_code=1
        )
    val = args[0].strip()
    if val in ["/mnt/recovery/bin/recovery.sh", "recovery.sh", "/mnt/recovery/bin"]:
        ctx.state.discovered_clues["ALERT_0x02"] = True
        ctx.bus.publish(Event("clue_discovered", {"clue_id": "ALERT_0x02"}))
        banner = "\033[1;32m[SUCCESS]: Tampered sector verified!\033[0m /mnt/recovery/bin/recovery.sh logged in incident dossier.\n"
        banner += _check_all_triage_complete(ctx)
        return ctx.result_factory(stdout=banner)
    else:
        return ctx.result_factory(
            stderr=f"\033[1;33m[ERROR]: Sector path '{val}' incorrect.\033[0m Audit /var/log/auth.log for the yellow [ALERT-0x02] stripped recovery script.\n",
            exit_code=1
        )


def cmd_triage_interface(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "triage_interface", "args": args}))
    if not args:
        return ctx.result_factory(
            stderr="[ERROR]: Missing argument. Usage: triage_interface <DEVICE_NAME>\n"
                   "Tip: Audit /var/log/syslog for the cyan [ALERT-0x03] degraded network link.\n",
            exit_code=1
        )
    val = args[0].strip()
    if val == "osiris0":
        ctx.state.discovered_clues["ALERT_0x03"] = True
        ctx.bus.publish(Event("clue_discovered", {"clue_id": "ALERT_0x03"}))
        banner = "\033[1;32m[SUCCESS]: Degraded interface verified!\033[0m Device osiris0 logged in incident dossier.\n"
        banner += _check_all_triage_complete(ctx)
        return ctx.result_factory(stdout=banner)
    else:
        return ctx.result_factory(
            stderr=f"\033[1;36m[ERROR]: Interface '{val}' incorrect.\033[0m Audit /var/log/syslog for the cyan [ALERT-0x03] degraded network link.\n",
            exit_code=1
        )


def cmd_triage_service(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "triage_service", "args": args}))
    if not args:
        return ctx.result_factory(
            stderr="[ERROR]: Missing argument. Usage: triage_service <SERVICE_NAME>\n"
                   "Tip: Audit /var/log/syslog for the magenta [ALERT-0x04] killed cluster daemon.\n",
            exit_code=1
        )
    val = args[0].strip()
    if val in ["phoenix-sync.service", "phoenix-sync"]:
        ctx.state.discovered_clues["ALERT_0x04"] = True
        ctx.bus.publish(Event("clue_discovered", {"clue_id": "ALERT_0x04"}))
        banner = "\033[1;32m[SUCCESS]: Terminated service verified!\033[0m phoenix-sync.service logged in incident dossier.\n"
        banner += _check_all_triage_complete(ctx)
        return ctx.result_factory(stdout=banner)
    else:
        return ctx.result_factory(
            stderr=f"\033[1;35m[ERROR]: Service '{val}' incorrect.\033[0m Audit /var/log/syslog for the magenta [ALERT-0x04] killed cluster daemon.\n",
            exit_code=1
        )


def cmd_manuals(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "manuals", "args": args}))

    catalog = [
        ("SURVIVAL CARD", "/home/alice/README.txt", "Basic Navigation, Terminal Diagnostics & Decrypt"),
        ("LONG LISTING GUIDE", "/opt/backup/profiles/.HOW_TO_READ_LL.txt", "File Details, Modes & Permissions Breakdown"),
        ("PROFILE SCRATCHPAD", "/opt/backup/profiles/NOTE_FROM_MORGAN.txt", "Shell Profile Template & Redirection Overwrite"),
        ("LOG TRIAGE SCRATCHPAD", "/var/log/NOTE_FROM_MORGAN.txt", "Log Streams, Filtering Noise & Search Signatures"),
        ("LOG FORENSICS MANUAL", "/var/log/HOW_TO_READ_LOGS.txt", "Log Anatomy, Event Formatting & Filtering"),
        ("GREP FORENSICS GUIDE", "/var/log/.grep_juice", "Log Filter Patterns & Practical Grep Recipes"),
        ("SECOPS TRIAGE GUIDE", "/var/log/REPAIR_COMMANDS.txt", "Incident Dossier Registration Commands"),
        ("RECOVERY SCRATCHPAD", "/mnt/recovery/NOTE_FROM_MORGAN.txt", "Recursive Search Utility & Key Location"),
        ("PERMISSIONS SCRATCHPAD", "/mnt/recovery/bin/PERMISSIONS_NOTE.txt", "Octal Mode Bits, Execute Rights & Signal Traps"),
        ("PROCESS SCRATCHPAD", "/tmp/NOTE_FROM_MORGAN.txt", "Process Tables, High CPU & Unconditional Signals"),
        ("NETWORK SCRATCHPAD", "/etc/network/NOTE_FROM_MORGAN.txt", "Interface Link State & Gateway Ping Verification"),
        ("PHOENIX SCRATCHPAD", "/etc/phoenix/NOTE_FROM_MORGAN.txt", "Append Mode (>>), Config Permissions & Daemon"),
        ("SYSADMIN PROTOCOLS", "/usr/share/doc/sysadmin_notes.txt", "Process Management, File Modes & Networking"),
    ]

    discovered = getattr(ctx.state, "discovered_manuals", {})
    available = []

    for title, path, desc in catalog:
        if discovered.get(path, False):
            node, _ = ctx.vfs.get_node([], path)
            if node:
                available.append((title, path, desc))

    if not available:
        return ctx.result_factory(
            stdout=(
                "================================================================================\n"
                "               OSIRIS WORKSTATION // DISCOVERED FIELD MANUALS\n"
                "================================================================================\n"
                "[!] No field manuals recovered yet.\n"
                "Inspect documentation files using 'cat' to register them in your manual inventory.\n"
                "================================================================================\n"
            )
        )

    lines = [
        "================================================================================",
        "               OSIRIS WORKSTATION // DISCOVERED FIELD MANUALS",
        "================================================================================",
        f"Index of recovered operational guides and cheat sheets ({len(available)} discovered):\n"
    ]

    for title, path, desc in available:
        lines.append(f"  • \033[1;36m{title:<22}\033[0m : {desc}")
        lines.append(f"    Location: {path}  (Read: 'cat {path}')\n")

    lines.append("================================================================================")
    lines.append("Tip: Use 'cat <path>' to review any manual, or 'man <command>' for command help.")
    lines.append("================================================================================")
    return ctx.result_factory(stdout="\n".join(lines) + "\n")


def cmd_docs(ctx: CommandContext, args: List[str]) -> CommandResult:
    return cmd_manuals(ctx, args)


def cmd_fieldguide(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "fieldguide", "args": args}))
    from terminal_zero.content.debriefs import DebriefManager

    cards = []
    for flag, card_text in DebriefManager.DEBRIEFS.items():
        if ctx.state.system_flags.get(flag, False) or ctx.state.unlocked_cards.get(flag, False):
            title = DebriefManager.TITLES.get(flag, flag)
            cards.append((title, card_text))

    if not cards:
        return ctx.result_factory(
            stdout=(
                "================================================================================\n"
                "               OSIRIS WORKSTATION // LINUX FIELD GUIDE VAULT\n"
                "================================================================================\n"
                "[!] No Field Guide entries unlocked yet.\n"
                "Complete workstation recovery milestones to collect real-world Linux debrief cards!\n"
                "================================================================================\n"
            )
        )

    lines = [
        "================================================================================",
        "               OSIRIS WORKSTATION // LINUX FIELD GUIDE VAULT",
        "================================================================================",
        f"Index of collected real-world Linux administration debriefs ({len(cards)} unlocked):\n"
    ]

    for title, card_text in cards:
        lines.append(card_text)
        lines.append("")

    lines.append("================================================================================")
    lines.append("Tip: Use 'manuals' for in-game documentation, or 'man <cmd>' for syntax.")
    lines.append("================================================================================")
    return ctx.result_factory(stdout="\n".join(lines) + "\n")


def cmd_cards(ctx: CommandContext, args: List[str]) -> CommandResult:
    return cmd_fieldguide(ctx, args)


def cmd_debriefs(ctx: CommandContext, args: List[str]) -> CommandResult:
    return cmd_fieldguide(ctx, args)


def cmd_lore(ctx: CommandContext, args: List[str]) -> CommandResult:
    return cmd_fieldguide(ctx, args)


def cmd_cluster_probe(ctx: CommandContext, args: List[str]) -> CommandResult:
    ctx.bus.publish(Event("command_executed", {"command": "cluster_probe", "args": args}))

    # 1. Oracle Bypass Protection: Master triage bus offline before log triage
    if not ctx.state.system_flags.get("LOGS_AUDITED", False):
        return ctx.result_factory(
            stderr="[PROBE FAULT]: Master triage bus offline. Audit security logs in /var/log before initiating cluster handshake.\n",
            exit_code=1
        )

    # 2. State Evaluations
    cpu_ok = not any(p.pid == 104 for p in ctx.state.process_table) and ctx.state.system_flags.get("CPU_NORMAL", False)

    key_node, _ = ctx.vfs.get_node([], "/mnt/recovery/keys/phoenix.key")
    has_key = key_node is not None and "PX-KEY-7701-ALPHA" in (key_node.content or "")
    ctrl_c_ok = ctx.state.unlocked_ergonomics.get("ctrl_c", False) is True
    storage_ok = has_key and ctrl_c_ok

    net_iface_ok = ctx.state.network_interfaces.get("osiris0", {}).get("state") == "UP"
    net_online = ctx.state.system_flags.get("NETWORK_ONLINE", False)
    network_ok = net_iface_ok and net_online

    all_passed = cpu_ok and storage_ok and network_ok

    tag_success = "\033[1;32m[ SUCCESS ]\033[0m"
    tag_pending = "\033[1;33m[ PENDING ]\033[0m"

    compute_tag = tag_success if cpu_ok else tag_pending
    storage_tag = tag_success if storage_ok else tag_pending
    network_tag = tag_success if network_ok else tag_pending

    lines = [
        "================================================================================",
        "                   PHOENIX CLUSTER RESTORATION PROBE v2.4",
        "================================================================================",
        f"  [ SPOKE A : COMPUTE ] ......... {compute_tag} -> Rogue miner killed, CPU normalized",
        f"  [ SPOKE B : STORAGE ] ......... {storage_tag} -> Phoenix recovery key loaded, SIGINT mapped",
        f"  [ SPOKE C : NETWORK ] ......... {network_tag} -> Interface osiris0 link UP, gateway online",
        "================================================================================",
    ]

    if not all_passed:
        lines.append("\n[DIAGNOSTIC ADVISORIES]:")
        if not cpu_ok:
            lines.append("  • Compute fault: Inspect /tmp and check running processes ('ps aux'). Rogue task still active.")
        if not storage_ok:
            lines.append("  • Storage fault: Locate recovery key in /mnt/recovery/keys/ and execute /mnt/recovery/bin/recovery.sh.")
        if not network_ok:
            lines.append("  • Network fault: Bring up adapter ('ip link set osiris0 up') and verify connectivity ('ping -c 4 10.0.42.1').")
        lines.append("")
        return ctx.result_factory(stdout="\n".join(lines) + "\n", exit_code=0)

    ctx.state.system_flags["VERTICAL_SLICE_COMPLETE"] = True
    ctx.bus.publish(Event("flag_changed", {"flag": "VERTICAL_SLICE_COMPLETE", "value": True}))

    lines.extend([
        "[ CLUSTER STATUS: SYNCHRONIZED ]",
        "All node telemetry verified. Phoenix service daemon online.",
        "",
        "================================================================================",
        " [VOX TRANSMISSION // PRIORITY CHANNEL 0x01]",
        "================================================================================",
        " Morgan: \"Alice... the telemetry cleared! The cluster handshake went through!",
        "          Every node in the cluster is acknowledging our heartbeat.",
        "          You took back control of this machine from the ground up.\"",
        "================================================================================",
        "",
        "*** VERTICAL SLICE COMPLETE ***",
        ""
    ])
    return ctx.result_factory(stdout="\n".join(lines) + "\n", exit_code=0)


