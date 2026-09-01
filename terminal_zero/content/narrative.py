from typing import Dict


def get_primary_goal(flags: Dict[str, bool]) -> str:
    if not flags.get("BUFFER_REPAIRED", False):
        return "CURRENT MISSION: Command recall memory is offline. Read 'BOOT_FAIL.log' and run 'repair_buffer' to restore Up/Down arrow history."
    elif not flags.get("BASHRC_RESTORED", False):
        return "CURRENT MISSION: Morgan left a backup profile in '/opt/backup/profiles/'. Head there with 'cd /opt/backup/profiles' and restore your shell."
    elif not flags.get("LOGS_AUDITED", False):
        return "CURRENT MISSION: Investigate the security breach. Audit incident logs in '/var/log' using 'cat', 'head', 'tail', or 'grep'."
    elif not (flags.get("RECOVERY_LOCATED", False) and flags.get("PERMISSIONS_RESTORED", False)):
        return "CURRENT MISSION: Locate recovery tools in '/mnt/recovery/bin', unlock execution with 'chmod +x', and run 'recovery.sh'."
    elif not flags.get("MALWARE_TERMINATED", False):
        return "CURRENT MISSION: Hunt down the rogue miner draining 98% CPU. Run 'ps aux' to find its PID, then terminate it with 'kill -9 104'."
    elif not flags.get("NETWORK_ONLINE", False):
        return "CURRENT MISSION: Network interface offline. Bring adapter 'apollo0' online with 'ip link set apollo0 up' and verify with 'ping'."
    elif not flags.get("PHOENIX_ONLINE", False):
        return "CURRENT MISSION: Final step! Append auth key from '/mnt/recovery/keys/phoenix.key' to '/etc/phoenix/phoenix.conf' and start 'phoenix_daemon'."
    else:
        return "MISSION ACCOMPLISHED: All workstation subsystems nominal! APOLLO is fully restored."


def get_todo_content(flags: Dict[str, bool]) -> str:
    m0 = "x" if flags.get("BUFFER_REPAIRED", False) else " "
    m1 = "x" if flags.get("BASHRC_RESTORED", False) else " "
    m2 = "x" if flags.get("LOGS_AUDITED", False) else " "
    m3 = "x" if flags.get("RECOVERY_LOCATED", False) else " "
    m5 = "x" if flags.get("MALWARE_TERMINATED", False) else " "
    m6 = "x" if flags.get("NETWORK_ONLINE", False) else " "
    m7 = "x" if flags.get("PHOENIX_ONLINE", False) else " "
    return (
        "================================================================================\n"
        "               APOLLO WORKSTATION // INCIDENT RECOVERY CHECKLIST\n"
        "================================================================================\n"
        f"[{m0}] 0. RESTORE RECALL    : Command history dead   -> Run 'repair_buffer'\n"
        f"[{m1}] 1. REBUILD PROFILE   : Shell shortcuts missing-> Copy /opt/backup/profiles/alice.bashrc to ~/.bashrc\n"
        f"[{m2}] 2. TRIAGE BREACH     : Intruder left traces   -> Inspect incident logs in /var/log/\n"
        f"[{m5}] 3. HUNT ROGUE MINER  : 98% CPU drain          -> Locate rogue PID with 'ps' & terminate with 'kill -9'\n"
        f"[{m6}] 4. ACTIVATE UPLINK   : Network offline        -> Bring 'apollo0' interface online with 'ip link'\n"
        f"[{m7}] 5. RESTART DAEMON    : PHOENIX offline        -> Re-link auth key & boot daemon in /etc/phoenix/\n"
        "================================================================================\n"
    )
