from typing import Dict, Optional


def get_incident_dossier(clues: Optional[Dict[str, bool]] = None) -> str:
    if clues is None:
        clues = {}

    c1 = "\033[1;32mPID: 104 (sys_miner)\033[0m" if clues.get("ALERT_0x01") else "\033[1;30m[ REDACTED_PID ]\033[0m"
    c2 = "\033[1;32m/mnt/recovery/bin/recovery.sh (mode: 000)\033[0m" if clues.get("ALERT_0x02") else "\033[1;30m[ REDACTED_PATH ]\033[0m"
    c3 = "\033[1;32mDevice: apollo0 (link: DOWN)\033[0m" if clues.get("ALERT_0x03") else "\033[1;30m[ REDACTED_DEVICE ]\033[0m"
    c4 = "\033[1;32mphoenix-sync.service (killed)\033[0m" if clues.get("ALERT_0x04") else "\033[1;30m[ REDACTED_SERVICE ]\033[0m"

    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))
    status_header = f"ALL LEADS UNMASKED ({count}/4)" if count == 4 else f"CLASSIFIED DOSSIER ({count}/4 LEADS UNMASKED)"

    return (
        "================================================================================\n"
        f"        APOLLO WORKSTATION // INCIDENT RECOVERY DOSSIER [{status_header}]\n"
        "================================================================================\n"
        f" \033[1;31m[ALERT-0x01]\033[0m INTRUDER PROCESS : Attacker deployed rogue miner -> {c1}\n"
        f" \033[1;33m[ALERT-0x02]\033[0m TAMPERED SECTOR  : Core recovery binary stripped   -> {c2}\n"
        f" \033[1;36m[ALERT-0x03]\033[0m HARDWARE STATUS  : Network interface knocked DOWN  -> {c3}\n"
        f" \033[1;35m[ALERT-0x04]\033[0m DAEMON STATUS    : Cluster service terminated      -> {c4}\n"
        "================================================================================\n"
        "INVESTIGATION DIRECTIVE: Audit compromised daemon logs in /var/log/ with 'cat',\n"
        "'head', 'tail', or 'grep' to uncover matching incident leads.\n"
        "================================================================================\n"
    )


def get_primary_goal(flags: Dict[str, bool], clues: Optional[Dict[str, bool]] = None) -> str:
    if clues is None:
        clues = {}

    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))

    if not flags.get("BUFFER_REPAIRED", False):
        return "CURRENT MISSION: Command history memory offline. Check 'diagnostics/BOOT_FAIL.log' and run the repair utility."
    elif not flags.get("BASHRC_RESTORED", False):
        return "CURRENT MISSION: Shell profile missing. Explore '/opt/backup/profiles/' and restore ~/.bashrc template."
    elif not flags.get("LOGS_AUDITED", False):
        if count == 0:
            return "CURRENT MISSION: Investigate security breach. Audit daemon logs in '/var/log/' with 'grep' or 'cat' to unmask leads."
        else:
            return f"CURRENT MISSION: Register security breach leads in '/var/log/'. ({count}/4 incident leads unmasked)."
    elif not (flags.get("PERMISSIONS_RESTORED", False) and flags.get("FIND_UNLOCKED", False)):
        return "CURRENT MISSION: Recovery partition locked. Elevate execution permissions on '/mnt/recovery/bin/recovery.sh' (chmod +x) and execute to rebuild search index."
    elif not flags.get("MALWARE_TERMINATED", False):
        return "CURRENT MISSION: CPU threshold critical @ 98%. Check running programs with 'ps' to find the rogue miner's process ID (PID), then terminate with 'kill -9 <PID>'."
    elif not flags.get("NETWORK_ONLINE", False):
        return "CURRENT MISSION: Physical network adapter offline. Inspect '/etc/network/interfaces', bring device 'apollo0' UP, and probe gateway reachability."
    elif not flags.get("PHOENIX_ONLINE", False):
        return "CURRENT MISSION: Cluster supervisor offline. Search for cryptographic key (*.key), append to '/etc/phoenix/phoenix.conf', lock permissions (chmod 644), and launch daemon."
    else:
        return "MISSION ACCOMPLISHED: All workstation subsystems nominal! APOLLO cluster gateway is fully restored."


