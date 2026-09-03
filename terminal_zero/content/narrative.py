from typing import Dict, Optional


def get_incident_dossier(clues: Optional[Dict[str, bool]] = None) -> str:
    if clues is None:
        clues = {}

    c1 = "\033[1;32mPID: 104 (sys_miner)\033[0m" if clues.get("ALERT_0x01") else "\033[1;30m[ REDACTED_PID ]\033[0m"
    c2 = "\033[1;32m/mnt/recovery/bin/recovery.sh (mode: 000)\033[0m" if clues.get("ALERT_0x02") else "\033[1;30m[ REDACTED_PATH ]\033[0m"
    c3 = "\033[1;32mDevice: osiris0 (link: DOWN)\033[0m" if clues.get("ALERT_0x03") else "\033[1;30m[ REDACTED_DEVICE ]\033[0m"
    c4 = "\033[1;32mphoenix-sync.service (killed)\033[0m" if clues.get("ALERT_0x04") else "\033[1;30m[ REDACTED_SERVICE ]\033[0m"

    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))
    status_header = f"ALL LEADS UNMASKED ({count}/4)" if count == 4 else f"CLASSIFIED DOSSIER ({count}/4 LEADS UNMASKED)"

    return (
        "================================================================================\n"
        f"        OSIRIS WORKSTATION // INCIDENT RECOVERY DOSSIER [{status_header}]\n"
        "================================================================================\n"
        f" \033[1;31m[ALERT-0x01]\033[0m INTRUDER PROCESS : Attacker deployed rogue miner -> {c1}\n"
        f" \033[1;33m[ALERT-0x02]\033[0m TAMPERED SECTOR  : Core recovery binary stripped   -> {c2}\n"
        f" \033[1;36m[ALERT-0x03]\033[0m HARDWARE STATUS  : Network interface knocked DOWN  -> {c3}\n"
        f" \033[1;35m[ALERT-0x04]\033[0m DAEMON STATUS    : Cluster service terminated      -> {c4}\n"
        "================================================================================\n"
        "INVESTIGATION DIRECTIVE: Audit compromised logs in /var/log/ with 'head',\n"
        "'tail', or 'grep' to confirm matching breach signatures.\n"
        "================================================================================\n"
    )


