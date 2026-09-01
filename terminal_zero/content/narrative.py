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
        "INVESTIGATION DIRECTIVE: Audit logs in /var/log/ with 'cat', 'head', 'tail', or 'grep'\n"
        "to discover matching color-coded [ALERT-0x0X] incident markers and fill in gaps.\n"
        "================================================================================\n"
    )


def get_primary_goal(flags: Dict[str, bool], clues: Optional[Dict[str, bool]] = None) -> str:
    if clues is None:
        clues = {}

    count = sum(1 for k in ["ALERT_0x01", "ALERT_0x02", "ALERT_0x03", "ALERT_0x04"] if clues.get(k))

    if not flags.get("BUFFER_REPAIRED", False):
        return "CURRENT MISSION: Command recall memory is offline. Read 'BOOT_FAIL.log' and run 'repair_buffer' to restore Up/Down arrow history."
    elif not flags.get("BASHRC_RESTORED", False):
        return "CURRENT MISSION: Morgan left a backup profile in '/opt/backup/profiles/'. Head there with 'cd /opt/backup/profiles' and restore your shell."
    elif not flags.get("LOGS_AUDITED", False):
        if count == 0:
            return "CURRENT MISSION: Investigate the security breach. Audit incident logs in '/var/log' using 'cat', 'head', 'tail', or 'grep' to unmask incident clues."
        else:
            return f"CURRENT MISSION: Triage breach logs in '/var/log'. ({count}/4 incident leads unmasked — inspect 'auth.log' and 'syslog')."
    elif not (flags.get("RECOVERY_LOCATED", False) and flags.get("PERMISSIONS_RESTORED", False)):
        return "CURRENT MISSION: Leads unmasked! Head to '/mnt/recovery/bin', unlock execution with 'chmod +x', and run 'recovery.sh'."
    elif not flags.get("MALWARE_TERMINATED", False):
        return "CURRENT MISSION: Hunt down rogue miner PID 104 draining 98% CPU. Run 'ps aux' to verify, then terminate with 'kill -9 104'."
    elif not flags.get("NETWORK_ONLINE", False):
        return "CURRENT MISSION: Network interface offline. Bring adapter 'apollo0' online with 'ip link set apollo0 up' and verify with 'ping'."
    elif not flags.get("PHOENIX_ONLINE", False):
        return "CURRENT MISSION: Final step! Append auth key from '/mnt/recovery/keys/phoenix.key' to '/etc/phoenix/phoenix.conf' and start 'phoenix_daemon'."
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
    m2_label = "2. TRIAGE BREACH     : All incident leads unmasked (4/4)" if flags.get("LOGS_AUDITED") else f"2. TRIAGE BREACH     : Unmask incident clues in /var/log/ ({count}/4 unmasked)"

    return (
        "================================================================================\n"
        "               APOLLO WORKSTATION // INCIDENT RECOVERY CHECKLIST\n"
        "================================================================================\n"
        f"[{m0}] 0. RESTORE RECALL    : Command history dead   -> Run 'repair_buffer'\n"
        f"[{m1}] 1. REBUILD PROFILE   : Shell shortcuts missing-> Copy /opt/backup/profiles/alice.bashrc to ~/.bashrc\n"
        f"[{m2}] {m2_label}\n"
        f"[{m5}] 3. HUNT ROGUE MINER  : 98% CPU drain          -> Locate rogue PID 104 with 'ps' & terminate with 'kill -9'\n"
        f"[{m6}] 4. ACTIVATE UPLINK   : Network offline        -> Bring 'apollo0' interface online with 'ip link'\n"
        f"[{m7}] 5. RESTART DAEMON    : PHOENIX offline        -> Re-link auth key & boot daemon in /etc/phoenix/\n"
        "================================================================================\n"
    )