def get_todo_content(flags: Dict[str, bool], clues: Optional[Dict[str, bool]] = None) -> str:
    if clues is None:
        clues = {}

    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))

    if not flags.get("BUFFER_REPAIRED", False):
        active_phase = 0
    elif not flags.get("BASHRC_RESTORED", False):
        active_phase = 1
    elif not flags.get("LOGS_AUDITED", False):
        active_phase = 2
    elif not flags.get("FIND_UNLOCKED", False):
        active_phase = 3
    elif not flags.get("MALWARE_TERMINATED", False):
        active_phase = 4
    elif not flags.get("NETWORK_ONLINE", False):
        active_phase = 5
    elif not flags.get("PHOENIX_ONLINE", False):
        active_phase = 6
    else:
        active_phase = 7

    p0 = "x" if flags.get("BUFFER_REPAIRED", False) else " "
    p0_1 = "x" if flags.get("README_INSPECTED", False) or flags.get("BUFFER_REPAIRED", False) else " "
    p0_2 = "x" if flags.get("BUFFER_REPAIRED", False) else " "

    p1 = "x" if flags.get("BASHRC_RESTORED", False) else " "
    p1_1 = "x" if flags.get("BASHRC_RESTORED", False) else " "
    p1_2 = "x" if flags.get("BASHRC_RESTORED", False) else " "

    p2 = "x" if flags.get("LOGS_AUDITED", False) else " "
    p2_1 = "x" if count > 0 or flags.get("LOGS_AUDITED", False) else " "
    p2_2 = "x" if flags.get("LOGS_AUDITED", False) else " "

    p3 = "x" if flags.get("FIND_UNLOCKED", False) else " "
    p3_1 = "x" if flags.get("PERMISSIONS_RESTORED", False) or flags.get("FIND_UNLOCKED", False) else " "
    p3_2 = "x" if flags.get("FIND_UNLOCKED", False) else " "
    p3_3 = "x" if flags.get("PHOENIX_ONLINE", False) or flags.get("KEY_DISCOVERED", False) else " "

    p4 = "x" if flags.get("MALWARE_TERMINATED", False) else " "
    p4_1 = "x" if flags.get("MALWARE_TERMINATED", False) or flags.get("PROCESS_CHECKED", False) else " "
    p4_2 = "x" if flags.get("MALWARE_TERMINATED", False) else " "

    p5 = "x" if flags.get("NETWORK_ONLINE", False) else " "
    p5_1 = "x" if flags.get("NETWORK_ONLINE", False) else " "
    p5_2 = "x" if flags.get("NETWORK_ONLINE", False) else " "
    p5_3 = "x" if flags.get("NETWORK_ONLINE", False) else " "

    p6 = "x" if flags.get("PHOENIX_ONLINE", False) else " "
    p6_1 = "x" if flags.get("PHOENIX_ONLINE", False) else " "
    p6_2 = "x" if flags.get("PHOENIX_ONLINE", False) else " "
    p6_3 = "x" if flags.get("PHOENIX_ONLINE", False) else " "

    p0_text = (
        f"[{p0}] PHASE 0: COLD BOOT & MEMORY RECALL\n"
        f"    • [{p0_1}] Inspect diagnostics/BOOT_FAIL.log for ring buffer fault\n"
        f"    • [{p0_2}] Execute line discipline repair utility to restore history recall\n\n"
    )

    p1_text = (
        f"[{p1}] PHASE 1: USER SHELL ENVIRONMENT\n"
        f"    • [{p1_1}] Locate backup profile template in /opt/backup/profiles/\n"
        f"    • [{p1_2}] Synchronize ~/.bashrc to restore command paths and shortcuts\n\n"
    ) if 1 <= active_phase else (
        f"[{p1}] PHASE 1: USER SHELL ENVIRONMENT\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p2_text = (
        f"[{p2}] PHASE 2: INCIDENT LOG FORENSICS\n"
        f"    • [{p2_1}] Audit security daemon events in /var/log/ with 'grep'\n"
        f"    • [{p2_2}] Register confirmed incident leads in dossier ({count}/4 unmasked)\n\n"
    ) if 2 <= active_phase else (
        f"[{p2}] PHASE 2: INCIDENT LOG FORENSICS\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p3_text = (
        f"[{p3}] PHASE 3: RECOVERY PARTITION & SEARCH INDEX\n"
        f"    • [{p3_1}] Elevate script execution permissions in /mnt/recovery/bin/ (chmod +x)\n"
        f"    • [{p3_2}] Run recovery.sh to rebuild filesystem search index (find)\n"
        f"    • [{p3_3}] Scan partition for cluster authentication key (*.key)\n\n"
    ) if 3 <= active_phase else (
        f"[{p3}] PHASE 3: RECOVERY PARTITION & SEARCH INDEX\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p4_text = (
        f"[{p4}] PHASE 4: PROCESS SUPERVISOR & ROGUE MINER\n"
        f"    • [{p4_1}] Check running programs with 'ps' to find the high-CPU rogue miner (PID)\n"
        f"    • [{p4_2}] Stop the rogue miner with 'kill -9 <PID>' using its process ID number\n\n"
    ) if 4 <= active_phase else (
        f"[{p4}] PHASE 4: PROCESS SUPERVISOR & ROGUE MINER\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p5_text = (
        f"[{p5}] PHASE 5: NETWORK HARDWARE & GATEWAY UPLINK\n"
        f"    • [{p5_1}] Review interface configuration in /etc/network/interfaces\n"
        f"    • [{p5_2}] Bring physical link state of device 'apollo0' to UP\n"
        f"    • [{p5_3}] Verify subnet gateway reachability with ICMP echo probe\n\n"
    ) if 5 <= active_phase else (
        f"[{p5}] PHASE 5: NETWORK HARDWARE & GATEWAY UPLINK\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p6_text = (
        f"[{p6}] PHASE 6: CLUSTER SUPERVISOR DAEMON\n"
        f"    • [{p6_1}] Append cryptographic recovery key to /etc/phoenix/phoenix.conf\n"
        f"    • [{p6_2}] Secure configuration file permissions (chmod 644)\n"
        f"    • [{p6_3}] Launch PHOENIX restoration service and verify socket on port 8080\n"
    ) if 6 <= active_phase else (
        f"[{p6}] PHASE 6: CLUSTER SUPERVISOR DAEMON\n"
        f"    • [ ] ??? [Classified Directives]\n"
    )

    footer = (
        "[SHORTCUT ACTIVE]:\n"
        "Type 'todo' or 'tasks' from any directory to inspect your recovery progress.\n"
        "Type 'manuals' or 'docs' to browse all discovered field manuals and guides."
    ) if flags.get("TODO_LINKED", False) else (
        "[OPERATOR SHORTCUT TIP]:\n"
        "Run 'taskctl link' to enable the 'todo' and 'tasks' global shortcuts anywhere!\n"
        "Run 'manuals' to view your collected system documentation and cheat sheets."
    )

    return (
        "================================================================================\n"
        "               APOLLO WORKSTATION // INCIDENT RECOVERY CHECKLIST\n"
        "================================================================================\n"
        f"{p0_text}"
        f"{p1_text}"
        f"{p2_text}"
        f"{p3_text}"
        f"{p4_text}"
        f"{p5_text}"
        f"{p6_text}"
        "================================================================================\n"
        f"{footer}\n"
        "================================================================================\n"
    )


