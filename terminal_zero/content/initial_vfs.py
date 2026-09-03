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
        "note", "feedback", "taskctl", "todo", "tasks", "manuals", "docs", "fieldguide",
        "triage_process", "triage_sector", "triage_interface", "triage_service"
    ]:
        add_file(f"/bin/{b}", "ELF 64-bit LSB executable\n", perms="755")
        add_file(f"/usr/bin/{b}", "ELF 64-bit LSB executable\n", perms="755")

    # Milestone 0: /home/alice & /home/alice/diagnostics
    add_file(
        "/home/alice/README.txt",
        "================================================================================\n"
        "          APOLLO WORKSTATION // EMERGENCY OPERATOR SURVIVAL CARD\n"
        "================================================================================\n"
        "SECONDARY NAVIGATION & DIAGNOSTIC UTILITIES:\n"
        "  • cd <folder>    : Move into a folder (e.g. 'cd diagnostics' or 'cd ..' to go back).\n"
        "  • pwd            : Print the current directory path you are standing in.\n"
        "  • decrypt        : Ask APOLLO AI to diagnose your last error in plain language.\n"
        "  • manuals        : Index all recovered field manuals, cheat sheets, and guides.\n"
        "  • sync           : Save workstation recovery progress to persistent storage.\n\n"
        "OPERATOR ADVISORY:\n"
        "Explore directory branches with 'cd' and 'ls'. Inspect logs and field notes with\n"
        "'cat' to uncover incident clues and discover system restoration tools.\n"
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

    # /etc/os-release (System Information)
    add_file(
        "/etc/os-release",
        "NAME=\"Apollo Workstation OS\"\n"
        "VERSION=\"2.4 LTS (Recovery Build 0x42)\"\n"
        "ID=apollo\n"
        "ID_LIKE=debian\n"
        "PRETTY_NAME=\"Apollo OS 2.4 (x86_64-apollo-linux-gnu)\"\n"
        "HOME_URL=\"https://apollo.internal/workstation\"\n",
        perms="644",
        owner="root"
    )

    # Milestone 1: /opt/backup/profiles & /home/alice
    add_file(
        "/home/alice/.note.txt",
        "// STICKY NOTE TAPED TO MONITOR:\n"
        "Alice — during the breach, strange logs and alerts were generated in /var/log/.\n"
        "Use 'grep' to filter log noise and unmask the attacker's traces.\n"
        "Emergency recovery scripts are locked down under /mnt/recovery/bin/.\n"
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
        "it also reveals secret hidden files and directories starting with a dot (.)!\n\n"
        "[PRO TIP]: Restoring ~/.bashrc re-enables [TAB] autocompletion!\n"
        "Type 'cd /o' and press [TAB] anywhere to autocomplete long paths instantly.\n"
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
        "uptime\nfree -h\ndf -h\nls -la /var/log\nsystemctl status\ncat /etc/os-release\n",
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
        "================================================================================\n"
        "             SYSADMIN PROTOCOLS // PROCESSES, MODES & NETWORKING\n"
        "================================================================================\n"
        "1. PROCESS SUPERVISION & SIGNALS:\n"
        "   • 'ps aux'         : Inspect the active Process Status table (PID, %CPU, COMMAND).\n"
        "   • 'kill -9 <PID>'  : Dispatch forceful SIGKILL signal to terminate runaway tasks.\n\n"
        "2. PERMISSIONS & FILE MODES:\n"
        "   • 'chmod +x <file>': Grant executable rights (r-x) to recovery scripts.\n"
        "   • 'chmod 644 <file>': Lock down configuration files to read-only security.\n\n"
        "3. NETWORKING & RECOVERY TOOLS:\n"
        "   • 'ip link set <dev> up'      : Bring offline network interfaces to UP state.\n"
        "   • 'ping <gateway>'            : Verify ICMP reachability to core gateway nodes.\n"
        "   • 'find <path> -name \"<pat>\"'  : Scan partition trees for hidden keys.\n"
        "================================================================================\n",
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

    grep_juice_content = (
        "================================================================================\n"
        "           SYSADMIN CHEAT SHEET // PRACTICAL 'grep' LOG FORENSICS\n"
        "================================================================================\n"
        "When triaging system breaches, raw logs contain hundreds of noisy events.\n"
        "Use 'grep' recipes to isolate critical incident keywords:\n\n"
        "1. ISOLATE ALERTS & ERRORS (Case-Insensitive):\n"
        "   • grep -i 'alert' /var/log/auth.log\n"
        "   • grep -i 'alert' /var/log/syslog\n"
        "   • grep -i 'error' /var/log/syslog\n\n"
        "2. FILTER RUNAWAY PROCESSES & HARDWARE LINKS:\n"
        "   • grep -i 'miner' /var/log/auth.log\n"
        "   • grep -i 'apollo0' /var/log/syslog\n\n"
        "3. SHOW LINE NUMBERS & EXCLUDE NOISY DAEMONS:\n"
        "   • grep -n -i 'failed' /var/log/auth.log   (Show line numbers)\n"
        "   • grep -v 'systemd' /var/log/syslog      (Invert match: strip daemon noise)\n"
        "================================================================================\n"
    )
    add_file("/var/log/.grep_juice", grep_juice_content, perms="644", owner="root")

    repair_commands_content = (
        "================================================================================\n"
        "         SECOPS TRIAGE REGISTRATION // INCIDENT REPAIR COMMANDS\n"
        "================================================================================\n"
        "To verify breach leads and register findings into the incident dossier, run the\n"
        "matching triage command with the parameter extracted from the log files:\n\n"
        " \033[1;31m[ALERT-0x01]\033[0m INTRUDER PROCESS PID:\n"
        "   • Source Log : /var/log/auth.log\n"
        "   • Command    : \033[1;31mtriage_process <PID>\033[0m\n"
        "   • Example    : triage_process 4991\n\n"
        " \033[1;33m[ALERT-0x02]\033[0m TAMPERED SECTOR PATH:\n"
        "   • Source Log : /var/log/auth.log\n"
        "   • Command    : \033[1;33mtriage_sector <FILE_PATH>\033[0m\n"
        "   • Example    : triage_sector /opt/data/corrupted_agent.sh\n\n"
        " \033[1;36m[ALERT-0x03]\033[0m DEGRADED NETWORK INTERFACE:\n"
        "   • Source Log : /var/log/syslog\n"
        "   • Command    : \033[1;36mtriage_interface <DEVICE_NAME>\033[0m\n"
        "   • Example    : triage_interface eth1\n\n"
        " \033[1;35m[ALERT-0x04]\033[0m TERMINATED CLUSTER SERVICE:\n"
        "   • Source Log : /var/log/syslog\n"
        "   • Command    : \033[1;35mtriage_service <SERVICE_NAME>\033[0m\n"
        "   • Example    : triage_service cron.service\n"
        "================================================================================\n"
    )
    add_file("/var/log/REPAIR_COMMANDS.txt", repair_commands_content, perms="644", owner="root")

    auth_lines = [
        "[INFO]: System boot complete (Linux 5.15.0-apollo).",
        "May 12 03:28:01 apollo systemd[1]: Starting System Logging Service...",
        "May 12 03:28:05 apollo kernel: Initializing cgroup subsys cpuset",
        "May 12 03:28:10 apollo systemd-logind[102]: Watching system buttons on /dev/input/event0",
        "May 12 03:29:14 apollo CRON[180]: pam_unix(cron:session): session opened for user root by (uid=0)",
        "May 12 03:29:15 apollo CRON[180]: pam_unix(cron:session): session closed for user root",
        "May 12 03:30:01 apollo systemd-logind[102]: New session c1 of user root.",
        "May 12 03:30:02 apollo pam_unix(sshd:session): session opened for user systemd",
        "May 12 03:31:00 apollo pam_unix(sshd:session): session closed for user systemd",
        "May 12 03:32:15 apollo CRON[185]: pam_unix(cron:session): session opened for user alice by (uid=1000)",
        "May 12 03:32:20 apollo CRON[185]: pam_unix(cron:session): session closed for user alice",
        "May 12 03:33:01 apollo systemd[1]: Created slice User Slice of UID 1000.",
        "May 12 03:34:10 apollo sshd[190]: Server listening on 0.0.0.0 port 22.",
        "May 12 03:35:00 apollo systemd[1]: Starting Daily apt download activities...",
        "May 12 03:35:12 apollo systemd[1]: apt-daily.service: Deactivated successfully.",
        "May 12 03:36:01 apollo CRON[195]: pam_unix(cron:session): session opened for user root",
        "May 12 03:36:05 apollo CRON[195]: pam_unix(cron:session): session closed for user root",
        "May 12 03:37:00 apollo pam_unix(sudo:session): session opened for user root by alice(uid=1000)",
        "May 12 03:37:05 apollo pam_unix(sudo:session): session closed for user root",
        "May 12 03:38:10 apollo sshd[204]: Invalid user operator from 192.168.1.105 port 44218",
        "May 12 03:38:12 apollo sshd[204]: Failed password for invalid user operator from 192.168.1.105 port 44218 ssh2",
        "May 12 03:38:15 apollo sshd[204]: Connection closed by invalid user operator 192.168.1.105 port 44218 [preauth]",
        "May 12 03:39:01 apollo sshd[208]: Accepted password for alice from 127.0.0.1 port 51220 ssh2",
        "May 12 03:39:02 apollo pam_unix(sshd:session): session opened for user alice by (uid=0)",
        "May 12 03:39:45 apollo sudo: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/systemctl status",
        "May 12 03:39:46 apollo pam_unix(sudo:session): session opened for user root by alice(uid=0)",
        "[ALERT-0x01]: Unauthorized access detected. Rogue miner deployed to /tmp/sys_miner (PID 104).",
        "[ALERT-0x02]: Recovery binary stripped in /mnt/recovery/bin/recovery.sh.",
        "May 12 03:40:01 apollo systemd-logind[102]: Session c1 logged out. Waiting for processes to exit.",
        "May 12 03:40:05 apollo systemd[1]: Removed slice User Slice of UID 0.",
        "May 12 03:40:15 apollo CRON[215]: pam_unix(cron:session): session opened for user root",
        "May 12 03:40:18 apollo CRON[215]: pam_unix(cron:session): session closed for user root",
        "May 12 03:41:00 apollo pam_unix(sshd:session): session opened for user systemd",
        "May 12 03:41:05 apollo pam_unix(sshd:session): session closed for user systemd",
        "May 12 03:42:00 apollo sshd[220]: Received disconnect from 192.168.1.105 port 44218: 11: Normal Shutdown",
        "May 12 03:42:15 apollo systemd[1]: Stopped User Manager for UID 1000.",
        "May 12 03:43:00 apollo systemd-logind[102]: System idle check complete."
    ]
    add_file("/var/log/auth.log", "\n".join(auth_lines) + "\n", perms="640", owner="root")

    syslog_lines = [
        "03:40:01 apollo systemd[1]: Starting System Logging Service...",
        "03:40:02 apollo kernel: [    0.000000] Linux version 5.15.0-apollo (gcc 11.2.0)",
        "03:40:02 apollo kernel: [    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz-5.15.0-apollo root=/dev/sda1 ro quiet",
        "03:40:03 apollo kernel: [    0.042100] x86/fpu: Supporting XSAVE feature 0x001: 'x87 floating point registers'",
        "03:40:03 apollo kernel: [    0.042105] x86/fpu: Supporting XSAVE feature 0x002: 'SSE registers'",
        "03:40:04 apollo systemd[1]: Mounted Huge Pages File System.",
        "03:40:04 apollo systemd[1]: Mounted POSIX Message Queue File System.",
        "03:40:05 apollo systemd[1]: Started Dispatch Password Requests to Console Directory Watch.",
        "03:40:06 apollo kernel: [    0.108420] e1000e: Intel(R) PRO/1000 Network Driver",
        "03:40:07 apollo kernel: [    0.108422] e1000e 0000:00:03.0 eth0: (PCI Express:2.5GT/s:Width x1) 52:54:00:12:34:56",
        "03:40:08 apollo systemd[1]: Reached target Local Encrypted Volumes.",
        "03:40:09 apollo systemd[1]: Listening on Syslog Socket.",
        "03:40:10 apollo systemd[1]: Reached target Network (Pre).",
        "03:40:12 apollo kernel: [ALERT-0x03] Interface apollo0 link state degraded: DOWN",
        "03:40:15 apollo systemd[1]: Starting Network Time Synchronization...",
        "03:40:18 apollo systemd-timesyncd[110]: Network configuration changed, trying to establish connection.",
        "03:40:22 apollo systemd[1]: Started Network Time Synchronization.",
        "03:40:30 apollo systemd[1]: Reached target System Time Set.",
        "03:40:45 apollo systemd[1]: Starting Rotate log files...",
        "03:40:50 apollo systemd[1]: logrotate.service: Deactivated successfully.",
        "03:41:00 apollo sys_miner[104]: CPU threshold exceeded: 98.2% allocation on core 0",
        "03:41:15 apollo kernel: [   12.401920] perf: interrupt took too long (2510 > 2500), lowering kernel.perf_event_max_sample_rate to 50000",
        "03:41:30 apollo systemd[1]: Starting Periodic ext4 Online Metadata Check...",
        "03:41:40 apollo systemd[1]: e4defrag.service: Deactivated successfully.",
        "03:42:00 apollo kernel: [   14.881200] CPU0: Core temperature above threshold, cpu clock throttled",
        "03:42:19 apollo systemd[1]: [ALERT-0x04] phoenix-sync.service: Main process exited, code=killed, status=9/KILL",
        "03:42:19 apollo systemd[1]: phoenix-sync.service: Failed with result 'signal'.",
        "03:42:25 apollo systemd[1]: phoenix-sync.service: Scheduled restart job, restart counter is at 1.",
        "03:42:30 apollo systemd[1]: Stopped Phoenix Synchronization Service.",
        "03:43:00 apollo kernel: [   18.109200] audit: type=1100 audit(1652341380.120:45): pid=104 uid=0 auid=1000 ses=1 msg='op=PAM:accounting grantors=pam_unix,pam_permit acct=\"root\" exe=\"/tmp/sys_miner\" hostname=? addr=? terminal=? res=success'",
        "03:43:15 apollo systemd[1]: Starting Daily Cleanup of Temporary Directories...",
        "03:43:20 apollo systemd[1]: systemd-tmpfiles-clean.service: Deactivated successfully."
    ]
    add_file("/var/log/syslog", "\n".join(syslog_lines) + "\n", perms="644", owner="root")
    add_file(
        "/var/log/system.log",
        "03:40:12 apollo kernel: eth0 link down\n03:42:19 apollo systemd: phoenix-sync terminated\n",
        perms="644",
        owner="root"
    )

    # Milestone 3 & 4: /mnt/recovery/
    add_file(
        "/mnt/recovery/docs/RECOVERY_NOTES.txt",
        "================================================================================\n"
        "                 SECOPS RECOVERY MANIFEST // PARTITION ADVISORY\n"
        "================================================================================\n"
        "1. PERMISSION RECOVERY & SEARCH INDEXING:\n"
        "   The intruder stripped execution permissions (mode 000) on scripts in bin/.\n"
        "   Restore execute permissions with: chmod +x /mnt/recovery/bin/recovery.sh\n"
        "   Then execute recovery.sh to rebuild the partition index and unlock 'find'.\n\n"
        "2. PHOENIX CLUSTER AUTHENTICATION:\n"
        "   The cryptographic cluster key is preserved across this partition.\n"
        "   Use 'find /mnt/recovery -name \"*.key\"' to locate authentication tokens.\n"
        "   Append the key to /etc/phoenix/phoenix.conf to restore the gateway.\n"
        "================================================================================\n",
        perms="644",
        owner="root"
    )
    add_file(
        "/mnt/recovery/bin/recovery.sh",
        "#!/bin/bash\necho '[KERNEL]: Rebuilding filesystem index table...'\necho 'Partition query registers synchronized. Filesystem search (find) online.'\n",
        perms="000",
        owner="root"
    )
    add_file("/mnt/recovery/bin/apollo-net", "ELF 64-bit LSB executable [APOLLO-NET v1.0]\n", perms="000", owner="root")
    add_file("/mnt/recovery/bin/phoenix_ctl", "ELF 64-bit LSB executable [PHOENIX-CTL v2.0]\n", perms="000", owner="root")
    add_file("/mnt/recovery/bin/recovery-tool", "ELF 64-bit LSB executable [RECOVERY-TOOL v2.1]\n", perms="000", owner="root")
    add_file("/mnt/recovery/keys/phoenix.key", "PX-KEY-7701-ALPHA\n", perms="600", owner="root")

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