def get_primary_goal(flags: Dict[str, bool], clues: Optional[Dict[str, bool]] = None) -> str:
    if clues is None:
        clues = {}

    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))

    if not flags.get("BUFFER_REPAIRED", False):
        return "CURRENT MISSION: Command history memory offline. Check 'diagnostics/BOOT_FAIL.log' and run 'repair_buffer'."
    elif not flags.get("BASHRC_RESTORED", False):
        return "CURRENT MISSION: Shell profile missing. Explore '/opt/backup/profiles/' and redirect config into ~/.bashrc."
    elif not flags.get("LOGS_AUDITED", False):
        if count == 0:
            return "CURRENT MISSION: Investigate security breach. Audit logs in '/var/log/' with 'tail' or 'grep'."
        else:
            return f"CURRENT MISSION: Register security breach leads in '/var/log/'. ({count}/4 incident leads unmasked)."
    elif not (flags.get("PERMISSIONS_RESTORED", False) and flags.get("FIND_UNLOCKED", False)):
        return "CURRENT MISSION: Recovery partition locked. Use 'find' and grant execute permissions ('chmod +x') to recovery tools."
    elif not flags.get("MALWARE_TERMINATED", False):
        return "CURRENT MISSION: CPU threshold critical @ 98%. Locate and terminate the high-CPU rogue miner process with 'kill -9'."
    elif not flags.get("NETWORK_ONLINE", False):
        return "CURRENT MISSION: Physical network adapter offline. Inspect '/etc/network/interfaces', bring device 'osiris0' online, and verify gateway."
    elif not flags.get("PHOENIX_ONLINE", False):
        return "CURRENT MISSION: Cluster supervisor offline. Append key to '/etc/phoenix/phoenix.conf' via '>>', set permissions ('chmod 644'), and launch daemon."
    else:
        return "MISSION ACCOMPLISHED: All workstation subsystems nominal! OSIRIS cluster gateway is fully restored."


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
    p3_2 = "x" if flags.get("PERMISSIONS_RESTORED", False) or flags.get("FIND_UNLOCKED", False) else " "
    p3_3 = "x" if flags.get("FIND_UNLOCKED", False) else " "

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
        f"    • [{p0_2}] Execute 'repair_buffer' to restore command history (Up/Down keys)\n\n"
    )

    p1_text = (
        f"[{p1}] PHASE 1: USER SHELL ENVIRONMENT\n"
        f"    • [{p1_1}] Locate backup profile template in /opt/backup/profiles/\n"
        f"    • [{p1_2}] Redirect clean config into ~/.bashrc to unlock Tab autocompletion\n\n"
    ) if 1 <= active_phase else (
        f"[{p1}] PHASE 1: USER SHELL ENVIRONMENT\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p2_text = (
        f"[{p2}] PHASE 2: INCIDENT LOG FORENSICS\n"
        f"    • [{p2_1}] Audit security logs in /var/log/ with 'tail' or 'grep'\n"
        f"    • [{p2_2}] Identify breach signatures and unmask dossier leads ({count}/4 unmasked)\n\n"
    ) if 2 <= active_phase else (
        f"[{p2}] PHASE 2: INCIDENT LOG FORENSICS\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p3_text = (
        f"[{p3}] PHASE 3: RECOVERY PARTITION & RECURSIVE SEARCH\n"
        f"    • [{p3_1}] Use 'find' in /mnt/recovery to locate recovery script and cluster key\n"
        f"    • [{p3_2}] Grant execute permissions ('chmod +x') to /mnt/recovery/bin/recovery.sh\n"
        f"    • [{p3_3}] Run './recovery.sh' to link signal handlers and unlock Ctrl+C\n\n"
    ) if 3 <= active_phase else (
        f"[{p3}] PHASE 3: RECOVERY PARTITION & RECURSIVE SEARCH\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p4_text = (
        f"[{p4}] PHASE 4: PROCESS SUPERVISOR & ROGUE MINER\n"
        f"    • [{p4_1}] Audit process table with 'ps aux' to locate high-CPU rogue worker\n"
        f"    • [{p4_2}] Force-terminate miner process using unconditional signal ('kill -9')\n\n"
    ) if 4 <= active_phase else (
        f"[{p4}] PHASE 4: PROCESS SUPERVISOR & ROGUE MINER\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p5_text = (
        f"[{p5}] PHASE 5: NETWORK HARDWARE & GATEWAY UPLINK\n"
        f"    • [{p5_1}] Inspect interface definitions in /etc/network/interfaces\n"
        f"    • [{p5_2}] Bring physical interface 'osiris0' online via 'ip link'\n"
        f"    • [{p5_3}] Verify gateway reachability with ping probe ('ping -c 4 10.0.42.1')\n\n"
    ) if 5 <= active_phase else (
        f"[{p5}] PHASE 5: NETWORK HARDWARE & GATEWAY UPLINK\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    p6_text = (
        f"[{p6}] PHASE 6: CLUSTER SUPERVISOR DAEMON\n"
        f"    • [{p6_1}] Safely append cluster key into /etc/phoenix/phoenix.conf using '>>'\n"
        f"    • [{p6_2}] Lock down configuration permissions ('chmod 644')\n"
        f"    • [{p6_3}] Launch 'phoenix_daemon start' and verify listener socket on port 8080\n"
    ) if 6 <= active_phase else (
        f"[{p6}] PHASE 6: CLUSTER SUPERVISOR DAEMON\n"
        f"    • [ ] ??? [Classified Directives]\n\n"
    )

    footer = (
        "[SHORTCUT ACTIVE]:\n"
        "Type 'todo' or 'tasks' from any directory to inspect your recovery progress.\n"
        "Type 'manuals' or 'docs' to browse all discovered field manuals and guides."
    ) if flags.get("TODO_LINKED", False) else (
        "[STATUS]: Type 'todo' from any folder to review active workstation objectives.\n"
        "Tip: Run 'taskctl link' to enable global shortcuts, or 'manuals' for documentation."
    )

    return (
        "================================================================================\n"
        "               OSIRIS WORKSTATION // INCIDENT RECOVERY CHECKLIST\n"
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
        "[PHOENIX-DAEMON]: Handshake verified with gateway node 10.0.42.1:8080.\n"
        "[PHOENIX-DAEMON]: Ingress routing tables broadcasted across subnet.\n"
        "[PHOENIX-DAEMON]: Workstation OSIRIS verified as AUTHENTIC ROOT CLUSTER NODE.\n"
        "\n"
        "================================================================================\n"
        "                        OSIRIS WORKSTATION RECOVERED\n"
        "================================================================================\n"
        "  All local subsystems operational. Global mesh synchronization initialized.\n"
        "  Workstation containment lifted. Terminal session secured.\n"
        "================================================================================\n"
        "\n"
        "[INCOMING SYSTEM BROADCAST // MORGAN]\n"
        "\"Alice... the gateway just responded. The entire Phoenix mesh is lighting up \n"
        "across the northern grid. \n"
        "\n"
        "I don't know who you were before this system crashed, but you just audited logs, \n"
        "re-linked POSIX line disciplines, managed processes, and brought a dead \n"
        "infrastructure cluster back to life from a raw command prompt.\n"
        "\n"
        "Take a breath. You're no longer typing in the dark. \n"
        "\n"
        "I'll see you on the network.\"\n"
        "================================================================================\n"
    )