def get_victory_screen() -> str:
    return (
        "\n"
        "================================================================================\n"
        "       ★ ★ ★  APOLLO WORKSTATION RESTORATION COMPLETE  ★ ★ ★\n"
        "================================================================================\n"
        " [ OK ] Memory Recall Buffer    : Synchronized (TTY line discipline active)\n"
        " [ OK ] User Shell Environment   : Restored (PATH, aliases & tab-completion online)\n"
        " [ OK ] Security Log Audit       : Triaged (All 4 intrusion vectors isolated)\n"
        " [ OK ] Recovery Partition       : Execution permissions & signal traps linked\n"
        " [ OK ] Process Integrity        : Rogue miner terminated (CPU 0.1% nominal)\n"
        " [ OK ] Network Interface        : Device apollo0 ONLINE (10.0.42.15/24)\n"
        " [ OK ] PHOENIX Restoration Svc  : Daemon listening on 127.0.0.1:8080 (Gateway UP)\n"
        "================================================================================\n"
        "*** WORKSTATION OPERATIONAL: MISSION ACCOMPLISHED ***\n"
        "Operator alice: You successfully diagnosed, triaged, and recovered APOLLO!\n"
        "Type 'exit' to disconnect or 'help' to review recovered subsystems.\n"
        "================================================================================\n"
    )
