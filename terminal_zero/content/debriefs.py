import sys
from typing import Dict
from terminal_zero.core.events import Event, EventBus


class DebriefManager:
    DEBRIEFS: Dict[str, str] = {
        "BUFFER_REPAIRED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Terminal Line Disciplines & Input Buffering        │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You just repaired the input ring buffer to restore command history.   │\n"
            "│ In real Linux systems:                                                 │\n"
            "│ • The kernel TTY line discipline handles cooked vs raw input modes.    │\n"
            "│ • Libraries like GNU Readline manage arrow key navigation and history. │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "BASHRC_RESTORED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Shell Startup Profiles & Environment Variables    │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You restored ~/.bashrc to re-enable tab autocompletion and $PATH.     │\n"
            "│ In real Linux systems:                                                 │\n"
            "│ • ~/.bashrc runs for interactive non-login shells.                     │\n"
            "│ • The $PATH variable defines directory search order for executables.   │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "MALWARE_TERMINATED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Real-World Process Administration & Signals        │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You just used 'kill -9' to terminate a rogue process.                  │\n"
            "│ In production Linux environments:                                      │\n"
            "│ • SIGTERM (-15) allows processes to clean up sockets & open files.     │\n"
            "│ • SIGKILL (-9) immediately revokes kernel resources; use with care!    │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "FIND_UNLOCKED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: POSIX File Permissions & Filesystem Search         │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You made recovery.sh executable and rebuilt the partition search index.│\n"
            "│ In real Linux systems:                                                 │\n"
            "│ • 'chmod +x' or 'chmod 755' restores executable mode bits on binaries. │\n"
            "│ • 'find' traverses directory hierarchies matching names, types, & size.│\n"
            "│ • Example: find / -name \"*.key\" or find /mnt/recovery -type f          │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "LOGS_AUDITED": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Log Triaging & Stream Filtering                    │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You filtered security logs in /var/log to isolate the intrusion.       │\n"
            "│ In real Linux systems:                                                 │\n"
            "│ • 'grep -i' searches case-insensitively for key strings in logs.       │\n"
            "│ • 'tail -n' and 'tail -f' monitor the latest append-only kernel events.│\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "NETWORK_ONLINE": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Network Interface Management with 'ip'             │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You used 'ip link set apollo0 up' to bring the network online.        │\n"
            "│ In modern Linux distributions:                                         │\n"
            "│ • The 'ip' tool (iproute2) replaced the legacy 'ifconfig' utility.     │\n"
            "│ • 'ip addr' inspects subnets, while 'ip route' controls IP gateways.  │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        ),
        "PHOENIX_ONLINE": (
            "┌────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Daemon Sockets & Service Orchestration             │\n"
            "├────────────────────────────────────────────────────────────────────────┤\n"
            "│ You restored the PHOENIX daemon and verified listening sockets.        │\n"
            "│ In enterprise Linux environments:                                      │\n"
            "│ • 'ss -tulpn' audits TCP/UDP sockets and binds to specific interfaces. │\n"
            "│ • Systemd unit files manage auto-restart and target state transitions. │\n"
            "└────────────────────────────────────────────────────────────────────────┘"
        )
    }

    TITLES: Dict[str, str] = {
        "BUFFER_REPAIRED": "Terminal Line Disciplines & Input Buffering",
        "BASHRC_RESTORED": "Shell Startup Profiles & Environment Variables",
        "MALWARE_TERMINATED": "Real-World Process Administration & Signals",
        "FIND_UNLOCKED": "POSIX File Permissions & Filesystem Search",
        "LOGS_AUDITED": "Log Triaging & Stream Filtering",
        "NETWORK_ONLINE": "Network Interface Management with 'ip'",
        "PHOENIX_ONLINE": "Daemon Sockets & Service Orchestration",
    }

    def __init__(self, bus: EventBus, output_writer=None):
        self.bus = bus
        self.output_writer = output_writer or sys.stdout.write
        self.bus.subscribe(self.handle_event)

    def handle_event(self, event: Event):
        if event.type == "flag_changed":
            flag = event.data.get("flag")
            value = event.data.get("value")
            if value and flag in self.DEBRIEFS:
                title = self.TITLES.get(flag, flag)
                if flag == "BASHRC_RESTORED":
                    self.output_writer("\n[!] ABILITY UNLOCKED: Shell Profile & Command Shortcuts Synchronized (Aliases active: try 'll')\n")
                elif flag == "BUFFER_REPAIRED":
                    self.output_writer("\n[!] ABILITY UNLOCKED: Command Memory Recall (Use UP/DOWN arrows to navigate history)\n")
                self.output_writer(f"[+] Linux Field Guide entry registered: '{title}'\n    (Type 'fieldguide' or 'cards' to review your real-world Linux debriefs)\n")
