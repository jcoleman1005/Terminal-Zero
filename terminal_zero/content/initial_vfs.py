from typing import Dict, Optional
from terminal_zero.core.vfs import VFSNode
from terminal_zero.content.narrative import get_todo_content, get_incident_dossier


def build_default_vfs(flags: Optional[Dict[str, bool]] = None) -> VFSNode:
    if flags is None:
        flags = {}
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

    # Standard POSIX & FHS Structure across all sectors
    dirs = [
        "bin", "usr/bin", "usr/share/doc", "home/alice", "home/alice/diagnostics", "var/log", "tmp", 
        "mnt/recovery/bin", "mnt/recovery/keys", "mnt/recovery/docs",
        "opt/backup", "opt/backup/profiles", "etc/network", "etc/phoenix",
        "opt/phoenix", "opt/phoenix/recovery", "opt/phoenix/config"
    ]
    for d in dirs:
        add_dir("/" + d)

    # Soft-Gate /opt/phoenix via Permissions (0700 until LOGS_AUDITED or RECOVERY_LOCATED is set)
    phoenix_perms = "755" if (flags.get("LOGS_AUDITED", False) or flags.get("RECOVERY_LOCATED", False)) else "700"
    add_dir("/opt/phoenix", perms=phoenix_perms, owner="root")

    # Standard Binaries in /bin and /usr/bin
    for b in [
        "cat", "cd", "echo", "exit", "ls", "pwd", "sync", "decrypt", "apollo-diagnostics",
        "chmod", "man", "ps", "kill", "ip", "ss", "ping", "head", "tail", "grep", "find",
        "repair_buffer", "phoenix_ctl", "phoenix_daemon", "apollo-net", "tree",
        "note", "feedback", "taskctl", "todo", "tasks",
        "triage_process", "triage_sector", "triage_interface", "triage_service"
    ]:
        add_file(f"/bin/{b}", "ELF 64-bit LSB executable", perms="755")
        add_file(f"/usr/bin/{b}", "ELF 64-bit LSB executable", perms="755")

    # Milestone 0: /home/alice & /home/alice/diagnostics
    add_file(
        "/home/alice/README.txt",
        "================================================================================\n"
        "          APOLLO WORKSTATION // EMERGENCY OPERATOR SURVIVAL CARD\n"
        "================================================================================\n"
        "BASIC NAVIGATION ACTIONS:\n"
        "  • ls             : Look around (list visible files and folders).\n"
        "  • cd <folder>    : Move into a folder (e.g. 'cd diagnostics' or 'cd ..' to go back).\n"
        "  • cat <file>     : Open and read a file's contents (e.g. 'cat README.txt').\n"
        "  • pwd            : Check what folder you are currently standing in.\n"
        "  • decrypt        : Ask APOLLO AI to diagnose your last error in plain language.\n"
        "  • sync           : Save workstation progress to persistent disk.\n\n"
        "OPERATOR ADVISORY:\n"
        "Explore your environment with 'ls' and 'cd'. Inspect logs with 'cat' to diagnose\n"
        "faults and discover emergency recovery utilities.\n"
        "================================================================================\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/diagnostics/BOOT_FAIL.log",
        "[KERNEL ALERT] Apollo Workstation Core Subsystem Degraded (Boot ID: 0x42-INIT).\n"
        "[SUBSYSTEM FAULT] Command History Memory is offline. Interactive command recall (UP/DOWN arrow keys) disabled.\n"
        "[ACTION REQUIRED] Run 'repair_buffer' to restore terminal memory registers.\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/diagnostics/INCIDENT_REPORT.log",
        get_incident_dossier({}),
        perms="644",
        owner="alice"
    )

    # Milestone 1: /opt/backup/profiles & /home/alice
    add_file(
        "/home/alice/.note.txt",
        "// STICKY NOTE TAPED TO MONITOR:\n"
        "Alice — your shell profile (.bashrc) got deleted during the incident.\n"
        "I stored a backup template in /opt/backup/profiles/.\n"
        "Head over there ('cd /opt/backup/profiles') and read my note to get your shortcuts back!\n"
        "— Morgan\n",
        perms="644",
        owner="alice"
    )
    morgan_note = (
        "// MORGAN [03:42 AM] — INCIDENT OVERRIDE\n"
        "Alice — during the breach, your shell profile was wiped out, which broke your\n"
        "command search paths and shortcuts.\n\n"
        "I left a clean backup template right here ('alice.bashrc').\n\n"
        "To clone it back into your home directory, write it over with '>':\n"
        "  cat alice.bashrc > /home/alice/.bashrc\n\n"
        "(Note: '~' is shorthand for your home folder, so 'cat alice.bashrc > ~/.bashrc' also works!)\n\n"
        "Once restored, try typing 'll' right here.\n"
        "The 'll' shortcut not only displays full file details (permissions, owner, size),\n"
        "it also reveals secret hidden files and directories starting with a dot (.)!\n"
    )
    add_file("/opt/backup/profiles/NOTE_FROM_MORGAN.txt", morgan_note, perms="644", owner="root")
    
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
        "You can restore executable permissions on any file using 'chmod +x <filename>'.\n"
        "================================================================================\n"
    )
    add_file("/opt/backup/profiles/.HOW_TO_READ_LL.txt", ll_guide_content, perms="644", owner="root")
    
    add_file(
        "/opt/backup/profiles/alice.bashrc",
        "# ALICE SHELL PROFILE TEMPLATE\n"
        "# Clone to your home folder with: cat alice.bashrc > /home/alice/.bashrc\n"
        "export PATH=/bin:/usr/bin:/mnt/recovery/bin\n"
        "alias ll='ls -la'\n",
        perms="644",
        owner="root"
    )
    add_file(
        "/home/alice/.bashrc",
        "",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/.bash_history",
        "ps aux | grep miner\nkill -9 104\nip link set apollo0 up\nping -c 4 10.0.42.1\nchmod +x /mnt/recovery/bin/apollo-net\n/opt/phoenix/phoenix_daemon --sync\n",
        perms="644",
        owner="alice"
    )
    add_file(
        "/home/alice/TODO.txt",
        get_todo_content(flags),
        perms="644",
        owner="alice"
    )
    add_file(
        "/usr/share/doc/mapping_tool.txt",
        "UTILITY RECOVERY NOTE:\nVisual hierarchy utility 'tree' preserved under /opt/phoenix/recovery/tree\n",
        perms="644",
        owner="root"
    )
    add_file(
        "/usr/share/doc/sysadmin_notes.txt",
        "SYSADMIN LOG - RECOVERY PROTOCOLS:\n1. Use 'grep' to search error streams.\n2. Ensure recovery binaries have execution permissions via 'chmod'.\n3. Bring interfaces up using 'ip link set <dev> up'.\n",
        perms="644",
        owner="root"
    )

    # Milestone 2: /var/log/ with teaching manuals and color-coded incident alert tags
    how_to_read_logs_content = (
        "================================================================================\n"
        "          APOLLO SECOPS FIELD MANUAL // HOW TO READ SYSTEM LOGS\n"
        "================================================================================\n"
        "Alice — when an attack happens, system daemons log events to /var/log/.\n"
        "Raw logs look dense, but every line follows a strict 4-part anatomy:\n\n"
        "  [ TIMESTAMP ]  [ HOST ]  [ DAEMON/SERVICE ]   [ EVENT MESSAGE ]\n"
        "  03:38:10       apollo    sshd[204]:           Invalid user operator from 192.168.1.105\n"
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
        "• cat <file>            : Stream an entire log from start to finish.\n"
        "• head -n 5 <file>      : Peek at the earliest events (e.g. system boot).\n"
        "• tail -n 10 <file>     : Focus on the latest events (e.g. recent attack activity).\n"
        "• grep -i \"pattern\" <file>: Filter the noise to isolate specific keywords or alerts.\n\n"
        "--------------------------------------------------------------------------------\n"
        "3. TRIAGE VERIFICATION:\n"
        "--------------------------------------------------------------------------------\n"
        "Read 'REPAIR_COMMANDS.txt' for the list of triage verification commands to\n"
        "register confirmed security leads into your incident dossier.\n"
        "================================================================================\n"
    )
    add_file("/var/log/HOW_TO_READ_LOGS.txt", how_to_read_logs_content, perms="644", owner="root")

    repair_commands_content = (
        "================================================================================\n"
        "         SECOPS TRIAGE REGISTRATION // INCIDENT REPAIR COMMANDS\n"
        "================================================================================\n"
        "To verify breach leads and register findings into the incident dossier, run the\n"
        "matching triage command with the parameter extracted from the log files:\n\n"
        " \033[1;31m[ALERT-0x01]\033[0m INTRUDER PROCESS PID:\n"
        "   • Source Log : /var/log/auth.log\n"
        "   • Command    : \033[1;31mtriage_process <PID>\033[0m\n"
        "   • Example    : triage_process 999\n\n"
        " \033[1;33m[ALERT-0x02]\033[0m TAMPERED SECTOR PATH:\n"
        "   • Source Log : /var/log/auth.log\n"
        "   • Command    : \033[1;33mtriage_sector <FILE_PATH>\033[0m\n"
        "   • Example    : triage_sector /mnt/recovery/bin/recovery.sh\n\n"
        " \033[1;36m[ALERT-0x03]\033[0m DEGRADED NETWORK INTERFACE:\n"
        "   • Source Log : /var/log/syslog\n"
        "   • Command    : \033[1;36mtriage_interface <DEVICE_NAME>\033[0m\n"
        "   • Example    : triage_interface eth0\n\n"
        " \033[1;35m[ALERT-0x04]\033[0m TERMINATED CLUSTER SERVICE:\n"
        "   • Source Log : /var/log/syslog\n"
        "   • Command    : \033[1;35mtriage_service <SERVICE_NAME>\033[0m\n"
        "   • Example    : triage_service nginx.service\n"
        "================================================================================\n"
    )
    add_file("/var/log/REPAIR_COMMANDS.txt", repair_commands_content, perms="644", owner="root")

    auth_content = (
        "[INFO]: System boot complete.\n"
        " [WARN]: Normal PAM session opened for user root.\n"
        " [WARN]: Normal PAM session closed for user root.\n"
        " [WARN]: Normal PAM session opened for user alice.\n"
        " [WARN]: Normal PAM session closed for user alice.\n"
        "03:38:10 apollo sshd[204]: Invalid user operator from 192.168.1.105 port 44218\n"
        "03:38:12 apollo sshd[204]: Failed password for invalid user operator from 192.168.1.105 port 44218 ssh2\n"
        "03:39:01 apollo sshd[208]: Accepted password for alice from 127.0.0.1 port 51220 ssh2\n"
        "03:39:45 apollo sudo: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/systemctl status\n"
        "\033[1;31m[ALERT-0x01]\033[0m: Unauthorized access detected. Rogue miner deployed to /tmp/sys_miner (PID 104).\n"
        "\033[1;33m[ALERT-0x02]\033[0m: Recovery binary stripped in /mnt/recovery/bin/recovery.sh.\n"
    )
    add_file("/var/log/auth.log", auth_content, perms="640", owner="root")
    add_file(
        "/var/log/syslog",
        "03:40:01 apollo systemd[1]: Starting System Logging Service...\n"
        "03:40:05 apollo kernel: [    0.000000] Linux version 5.15.0-apollo (gcc 11.2.0)\n"
        "03:40:12 apollo kernel: \033[1;36m[ALERT-0x03]\033[0m Interface apollo0 link state degraded: DOWN\n"
        "03:41:00 apollo sys_miner[104]: CPU threshold exceeded: 98.2% allocation on core 0\n"
        "03:42:19 apollo systemd[1]: \033[1;35m[ALERT-0x04]\033[0m phoenix-sync.service: Main process exited, code=killed, status=9/KILL\n"
        "03:42:19 apollo systemd[1]: phoenix-sync.service: Failed with result 'signal'.\n",
        perms="644"
    )
    add_file(
        "/var/log/system.log",
        "03:40:12 apollo kernel: eth0 link down\n03:42:19 apollo systemd: phoenix-sync terminated\n",
        perms="644"
    )

    # Milestone 3 & 4: /mnt/recovery/
    add_file(
        "/mnt/recovery/docs/RECOVERY_NOTES.txt",
        "================================================================================\n"
        "                 SECOPS RECOVERY MANIFEST // PARTITION ADVISORY\n"
        "================================================================================\n"
        "1. PERMISSION RECOVERY:\n"
        "   The intruder stripped execution permissions (mode 000) on scripts in bin/.\n"
        "   Restore execute permissions with: chmod +x /mnt/recovery/bin/recovery.sh\n"
        "   Then execute recovery.sh to link kernel signal handling (unlocking Ctrl+C).\n\n"
        "2. PHOENIX CLUSTER AUTHENTICATION:\n"
        "   The cryptographic cluster key is preserved under:\n"
        "   /mnt/recovery/keys/phoenix.key\n"
        "   This key must be appended to the PHOENIX daemon configuration in /etc/phoenix/\n"
        "   to restore the restoration gateway.\n"
        "================================================================================\n",
        perms="644",
        owner="root"
    )
    add_file(
        "/mnt/recovery/bin/recovery.sh",
        "#!/bin/bash\necho '[KERNEL]: Restoring signal trap vector...'\necho 'SIGINT handler online.'\n",
        perms="000",
        owner="root"
    )
    add_file("/mnt/recovery/bin/apollo-net", "ELF 64-bit LSB executable [APOLLO-NET v1.0]", perms="000", owner="root")
    add_file("/mnt/recovery/bin/phoenix_ctl", "ELF 64-bit LSB executable [PHOENIX-CTL v2.0]", perms="000", owner="root")
    add_file("/mnt/recovery/bin/recovery-tool", "ELF 64-bit LSB executable [RECOVERY-TOOL v2.1]", perms="000", owner="root")
    add_file("/mnt/recovery/keys/phoenix.key", "PX-KEY-7701-ALPHA\n", perms="600", owner="root")

    # Soft-Gated & Diegetic Tool Binaries
    add_file("/opt/phoenix/recovery/tree", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/grep", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/find", "ELF 64-bit LSB executable", perms="755")
    add_file("/opt/phoenix/recovery/recovery.sh", "#!/bin/bash\necho 'Restoring core nodes...'", perms="755")
    add_file("/opt/phoenix/phoenix_daemon", "ELF 64-bit LSB executable [PHOENIX-DAEMON v2.5]", perms="755")
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

    # Milestone 6: /etc/network/interfaces & NOTE.txt
    add_file(
        "/etc/network/interfaces",
        "auto lo\niface lo inet loopback\n\nauto apollo0\niface apollo0 inet static\n  address 10.0.42.15/24\n  gateway 10.0.42.1\n",
        perms="644",
        owner="root"
    )
    add_file(
        "/etc/network/NOTE.txt",
        "NETWORK CONFIGURATION NOTE:\nPrimary interface knocked offline following intrusion attempt.\nUse 'ip link' to inspect interfaces and bring adapter 'apollo0' back online.\nTest reachability with 'ping 10.0.42.1'.\n",
        perms="644",
        owner="root"
    )

    # Milestone 7: /etc/phoenix/ & Fallback Backups
    initial_conf = "[PHOENIX_DAEMON_CONFIG]\nLISTEN_PORT=8080\nGATEWAY=10.0.42.1\n"
    add_file("/etc/phoenix/phoenix.conf", initial_conf, perms="600", owner="root")
    add_file("/etc/phoenix/phoenix.conf.default", initial_conf, perms="644", owner="root")
    add_file("/opt/backup/phoenix.conf", initial_conf, perms="644", owner="root")
    add_file(
        "/etc/phoenix/NOTE.txt",
        "[MORGAN'S FINAL FIELD NOTE]\n"
        "Alice — to recover the cluster supervisor, the PHOENIX daemon requires two prerequisites:\n"
        "  1. Append our cryptographic recovery key (/mnt/recovery/keys/phoenix.key) to /etc/phoenix/phoenix.conf\n"
        "  2. Secure configuration permissions to read-only mode (chmod 644 /etc/phoenix/phoenix.conf)\n"
        "Once secured, launch 'phoenix_daemon start' to restore the gateway!\n",
        perms="644",
        owner="root"
    )

    return root
