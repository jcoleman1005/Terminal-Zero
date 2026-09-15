from typing import Dict, Optional
from terminal_zero.core.vfs import VFSNode
from terminal_zero.content.narrative import get_todo_content, get_incident_dossier


def build_default_vfs(flags: Optional[Dict[str, bool]] = None) -> VFSNode:
    if flags is None:
        flags = {}
    root = VFSNode(type="dir", permissions="755", owner="root", group="root")

    def add_dir(path: str, perms: str = "755", owner: str = "root", group: str = "root") -> VFSNode:
        parts = [p for p in path.split("/") if p]
        curr = root
        for p in parts:
            if p not in curr.children:
                curr.children[p] = VFSNode(type="dir", permissions=perms, owner=owner, group=group)
            curr = curr.children[p]
        return curr

    def add_file(path: str, content: str, perms: str = "644", owner: str = "root", group: str = "root") -> VFSNode:
        parts = [p for p in path.split("/") if p]
        parent_parts = parts[:-1]
        filename = parts[-1]
        parent = root
        for p in parent_parts:
            if p not in parent.children:
                parent.children[p] = VFSNode(type="dir", permissions="755", owner=owner, group=group)
            parent = parent.children[p]
        node = VFSNode(type="file", permissions=perms, owner=owner, group=group, content=content)
        parent.children[filename] = node
        return node

    # Standard POSIX & FHS Structure across all sectors
    dirs = [
        "bin", "usr/bin", "usr/share/doc", "var/log", "tmp",
        "mnt/recovery", "mnt/recovery/archive/2038", "mnt/recovery/backups/stale", "mnt/recovery/tools/legacy",
        "mnt/recovery/bin", "mnt/recovery/keys", "mnt/recovery/docs",
        "opt/backup", "opt/backup/profiles", "etc/network", "etc/phoenix", "etc/skel",
        "opt/phoenix", "opt/phoenix/bin", "opt/phoenix/recovery", "opt/phoenix/config"
    ]
    for d in dirs:
        add_dir("/" + d)

    add_dir("/home", perms="755", owner="root", group="root")
    add_dir("/home/alice", perms="755", owner="alice", group="alice")
    add_dir("/home/alice/diagnostics", perms="755", owner="alice", group="alice")
    # Hidden archive of personal logs left by the previous operator (Maya).
    # Discovered when the player runs 'ls -a' in /home/alice/.
    add_dir("/home/alice/.maya_notes", perms="755", owner="alice", group="alice")
    add_dir("/home/alice/.maya_notes/archive", perms="755", owner="alice", group="alice")
    add_dir("/etc/skel", perms="0755", owner="root", group="root")

    # Soft-Gate /opt/phoenix via Permissions (0700 until LOGS_AUDITED or RECOVERY_LOCATED is set)
    phoenix_perms = "755" if (flags.get("LOGS_AUDITED", False) or flags.get("RECOVERY_LOCATED", False)) else "700"
    add_dir("/opt/phoenix", perms=phoenix_perms, owner="root")

    # Standard Binaries in /bin and /usr/bin
    for b in [
        "cat", "cd", "echo", "exit", "ls", "pwd", "sync", "decrypt", "osiris-diagnostics",
        "chmod", "man", "ps", "kill", "ip", "ss", "ping", "head", "tail", "grep", "find",
        "stty", "rm", "cp", "touch", "cluster_probe",
        "repair_buffer", "phoenix_ctl", "phoenix_daemon", "osiris-net", "tree",
        "note", "feedback", "taskctl", "todo", "tasks", "manuals", "docs", "fieldguide",
        "triage_process", "triage_sector", "triage_interface", "triage_service"
    ]:
        add_file(f"/bin/{b}", "ELF 64-bit LSB executable\n", perms="755")
        add_file(f"/usr/bin/{b}", "ELF 64-bit LSB executable\n", perms="755")

    # Evaluator binary in /opt/phoenix/bin
    add_file("/opt/phoenix/bin/cluster_probe", "ELF 64-bit LSB executable [CLUSTER-PROBE v2.4]\n", perms="755", owner="root")

    # /etc/motd
    add_file(
        "/etc/motd",
        "================================================================================\n"
        "                    OSIRIS WORKSTATION // KERNEL v5.19.0-24\n"
        "================================================================================\n"
        " [ALERT] SYSTEM INTEGRITY COMPROMISED. AUTOMATIC QUARANTINE PROTOCOL ACTIVE.\n"
        " [ALERT] WAN LINK SEVERED. PRIMARY LINE DISCIPLINE DRIVERS CORRUPTED.\n"
        " \n"
        " Current Session: alice [CONSOLE TTY1]\n"
        " Security Context: RESTRICTED SANDBOX (/home/alice)\n\n"
        " Standard desktop services are offline. Terminal fallback active.\n"
        " Review local incident logs and recovery instructions in your home directory.\n"
        "================================================================================\n",
        perms="644",
        owner="root"
    )

    # Milestone 0: /home/alice & /home/alice/diagnostics
    readme_content = (
        "// ============================================================================\n"
        "// OSIRIS WORKSTATION // EMERGENCY OPERATOR PROTOCOL\n"
        "// ============================================================================\n"
        "Alice—\n\n"
        "If you're seeing this on your screen, the automated lockdown caught you at your\n"
        "desk when the network dropped. Don't panic. The system put your terminal in a\n"
        "quarantine environment (/home/alice) so the attack couldn't touch your shell.\n\n"
        "The desktop GUI is gone. You're going to have to drive this machine through the\n"
        "command line.\n\n"
        "Keep these three commands in your head right now:\n"
        "  • 'pwd'            (Print Working Directory)\n"
        "    Tells you where you are standing in the system tree.\n"
        "  • 'ls'             (List)\n"
        "    Shows you all visible files and folders in your current directory.\n"
        "  • 'cat <filename>' (Concatenate / Read)\n"
        "    Dumps the text inside a file right onto your screen.\n"
        "    Example: cat README.txt\n\n"
        "Your terminal driver took a direct hit on boot, which is why your Up/Down arrow\n"
        "keys aren't recalling previous commands.\n\n"
        "Inspect 'BOOT_FAIL.log' using 'cat' to see the exact fault, then\n"
        "run the recovery utility it specifies.\n\n"
        "If a command fails or spits out an error you don't understand, type 'decrypt'.\n"
        "I wrote it to catch whatever POSIX error the kernel just threw and translate\n"
        "the sysadmin jargon into plain English.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/home/alice/README.txt", readme_content, perms="644", owner="alice")

    boot_fail_content = (
        "[03:41:02.109] [KERNEL ALERT] Osiris Workstation Core Subsystem Degraded (Boot ID: 0x42-INIT).\n"
        "[03:41:02.112] [ERR_TTY_RING] Input ring buffer desynchronized at line discipline layer.\n"
        "[03:41:02.115] [HARDWARE FAULT] Interactive command recall (UP/DOWN arrow keys) suspended.\n"
        "[03:41:02.118] [DRIVER STATE] Line discipline running in raw unbuffered mode (-icanon echo).\n"
        "[03:41:02.120] [DIAGNOSTIC] Register mismatch in terminal driver ring registers.\n"
        "[03:41:02.125] [ACTION REQUIRED] Reset line discipline to sane defaults by running: 'stty sane'\n"
    )
    add_file("/home/alice/BOOT_FAIL.log", boot_fail_content, perms="644", owner="alice")
    add_file("/home/alice/diagnostics/BOOT_FAIL.log", boot_fail_content, perms="644", owner="alice")

    add_file(
        "/home/alice/diagnostics/INCIDENT_REPORT.log",
        get_incident_dossier({}),
        perms="644",
        owner="alice"
    )

    # /etc/os-release (System Information)
    add_file(
        "/etc/os-release",
        "NAME=\"Osiris Workstation OS\"\n"
        "VERSION=\"2.4 LTS (Recovery Build 0x42)\"\n"
        "ID=osiris\n"
        "ID_LIKE=debian\n"
        "PRETTY_NAME=\"Osiris OS 2.4 (x86_64-osiris-linux-gnu)\"\n"
        "HOME_URL=\"https://osiris.internal/workstation\"\n",
        perms="644",
        owner="root"
    )

    # Milestone 1: /opt/backup/profiles & /home/alice
    # Note: visible as MORGAN_NOTE.txt (no dot-prefix). The ls -a mechanic is taught
    # here conceptually, then rewarded later when the player finds hidden lore in
    # other directories they revisit (starting with .maya_notes/ right here).
    # Option B: teaches rm locally, sends player to /opt/backup/profiles/ for cp lesson.
    # Option C: frames Maya's notes as character archaeology, not a tutorial.
    note_content = (
        "// STICKY NOTE TAPED TO MONITOR FRAME\n"
        "Alice—\n\n"
        "The attacker didn't just break the drivers; they tried to bury their tracks.\n\n"
        "Once you fix the terminal buffer ('stty sane'), remember that Unix hides files\n"
        "and directories whose names start with a dot. Plain 'ls' won't show them.\n"
        "You need the '-a' flag — it stands for 'all':\n"
        "  ls -a\n\n"
        "There's a corrupted shell config the attacker left behind. Delete it.\n"
        "'rm' removes a file permanently — no trash bin, no undo. It takes one\n"
        "argument: the path to the target.\n"
        "  rm /home/alice/.bashrc.corrupt\n\n"
        "Then head to /opt/backup/profiles/ — I left the clean replacement there\n"
        "along with instructions for getting it into place.\n\n"
        "The previous operator also left some personal logs in a hidden directory here.\n"
        "Her notes are raw — she was figuring this out in real time, same as you.\n"
        "Once you know 'ls -a', you'll find them.\n\n"
        "— Morgan\n"
    )
    add_file("/home/alice/MORGAN_NOTE.txt", note_content, perms="644", owner="alice", group="alice")
    add_file(
        "/home/alice/.bashrc.corrupt",
        "# CORRUPTED ENVIRONMENT PROFILE\n# SYNTAX ERROR AT LINE 1: BAD RECOVERY DESCRIPTOR\n",
        perms="0644",
        owner="alice",
        group="alice"
    )
    alice_bashrc_content = (
        "# Clean Operator Profile for OSIRIS Workstation (User: alice)\n"
        "# Base environment initialization & Readline recovery\n"
        "export PATH=\"/bin:/usr/bin:/opt/phoenix/bin\"\n"
        "export PS1=\"\\u@osiris:\\w\\$ \"\n\n"
        "# Readline Ergonomics & Completion Hooks\n"
        "bind 'set show-all-if-ambiguous on'\n"
        "bind 'set completion-ignore-case on'\n"
        "bind 'TAB:complete'\n\n"
        "# System Aliases\n"
        "alias ll='ls -la'\n"
        "alias cls='clear'\n"
    )
    add_file(
        "/home/alice/.bashrc.default",
        alice_bashrc_content,
        perms="0444",
        owner="root",
        group="root"
    )
    add_file(
        "/etc/skel/.bashrc",
        alice_bashrc_content,
        perms="0644",
        owner="root",
        group="root"
    )

    morgan_note = (
        "// ============================================================================\n"
        "// INCIDENT SCRATCHPAD // OSIRIS WORKSTATION // PRIORITY: HIGH\n"
        "// HOST: osiris-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 03:42:11 AM\n"
        "// FILE: /opt/backup/profiles/MORGAN_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Alice—\n\n"
        "You found it — 'alice.bashrc'. That's your clean shell profile.\n\n"
        "'cp' copies a file. It takes exactly two arguments, always in this order:\n"
        "  cp <source> <destination>\n"
        "Source first. Destination second. Always.\n\n"
        "Copy the profile into your home directory:\n"
        "  cp alice.bashrc /home/alice/.bashrc\n\n"
        "Once that file is in place your Readline bindings will link back up.\n"
        "Tab autocompletion will be live again — no more typing full paths by hand.\n\n"
        "I also added an alias for 'll' inside that profile. Use it. It runs 'ls -la'\n"
        "under the hood — permissions, ownership, and hidden dotfiles in one view.\n\n"
        "I'm heading toward /var/log/ to see what kind of malware they dropped on us.\n"
        "Fix your profile and meet me there.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/opt/backup/profiles/MORGAN_NOTE.txt", morgan_note, perms="644", owner="root")

    ll_guide_content = (
        "================================================================================\n"
        "         SYSADMIN REFERENCE GUIDE // HOW TO READ 'll' (LONG LISTING)\n"
        "================================================================================\n"
        "Standard 'ls' only shows visible filenames.\n"
        "The 'll' shortcut reveals hidden dotfiles and prints 5 critical columns:\n\n"
        "  [ PERMISSIONS ]  [ LINKS ]  [ OWNER ]  [ SIZE ]  [ FILENAME ]\n"
        "  -rw-r--r--       1          root       4096      alice.bashrc\n"
        "  drwxr-xr-x       1          root       4096      profiles/\n"
        "  ----------       1          root       4096      recovery.sh\n\n"
        "--------------------------------------------------------------------------------\n"
        "DECODING THE PERMISSIONS COLUMN:\n"
        "--------------------------------------------------------------------------------\n"
        "• 1st character: 'd' = Directory (folder), '-' = Regular file.\n"
        "• Next 3 chars : Owner permissions:\n"
        "                 'r' = Read (can view contents with 'cat' or 'head')\n"
        "                 'w' = Write (can edit or overwrite with '>')\n"
        "                 'x' = Execute (can run programs or scripts like './tool')\n"
        "                 '-' = Permission revoked / missing.\n\n"
        "[KEY RECOVERY TAKEAWAY]:\n"
        "If a tool has '---' instead of 'r-x' or 'rwx', it cannot run!\n"
        "You can restore executable permissions on any file using: \033[1;33mchmod +x <filename>\033[0m\n"
        "================================================================================\n"
    )
    add_file("/opt/backup/profiles/LL_GUIDE.txt", ll_guide_content, perms="644", owner="root")

    add_file("/opt/backup/profiles/alice.bashrc", alice_bashrc_content, perms="644", owner="root")
    add_file(
        "/home/alice/.bashrc",
        "",
        perms="0644",
        owner="alice",
        group="alice"
    )
    add_file(
        "/home/alice/.bash_history",
        "pwd\nls -la\ncat diagnostics/BOOT_FAIL.log\nrepair_buffer\ncat MORGAN_NOTE.txt\nls -a\nrm /home/alice/.bashrc.corrupt\ncd /opt/backup/profiles\ncat MORGAN_NOTE.txt\ncp alice.bashrc /home/alice/.bashrc\n",
        perms="600",
        owner="alice",
        group="alice"
    )
    add_file(
        "/home/alice/TODO.txt",
        get_todo_content(flags),
        perms="644",
        owner="alice",
        group="alice"
    )
    add_file(
        "/usr/share/doc/mapping_tool.txt",
        "UTILITY RECOVERY NOTE:\nVisual hierarchy utility 'tree' preserved under /opt/phoenix/recovery/tree\n",
        perms="644",
        owner="root"
    )
    add_file(
        "/usr/share/doc/sysadmin_notes.txt",
        "================================================================================\n"
        "             SYSADMIN PROTOCOLS // PROCESSES, MODES & NETWORKING\n"
        "================================================================================\n"
        "1. PROCESS SUPERVISION & SIGNALS:\n"
        "   • \033[1;33mps aux\033[0m          : Inspect active system processes (PID, %CPU, COMMAND).\n"
        "   • \033[1;33mkill -9 <PID>\033[0m   : Dispatch forceful SIGKILL signal to terminate rogue tasks.\n\n"
        "2. PERMISSIONS & FILE MODES:\n"
        "   • \033[1;33mchmod +x <file>\033[0m : Grant executable rights (r-x) to recovery scripts.\n"
        "   • \033[1;33mchmod 644 <file>\033[0m: Lock down configuration files to secure read-only mode.\n\n"
        "3. NETWORKING & RECOVERY TOOLS:\n"
        "   • \033[1;33mip link set <dev> up\033[0m : Bring offline network adapter online.\n"
        "   • \033[1;33mping <gateway>\033[0m       : Verify ICMP reachability to core gateway nodes.\n"
        "   • \033[1;33mfind <path> -name \"<pat>\"\033[0m : Search filesystem trees for hidden tokens.\n"
        "================================================================================\n",
        perms="644",
        owner="root"
    )

    # Maya_04 — placed at /opt/backup/profiles/ for contextual discovery.
    # The player arrives here to restore .bashrc; Maya's note reveals the human
    # backstory: the previous operator had this exact same problem.
    maya_04_content = (
        "// ============================================================================\n"
        "// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]\n"
        "// TIMESTAMP: 2042-07-20 // FILE: /opt/backup/profiles/PREVIOUS_OPERATOR_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Javi kept writing about how the up and down arrow keys and the tab key \"saved\n"
        "my fingers from having to type more than I need to.\" He was always kind of lazy.\n\n"
        "But so am I. So I tried using them and kept getting errors — nothing was\n"
        "completing, nothing was recalling.\n\n"
        "Buried in one of his technical notes he explained that his shell profile had\n"
        "gotten wiped once. A file called '.bashrc' in his home folder — the one that\n"
        "configures how the terminal behaves — was missing. Without it, Tab and the\n"
        "arrow keys basically go dead. He said he had to restore it from a backup he\n"
        "kept at /opt/backup/profiles/.\n\n"
        "I patched mine from there. If you're reading this and your terminal feels\n"
        "broken: check /opt/backup/profiles/ first.\n\n"
        "— Maya\n"
        "// ============================================================================\n"
    )
    add_file("/opt/backup/profiles/PREVIOUS_OPERATOR_NOTE.txt", maya_04_content, perms="644", owner="root")

    # Milestone 2: /var/log/
    var_log_morgan_note = (
        "// ============================================================================\n"
        "// INCIDENT SCRATCHPAD // OSIRIS WORKSTATION // LOG TRIAGE\n"
        "// HOST: osiris-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 04:22:08 AM\n"
        "// FILE: /var/log/MORGAN_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Alice—\n\n"
        "auth.log has several hundred lines. You cannot read it straight through\n"
        "with 'cat' — it'll scroll off your screen before you find anything useful.\n\n"
        "There are two tools that let you work a large file without drowning in output.\n"
        "I left a breakdown of both in 'LOG_FORENSICS_GUIDE.txt' — read that first.\n\n"
        "Then come back here. The breach signature is buried in this log.\n"
        "Filter for it.\n\n"
        "If you want a scratchpad to track what you find:\n"
        "  touch ~/incident_notes.txt\n"
        "'~' is shorthand for your home directory — you can use it in any path.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/var/log/MORGAN_NOTE.txt", var_log_morgan_note, perms="644", owner="alice")

    how_to_read_logs_content = (
        "================================================================================\n"
        "          OSIRIS SECOPS FIELD MANUAL // HOW TO READ SYSTEM LOGS\n"
        "================================================================================\n"
        "Alice — when an attack happens, system daemons log events to /var/log/.\n"
        "Raw logs look dense, but every line follows a strict 4-part anatomy:\n\n"
        "  [ TIMESTAMP ]  [ HOST ]  [ DAEMON/SERVICE ]   [ EVENT MESSAGE ]\n"
        "  03:38:10       osiris    sshd[204]:           Invalid user operator from 192.168.1.105\n"
        "  └── When       └── Where └── Who logged it    └── What actually happened\n\n"
        "--------------------------------------------------------------------------------\n"
        "1. THE 4 COMMON INCIDENT DAEMONS:\n"
        "--------------------------------------------------------------------------------\n"
        "• 'sshd[PID]'   : Secure Shell logins (brute force attacks, unauthorized entry).\n"
        "• 'sudo'        : Administrator privilege escalation.\n"
        "• 'kernel'      : Core OS hardware & network link events.\n"
        "• 'systemd[1]'  : System service supervisor (terminated daemons).\n\n"
        "--------------------------------------------------------------------------------\n"
        "2. YOUR LOG INVESTIGATION TOOLKIT:\n"
        "--------------------------------------------------------------------------------\n"
        "• \033[1;33mcat <file>\033[0m            : Stream an entire log from start to finish.\n"
        "• \033[1;33mhead -n 5 <file>\033[0m      : Peek at the earliest events (e.g. system boot).\n"
        "• \033[1;33mtail -n 10 <file>\033[0m     : Focus on the latest events (e.g. recent attack activity).\n"
        "• \033[1;33mgrep -i \"pattern\" <file>\033[0m: Filter the noise to isolate specific keywords or alerts.\n\n"
        "--------------------------------------------------------------------------------\n"
        "3. TRIAGE VERIFICATION:\n"
        "--------------------------------------------------------------------------------\n"
        "Read 'REPAIR_COMMANDS.txt' for the list of triage verification commands to\n"
        "register confirmed security leads into your incident dossier.\n"
        "================================================================================\n"
    )
    add_file("/var/log/LOG_FORENSICS_GUIDE.txt", how_to_read_logs_content, perms="644", owner="root")

    grep_juice_content = (
        "================================================================================\n"
        "           SYSADMIN CHEAT SHEET // PRACTICAL 'grep' LOG FORENSICS\n"
        "================================================================================\n"
        "When triaging system breaches, raw logs contain hundreds of noisy events.\n"
        "Use 'grep' recipes to isolate critical incident keywords:\n\n"
        "1. ISOLATE ALERTS & ERRORS (Case-Insensitive):\n"
        "   • \033[1;33mgrep -i 'alert' /var/log/auth.log\033[0m\n"
        "   • \033[1;33mgrep -i 'alert' /var/log/syslog\033[0m\n"
        "   • \033[1;33mgrep -i 'error' /var/log/syslog\033[0m\n\n"
        "2. FILTER RUNAWAY PROCESSES & HARDWARE LINKS:\n"
        "   • \033[1;33mgrep -i 'miner' /var/log/auth.log\033[0m\n"
        "   • \033[1;33mgrep -i 'osiris0' /var/log/syslog\033[0m\n\n"
        "3. SHOW LINE NUMBERS & EXCLUDE NOISY DAEMONS:\n"
        "   • \033[1;33mgrep -n -i 'failed' /var/log/auth.log\033[0m   (Show line numbers)\n"
        "   • \033[1;33mgrep -v 'systemd' /var/log/syslog\033[0m      (Invert match: strip daemon noise)\n"
        "================================================================================\n"
    )
    add_file("/var/log/.grep_juice", grep_juice_content, perms="644", owner="root")

    repair_commands_content = (
        "================================================================================\n"
        "         SECOPS TRIAGE REGISTRATION // INCIDENT REPAIR COMMANDS\n"
        "================================================================================\n"
        "To verify breach leads and register findings into the incident dossier, run the\n"
        "matching triage command with the parameter extracted from the log files:\n\n"
        " [ALERT-0x01] INTRUDER PROCESS PID:\n"
        "   • Source Log : /var/log/auth.log\n"
        "   • Command    : \033[1;33mtriage_process <PID>\033[0m\n"
        "   • Example    : triage_process 4991\n\n"
        " [ALERT-0x02] TAMPERED SECTOR PATH:\n"
        "   • Source Log : /var/log/auth.log\n"
        "   • Command    : \033[1;33mtriage_sector <FILE_PATH>\033[0m\n"
        "   • Example    : triage_sector /opt/data/corrupted_agent.sh\n\n"
        " [ALERT-0x03] DEGRADED NETWORK INTERFACE:\n"
        "   • Source Log : /var/log/syslog\n"
        "   • Command    : \033[1;33mtriage_interface <DEVICE_NAME>\033[0m\n"
        "   • Example    : triage_interface eth1\n\n"
        " [ALERT-0x04] TERMINATED CLUSTER SERVICE:\n"
        "   • Source Log : /var/log/syslog\n"
        "   • Command    : \033[1;33mtriage_service <SERVICE_NAME>\033[0m\n"
        "   • Example    : triage_service cron.service\n"
        "================================================================================\n"
    )
    add_file("/var/log/REPAIR_COMMANDS.txt", repair_commands_content, perms="644", owner="root")

    auth_lines = [
        "# ==============================================================================",
        "# OSIRIS SYSTEM AUTHENTICATION LOG (/var/log/auth.log)",
        "# DIRECTIVE: Inspect security events using pattern filtration.",
        "# SYNTAX   : grep \"<PATTERN>\" <FILE>",
        "# EXAMPLE  : grep -i \"ALERT\" /var/log/auth.log",
        "# ==============================================================================",
    ]
    for i in range(1, 201):
        pid = 1000 + i
        auth_lines.append(f"[2042-10-11 03:{i//60:02d}:{i%60:02d}] osiris sshd[{pid}]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=10.0.42.{100 + (i%50)} user=root")
        if i == 45:
            auth_lines.append("[2042-10-11 03:00:45] osiris kernel: ALERT: Rogue miner deployed -> PID: 104 (sys_miner) in /tmp [ALERT-0x01]")
        elif i == 90:
            auth_lines.append("[2042-10-11 03:01:30] osiris kernel: ALERT: Recovery binary stripped -> /mnt/recovery/bin/recovery.sh (mode 0000) [ALERT-0x02]")
        elif i == 135:
            auth_lines.append("[2042-10-11 03:02:15] osiris kernel: ALERT: osiris0 link state degraded -> Device: osiris0 (state DOWN) [ALERT-0x03]")
    add_file("/var/log/auth.log", "\n".join(auth_lines) + "\n", perms="644", owner="root")

    syslog_lines = [
        "03:40:01 osiris systemd[1]: Starting System Logging Service...",
        "03:40:02 osiris kernel: [    0.000000] Linux version 5.15.0-osiris (gcc 11.2.0)",
        "03:40:02 osiris kernel: [    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz-5.15.0-osiris root=/dev/sda1 ro quiet",
        "03:40:03 osiris kernel: [    0.042100] x86/fpu: Supporting XSAVE feature 0x001: 'x87 floating point registers'",
        "03:40:03 osiris kernel: [    0.042105] x86/fpu: Supporting XSAVE feature 0x002: 'SSE registers'",
        "03:40:04 osiris systemd[1]: Mounted Huge Pages File System.",
        "03:40:04 osiris systemd[1]: Mounted POSIX Message Queue File System.",
        "03:40:05 osiris systemd[1]: Started Dispatch Password Requests to Console Directory Watch.",
        "03:40:06 osiris kernel: [    0.108420] e1000e: Intel(R) PRO/1000 Network Driver",
        "03:40:07 osiris kernel: [    0.108422] e1000e 0000:00:03.0 eth0: (PCI Express:2.5GT/s:Width x1) 52:54:00:12:34:56",
        "03:40:08 osiris systemd[1]: Reached target Local Encrypted Volumes.",
        "03:40:09 osiris systemd[1]: Listening on Syslog Socket.",
        "03:40:10 osiris systemd[1]: Reached target Network (Pre).",
        "03:40:12 osiris kernel: [ALERT-0x03] Interface osiris0 link state degraded: DOWN",
        "03:40:15 osiris systemd[1]: Starting Network Time Synchronization...",
        "03:40:18 osiris systemd-timesyncd[110]: Network configuration changed, trying to establish connection.",
        "03:40:22 osiris systemd[1]: Started Network Time Synchronization.",
        "03:40:30 osiris systemd[1]: Reached target System Time Set.",
        "03:40:45 osiris systemd[1]: Starting Rotate log files...",
        "03:40:50 osiris systemd[1]: logrotate.service: Deactivated successfully.",
        "03:41:00 osiris sys_miner[104]: CPU threshold exceeded: 98.2% allocation on core 0",
        "03:41:15 osiris kernel: [   12.401920] perf: interrupt took too long (2510 > 2500), lowering kernel.perf_event_max_sample_rate to 50000",
        "03:41:30 osiris systemd[1]: Starting Periodic ext4 Online Metadata Check...",
        "03:41:40 osiris systemd[1]: e4defrag.service: Deactivated successfully.",
        "03:42:00 osiris kernel: [   14.881200] CPU0: Core temperature above threshold, cpu clock throttled",
        "03:42:19 osiris systemd[1]: [ALERT-0x04] phoenix-sync.service: Main process exited, code=killed, status=9/KILL",
        "03:42:19 osiris systemd[1]: phoenix-sync.service: Failed with result 'signal'.",
        "03:42:25 osiris systemd[1]: phoenix-sync.service: Scheduled restart job, restart counter is at 1.",
        "03:42:30 osiris systemd[1]: Stopped Phoenix Synchronization Service.",
        "03:43:00 osiris kernel: [   18.109200] audit: type=1100 audit(1652341380.120:45): pid=104 uid=0 auid=1000 ses=1 msg='op=PAM:accounting grantors=pam_unix,pam_permit acct=\"root\" exe=\"/tmp/sys_miner\" hostname=? addr=? terminal=? res=success'",
        "03:43:15 osiris systemd[1]: Starting Daily Cleanup of Temporary Directories...",
        "03:43:20 osiris systemd[1]: systemd-tmpfiles-clean.service: Deactivated successfully."
    ]
    add_file("/var/log/syslog", "\n".join(syslog_lines) + "\n", perms="644", owner="root")
    add_file(
        "/var/log/system.log",
        "03:40:12 osiris kernel: eth0 link down\n03:42:19 osiris systemd: phoenix-sync terminated\n",
        perms="644",
        owner="root"
    )

    # Milestone 3 & 4: /mnt/recovery/
    mnt_recovery_morgan_note = (
        "// ============================================================================\n"
        "// INCIDENT SCRATCHPAD // OSIRIS WORKSTATION // RECOVERY MOUNT\n"
        "// HOST: osiris-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 05:10:44 AM\n"
        "// FILE: /mnt/recovery/MORGAN_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Alice—\n\n"
        "Before the quarantine locked me out, I mirrored our fallback tools and cluster\n"
        "authorization keys to this partition (/mnt/recovery).\n\n"
        "The problem: the automated unmount scramble threw directory branches all over\n"
        "the place. Hunting through every subfolder by hand with 'cd' and 'ls' will take\n"
        "hours we don't have.\n\n"
        "Use the recursive search utility 'find':\n"
        "  find <START_DIRECTORY> -name \"<SEARCH_PATTERN>\" -type f\n\n"
        "How it works:\n"
        "  • <START_DIRECTORY> : Where to begin searching (use '.' for here, or '/mnt/recovery').\n"
        "  • -name \"<PATTERN>\" : The filename you want. You can use wildcards like \"*.sh\" or \"*.key\".\n"
        "  • -type f           : Restricts the output to regular files (ignoring folders).\n\n"
        "We need two critical assets from this partition:\n"
        "1. Our subsystem recovery shell script (ends in .sh).\n"
        "2. The cryptographic PHOENIX access token (ends in .key).\n\n"
        "Locate them. If you need full option lists for the search utility, run 'man find'.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/mnt/recovery/MORGAN_NOTE.txt", mnt_recovery_morgan_note, perms="644", owner="alice")

    add_file(
        "/mnt/recovery/docs/RECOVERY_GUIDE.txt",
        "================================================================================\n"
        "                 SECOPS RECOVERY MANIFEST // PARTITION ADVISORY\n"
        "================================================================================\n"
        "1. PERMISSION RECOVERY & SEARCH INDEXING:\n"
        "   The intruder stripped execution permissions (mode 000) on scripts in bin/.\n"
        "   Restore execute permissions with: \033[1;33mchmod +x /mnt/recovery/bin/recovery.sh\033[0m\n"
        "   Then execute recovery.sh to rebuild the partition index and restore signal traps.\n\n"
        "2. PHOENIX CLUSTER AUTHENTICATION:\n"
        "   The cryptographic cluster key is preserved across this partition.\n"
        "   Use '\033[1;33mfind /mnt/recovery -name \"*.key\"\033[0m' to locate authentication tokens.\n"
        "================================================================================\n",
        perms="644",
        owner="root"
    )

    permissions_note = (
        "// ============================================================================\n"
        "// INCIDENT SCRATCHPAD // OSIRIS WORKSTATION // SECURITY LOCKDOWN\n"
        "// HOST: osiris-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 05:45:19 AM\n"
        "// FILE: /mnt/recovery/bin/MORGAN_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Alice—\n\n"
        "The containment protocol panicked and zeroed the permission mode bits on\n"
        "'recovery.sh'. Inspect it with 'ls -l' and you'll see:\n"
        "  ---------- 1 root root recovery.sh\n\n"
        "Linux will not execute any file unless its execute bit ('x') is explicitly\n"
        "flipped on. If you try to run it right now (/mnt/recovery/bin/recovery.sh), the shell will\n"
        "refuse with 'Permission denied'.\n\n"
        "You have to grant execution rights using 'chmod' (Change Mode):\n"
        "  chmod +x <FILE_PATH>\n\n"
        "Alternatively, you can set full standard permissions numerically:\n"
        "  chmod 755 <FILE_PATH>\n"
        "  (7 = Read/Write/Execute for Owner, 5 = Read/Execute for Group & Others)\n\n"
        "Once 'recovery.sh' has execute bits, run it with:\n"
        "  /mnt/recovery/bin/recovery.sh\n\n"
        "Executing this script restores our kernel signal traps. Once it completes, you'll\n"
        "get Ctrl+C (SIGINT) back so you can break out of hung processes.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/mnt/recovery/bin/MORGAN_NOTE.txt", permissions_note, perms="644", owner="alice")

    recovery_sh_content = (
        "#!/bin/bash\n"
        "# OSIRIS WORKSTATION // SUBSYSTEM RESTORATION SCRIPT\n"
        "# Re-links kernel signal handlers and line disciplines.\n\n"
        "echo \"[RECOVERY]: Probing line discipline vector registers...\"\n"
        "sleep 0.5\n"
        "echo \"[RECOVERY]: Restoring trap handler for SIGINT (Signal 2 / Ctrl+C)...\"\n"
        "sleep 0.5\n"
        "echo \"[SUCCESS]: Kernel signal table recalibrated. Interactive break handling online.\"\n"
    )
    add_file("/mnt/recovery/bin/recovery.sh", recovery_sh_content, perms="0000", owner="alice", group="alice")
    add_file("/mnt/recovery/bin/recovery.sh.default", recovery_sh_content, perms="0444", owner="root", group="root")

    add_file("/mnt/recovery/bin/osiris-net", "ELF 64-bit LSB executable [OSIRIS-NET v1.0]\n", perms="000", owner="root")
    add_file("/mnt/recovery/bin/phoenix_ctl", "ELF 64-bit LSB executable [PHOENIX-CTL v2.0]\n", perms="000", owner="root")
    add_file("/mnt/recovery/bin/recovery-tool", "ELF 64-bit LSB executable [RECOVERY-TOOL v2.1]\n", perms="000", owner="root")

    phoenix_key_content = (
        "-----BEGIN PHOENIX CLUSTER AUTHORIZATION TOKEN-----\n"
        "AUTH_TOKEN=PX-KEY-7701-ALPHA-SIGINT-TRAP-VECTOR-ENABLED\n"
        "CLUSTER_ID=OSIRIS-GRID-01\n"
        "ISSUED=2042-10-11T03:30:00Z\n"
        "SIGNATURE=d8e8fca2dc018b63b7e411b9802de922c091ad55\n"
        "-----END PHOENIX CLUSTER AUTHORIZATION TOKEN-----\n"
    )
    add_file("/mnt/recovery/keys/phoenix.key", phoenix_key_content, perms="644", owner="root")

    # /tmp/ Notes
    tmp_morgan_note = (
        "// ============================================================================\n"
        "// INCIDENT SCRATCHPAD // OSIRIS WORKSTATION // PROCESS REMEDIATION\n"
        "// HOST: osiris-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 06:15:33 AM\n"
        "// FILE: /tmp/MORGAN_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Alice—\n\n"
        "Our CPU thermal alarm is firing. The intruder dropped a persistent background\n"
        "miner into /tmp that is consuming nearly 100% of our compute cycles.\n\n"
        "First: get eyes on the process table.\n"
        "  ps aux\n"
        "'ps' lists every active process. The columns you need:\n"
        "  PID     — the process ID. This is your handle.\n"
        "  %CPU    — processor load. Your miner will be near 100%.\n"
        "  COMMAND — what the process actually is.\n\n"
        "Find the miner. Then kill it.\n\n"
        "Unix processes communicate through signals. 'kill' sends one.\n"
        "Signal 15 (SIGTERM) asks the process to stop — politely. It can ignore it.\n"
        "Signal 9 (SIGKILL) is forceful. It cannot be blocked or ignored.\n\n"
        "There's a stalled audit task to clear first:\n"
        "  kill 102\n\n"
        "The miner at PID 104 is hardened against Signal 15. Go straight to 9:\n"
        "  kill -9 104\n\n"
        "Kill the miner so our CPU cools down and frees up the network stack.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/tmp/MORGAN_NOTE.txt", tmp_morgan_note, perms="644", owner="alice")

    # Soft-Gated & Diegetic Tool Binaries
    add_file("/opt/phoenix/recovery/tree", "ELF 64-bit LSB executable\n", perms="755")
    add_file("/opt/phoenix/recovery/grep", "ELF 64-bit LSB executable\n", perms="755")
    add_file("/opt/phoenix/recovery/find", "ELF 64-bit LSB executable\n", perms="755")
    add_file("/opt/phoenix/recovery/recovery.sh", "#!/bin/bash\necho 'Restoring core nodes...'\n", perms="755")
    add_file("/opt/phoenix/phoenix_daemon", "ELF 64-bit LSB executable [PHOENIX-DAEMON v2.5]\n", perms="755")
    add_file(
        "/opt/phoenix/phoenix.conf",
        "# PHOENIX EMERGENCY RESTORATION DAEMON CONFIG\nSERVICE_ENABLED=1\nLISTEN_PORT=8080\nGATEWAY_IP=10.0.42.1\nRECOVERY_KEY=0x7F_PHOENIX_INIT_2042\n",
        perms="644"
    )
    add_file(
        "/opt/phoenix/config/phoenix.conf",
        "# PHOENIX EMERGENCY RESTORATION DAEMON CONFIG\nSERVICE_ENABLED=1\nLISTEN_PORT=8080\nGATEWAY_IP=10.0.42.1\nRECOVERY_KEY=0x7F_PHOENIX_INIT_2042\n",
        perms="644"
    )

    # Milestone 5: /etc/network/interfaces & MORGAN_NOTE.txt
    network_morgan_note = (
        "// ============================================================================\n"
        "// INCIDENT SCRATCHPAD // OSIRIS WORKSTATION // NETWORK RECOVERY\n"
        "// HOST: osiris-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 06:50:02 AM\n"
        "// FILE: /etc/network/MORGAN_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Alice—\n\n"
        "The miner is dead and CPU load is back to normal, but the machine is still\n"
        "isolated. The attack toggled our primary network adapter off at the driver level.\n\n"
        "Start by reading the hardware definitions:\n"
        "  cat interfaces\n"
        "You'll find our interface is named 'osiris0' and our gateway is at 10.0.42.1.\n\n"
        "Then check the current link state:\n"
        "  ip addr\n"
        "Look for 'osiris0' in the output. If it says 'state DOWN', the interface is\n"
        "offline at the hardware level. That's your problem.\n\n"
        "To bring it back online:\n"
        "  ip link set osiris0 up\n"
        "Reading left to right: 'link' is the physical network layer. 'set' changes\n"
        "its state. 'up' is the target state — online.\n\n"
        "Once it's up, confirm packets can reach the gateway:\n"
        "  ping -c 4 10.0.42.1\n"
        "The '-c 4' flag sends exactly 4 test packets and stops.\n"
        "If you get replies, the uplink is live.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/etc/network/MORGAN_NOTE.txt", network_morgan_note, perms="644", owner="alice")

    interfaces_content = (
        "# OSIRIS WORKSTATION NETWORK INTERFACE CONFIGURATION\n"
        "# Local loopback interface\n"
        "auto lo\n"
        "iface lo inet loopback\n\n"
        "# Primary Ethernet uplink (Degraded by automated containment)\n"
        "# Hardware MAC: 52:54:00:12:34:56\n"
        "auto osiris0\n"
        "iface osiris0 inet static\n"
        "    address 10.0.42.15/24\n"
        "    gateway 10.0.42.1\n"
        "    dns-nameservers 10.0.42.1\n"
    )
    add_file("/etc/network/interfaces", interfaces_content, perms="644", owner="root")

    # Milestone 6: /etc/phoenix/ & Fallback Backups
    phoenix_morgan_note = (
        "// ============================================================================\n"
        "// INCIDENT SCRATCHPAD // OSIRIS WORKSTATION // PHOENIX CLUSTER DAEMON\n"
        "// HOST: osiris-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 07:35:14 AM\n"
        "// FILE: /etc/phoenix/MORGAN_NOTE.txt\n"
        "// ============================================================================\n\n"
        "Alice—\n\n"
        "This is it. The gateway is reachable and the workstation is stable.\n"
        "The final step is bringing the PHOENIX cluster restoration daemon online.\n\n"
        "The daemon reads its configuration from 'phoenix.conf', but it's currently\n"
        "missing its authorization token.\n\n"
        "CRITICAL SYNTAX WARNING:\n"
        "You need to append the key you found earlier (/mnt/recovery/keys/phoenix.key)\n"
        "to the bottom of 'phoenix.conf'.\n"
        "  • A single '>' OVERWRITES the file, erasing all the listener settings.\n"
        "  • A double '>>' APPENDS the data cleanly to the end of the file.\n\n"
        "Syntax Template:\n"
        "  cat <SOURCE_KEY_FILE> >> <DESTINATION_CONFIG_FILE>\n\n"
        "(If you accidentally overwrite the file, do not panic: I left a pristine backup\n"
        "template at /etc/phoenix/phoenix.conf.default).\n\n"
        "After appending the key:\n"
        "1. Secure the configuration permissions. The daemon will refuse to start if the\n"
        "   file is world-writable. Set it to read-only for others:\n"
        "   chmod 644 /etc/phoenix/phoenix.conf\n\n"
        "2. Launch the restoration daemon:\n"
        "   phoenix_daemon start\n\n"
        "3. Verify that the daemon socket is actively listening on port 8080.\n"
        "   The pipe operator '|' feeds the output of one command into the next as input.\n"
        "   Here, 'ss -tulpn' lists all open network sockets; '| grep 8080' filters\n"
        "   that list down to just port 8080:\n"
        "   ss -tulpn | grep 8080\n\n"
        "You brought this terminal back from zero, Alice. Bring us home.\n\n"
        "— Morgan\n"
        "// ============================================================================\n"
    )
    add_file("/etc/phoenix/MORGAN_NOTE.txt", phoenix_morgan_note, perms="644", owner="root")

    initial_conf = (
        "# PHOENIX EMERGENCY CLUSTER RESTORATION DAEMON CONFIG\n"
        "LISTEN_ADDR=127.0.0.1\n"
        "LISTEN_PORT=8080\n"
        "GATEWAY_TARGET=10.0.42.1\n"
        "LOG_LEVEL=VERBOSE\n"
        "FAILOVER_MODE=AUTONOMOUS\n"
        "# --- APPEND BEARER TOKEN BELOW ---\n"
    )
    add_file("/etc/phoenix/phoenix.conf", initial_conf, perms="0644", owner="alice", group="alice")
    add_file("/etc/phoenix/phoenix.conf.default", initial_conf, perms="0444", owner="root", group="root")
    add_file("/opt/backup/phoenix.conf", initial_conf, perms="644", owner="root")

    # =========================================================================
    # Maya Notes — Personal logs left by the previous operator
    # Hidden inside /home/alice/.maya_notes/ (discovered via 'ls -a').
    # Maya_04 is placed at /opt/backup/profiles/ for contextual discovery
    # (see the PREVIOUS_OPERATOR_NOTE.txt entry above, near that section).
    # Maya_10 (goodbye letter) and Maya_05–09 are reserved for future drafting.
    # =========================================================================

    maya_00_content = (
        "// ============================================================================\n"
        "// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]\n"
        "// TIMESTAMP: 2042-07-14 // FILE: /home/alice/.maya_notes/Maya_00.txt\n"
        "// ============================================================================\n\n"
        "God this sucks. They threw me on this thing when Javi kicked the bucket, just\n"
        "because I knew how to turn it on. Javi never got around to training anybody\n"
        "how to do this.\n\n"
        "Anyway I found a sticky note taped to the terminal that says if I type 'cd'\n"
        "followed by the name of a directory — which is apparently a different \"room\"\n"
        "in the system — I can move there. I've been trying to hop around but I keep\n"
        "getting errors saying things like \"no such file or directory.\"\n\n"
        "At least I figured out that typing:\n"
        "  cd ~\n"
        "...always drops me back in my home folder. I'll take it.\n\n"
        "— Maya\n"
        "// ============================================================================\n"
    )
    add_file("/home/alice/.maya_notes/Maya_00.txt", maya_00_content, perms="644", owner="alice", group="alice")

    maya_01_content = (
        "// ============================================================================\n"
        "// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]\n"
        "// TIMESTAMP: 2042-07-15 // FILE: /home/alice/.maya_notes/Maya_01.txt\n"
        "// ============================================================================\n\n"
        "Ok I figured out why cd kept failing! You have to type the directory name\n"
        "EXACTLY as it appears — weird forward-slashes and dots included. The system\n"
        "is very literal.\n\n"
        "Oh yeah — I also found out that if I type 'ls -a', a whole extra bunch of\n"
        "files and folders appear. Javi apparently stashed some of his more... personal\n"
        "notes in those dot-folders. I read one. I was not interested in learning about\n"
        "his weird rash.\n\n"
        "— Maya\n"
        "// ============================================================================\n"
    )
    add_file("/home/alice/.maya_notes/Maya_01.txt", maya_01_content, perms="644", owner="alice", group="alice")

    maya_02_content = (
        "// ============================================================================\n"
        "// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]\n"
        "// TIMESTAMP: 2042-07-17 // FILE: /home/alice/.maya_notes/Maya_02.txt\n"
        "// ============================================================================\n\n"
        "Oh yeah! Just made my own secret file!\n\n"
        "Turns out when Javi wrote \"touching\" in one of his notes, he was literally\n"
        "talking about the command that creates a new empty file:\n"
        "  touch <filename>\n\n"
        "I definitely thought he meant something else. Anyway. I'm going to go back\n"
        "and leave some notes for myself in my home folder so I don't forget how to\n"
        "move around.\n\n"
        "— Maya\n"
        "// ============================================================================\n"
    )
    add_file("/home/alice/.maya_notes/Maya_02.txt", maya_02_content, perms="644", owner="alice", group="alice")

    # Maya_03 is one level deeper — player must 'cd archive' to find it,
    # then needs 'cd ..' to get back out. The note teaches the skill required
    # to leave the room it's in. Subdir name TBD; using 'archive' as placeholder.
    maya_03_content = (
        "// ============================================================================\n"
        "// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]\n"
        "// TIMESTAMP: 2042-07-18 // FILE: /home/alice/.maya_notes/archive/Maya_03.txt\n"
        "// ============================================================================\n\n"
        "Ok I'm starting to get lost. I went four directories deep trying to find where\n"
        "Javi kept his tool notes and had no idea how to backtrack.\n\n"
        "Luckily I mistyped something and discovered that 'cd ..' (two dots, no space)\n"
        "goes up one level to the parent folder. Accidentally stumbling into solutions\n"
        "is basically my whole strategy at this point.\n\n"
        "— Maya\n"
        "// ============================================================================\n"
    )
    add_file("/home/alice/.maya_notes/archive/Maya_03.txt", maya_03_content, perms="644", owner="alice", group="alice")

    return root
