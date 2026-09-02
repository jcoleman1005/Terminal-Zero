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
        return "CURRENT MISSION: Shell profile missing. Explore '/opt/backup/profiles/' and restore ~/.bashrc."
    elif not flags.get("LOGS_AUDITED", False):
        if count == 0:
            return "CURRENT MISSION: Investigate the security breach. Audit daemon logs in '/var/log/' to unmask incident clues."
        else:
            return f"CURRENT MISSION: Triage breach logs in '/var/log/'. ({count}/4 incident leads unmasked)."
    elif not (flags.get("PERMISSIONS_RESTORED", False) and flags.get("SIGINT_UNLOCKED", False)):
        return "CURRENT MISSION: Recovery tools locked. Explore '/mnt/recovery/bin/', restore execution permissions, and run recovery.sh."
    elif not flags.get("MALWARE_TERMINATED", False):
        return "CURRENT MISSION: CPU threshold critical. Audit process table with 'ps' and terminate the rogue miner PID."
    elif not flags.get("NETWORK_ONLINE", False):
        return "CURRENT MISSION: Network interface offline. Inspect '/etc/network/' and bring interface 'apollo0' online."
    elif not flags.get("PHOENIX_ONLINE", False):
        return "CURRENT MISSION: Final hurdle! Re-authenticate PHOENIX daemon with recovery key and start service in '/etc/phoenix/'."
    else:
        return "MISSION ACCOMPLISHED: All workstation subsystems nominal! APOLLO is fully restored."


def get_todo_content(flags: Dict[str, bool], clues: Optional[Dict[str, bool]] = None) -> str:
    if clues is None:
        clues = {}

    m0 = "x" if flags.get("BUFFER_REPAIRED", False) else " "
    m1 = "x" if flags.get("BASHRC_RESTORED", False) else " "
    m2 = "x" if flags.get("LOGS_AUDITED", False) else " "
    m3 = "x" if flags.get("RECOVERY_LOCATED", False) else " "
    m5 = "x" if flags.get("MALWARE_TERMINATED", False) else " "
    m6 = "x" if flags.get("NETWORK_ONLINE", False) else " "
    m7 = "x" if flags.get("PHOENIX_ONLINE", False) else " "

    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))
    m2_label = "2. TRIAGE BREACH     : All incident leads unmasked (4/4)" if flags.get("LOGS_AUDITED") else f"2. TRIAGE BREACH     : Audit daemons in /var/log/ ({count}/4 unmasked)"

    footer = (
        "[SHORTCUT ACTIVE]:\n"
        "Type 'todo' or 'tasks' from any directory to inspect your recovery progress.\n"
    ) if flags.get("TODO_LINKED", False) else (
        "[OPERATOR SHORTCUT TIP]:\n"
        "Run 'taskctl link' to enable the 'todo' and 'tasks' global shortcuts anywhere!\n"
    )

    return (
        "================================================================================\n"
        "               APOLLO WORKSTATION // INCIDENT RECOVERY CHECKLIST\n"
        "================================================================================\n"
        f"[{m0}] 0. RESTORE RECALL    : Input ring buffer dead -> Inspect diagnostics/BOOT_FAIL.log\n"
        f"[{m1}] 1. REBUILD PROFILE   : Shell shortcuts missing-> Find backup template in /opt/backup/\n"
        f"[{m2}] {m2_label}\n"
        f"[{m3}] 3. UNLOCK RECOVERY   : Tools stripped (chmod) -> Restore permissions in /mnt/recovery/\n"
        f"[{m5}] 4. HUNT ROGUE MINER  : 98% CPU drain          -> Find intruder in process table & terminate\n"
        f"[{m6}] 5. ACTIVATE UPLINK   : Network offline        -> Inspect network interfaces in /etc/network/\n"
        f"[{m7}] 6. RESTART DAEMON    : PHOENIX offline        -> Re-authenticate cluster daemon in /etc/phoenix/\n"
        "================================================================================\n"
        f"{footer}"
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
