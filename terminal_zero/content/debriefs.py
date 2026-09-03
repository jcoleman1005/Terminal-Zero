import sys
from typing import Dict
from terminal_zero.core.events import Event, EventBus


class DebriefManager:
    DEBRIEFS: Dict[str, str] = {
        "BUFFER_REPAIRED": (
            "┌──────────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Terminal Line Disciplines & Input Buffering              │\n"
            "├──────────────────────────────────────────────────────────────────────────────┤\n"
            "│ What you fixed in the game:                                                  │\n"
            "│ You ran 'repair_buffer' to restore your Up and Down arrow key history.       │\n"
            "│                                                                              │\n"
            "│ How real Linux systems handle this:                                          │\n"
            "│ • Terminal Emulators communicate with the Linux kernel through a software    │\n"
            "│   layer called the TTY Line Discipline.                                      │\n"
            "│ • In 'cooked mode', the line discipline buffers characters until Enter is    │\n"
            "│   pressed, allowing backspace editing. In 'raw mode', characters pass        │\n"
            "│   directly to the program.                                                   │\n"
            "│ • Arrow key command history is managed in user-space by GNU Readline.        │\n"
            "│   Readline saves previous entries to a hidden file (~/.bash_history) and     │\n"
            "│   navigates them via terminal escape sequences.                              │\n"
            "└──────────────────────────────────────────────────────────────────────────────┘"
        ),
        "BASHRC_RESTORED": (
            "┌──────────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Standard Output Redirection (> and >>)                   │\n"
            "├──────────────────────────────────────────────────────────────────────────────┤\n"
            "│ What you fixed in the game:                                                  │\n"
            "│ You used '>' to restore ~/.bashrc and '>>' to append a cryptographic key.    │\n"
            "│                                                                              │\n"
            "│ How real Linux systems handle this:                                          │\n"
            "│ • Every Linux process has three standard data streams: Standard Input        │\n"
            "│   (stdin / fd 0), Standard Output (stdout / fd 1), and Standard Error        │\n"
            "│   (stderr / fd 2).                                                           │\n"
            "│ • The single right arrow '>' redirects stdout into a file, completely        │\n"
            "│   TRUNCATING (erasing) any previous content inside that file.                │\n"
            "│ • The double right arrow '>>' opens the destination file in APPEND mode,      │\n"
            "│   writing new data strictly after the final line without touching old data.  │\n"
            "└──────────────────────────────────────────────────────────────────────────────┘"
        ),
        "LOGS_AUDITED": (
            "┌──────────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Log Triaging & Stream Filtering (grep / tail)            │\n"
            "├──────────────────────────────────────────────────────────────────────────────┤\n"
            "│ What you fixed in the game:                                                  │\n"
            "│ You filtered security logs in /var/log to isolate intrusion signatures.      │\n"
            "│                                                                              │\n"
            "│ How real Linux systems handle this:                                          │\n"
            "│ • In production systems, /var/log collects continuous streams of events from │\n"
            "│   systemd journald, syslogd, and authentication daemons.                     │\n"
            "│ • 'grep -i' performs fast case-insensitive pattern matching across gigabytes │\n"
            "│   of text without loading entire files into memory.                          │\n"
            "│ • 'tail -n' and 'tail -f' allow operators to follow recent log entries in    │\n"
            "│   real time as live incident events occur.                                   │\n"
            "└──────────────────────────────────────────────────────────────────────────────┘"
        ),
        "FIND_UNLOCKED": (
            "┌──────────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: POSIX Permissions & Execution Bits                       │\n"
            "├──────────────────────────────────────────────────────────────────────────────┤\n"
            "│ What you fixed in the game:                                                  │\n"
            "│ You used 'chmod +x' to make a recovery script runnable.                       │\n"
            "│                                                                              │\n"
            "│ How real Linux systems handle this:                                          │\n"
            "│ • Unix filesystems store access rights in mode bits split into triplets:     │\n"
            "│   User (Owner), Group, and Others.                                           │\n"
            "│ • The three permissions represent octal numbers:                             │\n"
            "│   r (Read) = 4  |  w (Write) = 2  |  x (Execute) = 1                          │\n"
            "│ • A script cannot execute unless the operating system sees the 'x' bit.      │\n"
            "│   'chmod 755' gives the owner rwx (4+2+1=7) and everyone else r-x (4+1=5).   │\n"
            "│   'chmod 644' sets rw-r--r-- (ideal for read-only configs like phoenix.conf).│\n"
            "└──────────────────────────────────────────────────────────────────────────────┘"
        ),
        "MALWARE_TERMINATED": (
            "┌──────────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Process Signaling (kill -15 vs kill -9)                  │\n"
            "├──────────────────────────────────────────────────────────────────────────────┤\n"
            "│ What you fixed in the game:                                                  │\n"
            "│ You used 'kill -9' to eliminate a rogue process that ignored shutdown.       │\n"
            "│                                                                              │\n"
            "│ How real Linux systems handle this:                                          │\n"
            "│ • In Linux, the 'kill' command does not simply delete a program; it sends an │\n"
            "│   asynchronous signal to a Process ID (PID).                                 │\n"
            "│ • SIGTERM (Signal 15) is a polite termination request. The application can   │\n"
            "│   trap the signal, flush caches, close database sockets, or even ignore it.  │\n"
            "│ • SIGKILL (Signal 9) cannot be caught, handled, or ignored by any program.   │\n"
            "│   The kernel immediately intercepts Signal 9, halts program execution, and  │\n"
            "│   reclaims its memory pages unconditionally.                                 │\n"
            "└──────────────────────────────────────────────────────────────────────────────┘"
        ),
        "NETWORK_ONLINE": (
            "┌──────────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Network Tooling & Interface Management (ip / ping)       │\n"
            "├──────────────────────────────────────────────────────────────────────────────┤\n"
            "│ What you fixed in the game:                                                  │\n"
            "│ You brought up interface 'osiris0' with 'ip link' and tested the gateway.     │\n"
            "│                                                                              │\n"
            "│ How real Linux systems handle this:                                          │\n"
            "│ • Modern Linux distributions deprecate old net-tools ('ifconfig') in favor   │\n"
            "│   of the iproute2 suite: 'ip addr', 'ip link', and 'ip route'.               │\n"
            "│ • 'ip link set <DEV> up' activates the network layer and driver queues.      │\n"
            "│ • 'ping -c <N>' sends ICMP ECHO_REQUEST packets to measure round-trip time   │\n"
            "│   and verify end-to-end IP reachability before starting services.            │\n"
            "└──────────────────────────────────────────────────────────────────────────────┘"
        ),
        "PHOENIX_ONLINE": (
            "┌──────────────────────────────────────────────────────────────────────────────┐\n"
            "│ [TAKE IT TO LINUX]: Network Sockets & Service Auditing (ss / listening ports) │\n"
            "├──────────────────────────────────────────────────────────────────────────────┤\n"
            "│ What you fixed in the game:                                                  │\n"
            "│ You launched the PHOENIX daemon and verified listening sockets with 'ss'.    │\n"
            "│                                                                              │\n"
            "│ How real Linux systems handle this:                                          │\n"
            "│ • Network sockets represent endpoints binding an IP address to a TCP/UDP     │\n"
            "│   port number (e.g. 127.0.0.1:8080).                                         │\n"
            "│ • 'ss -tulpn' directly dumps kernel socket tables:                           │\n"
            "│   -t (TCP) | -u (UDP) | -l (Listening) | -p (Show PID) | -n (Numeric ports). │\n"
            "│ • Chaining 'ss' with 'grep' allows operators to immediately determine if a   │\n"
            "│   service daemon is successfully bound to its assigned port.                 │\n"
            "└──────────────────────────────────────────────────────────────────────────────┘"
        )
    }

    TITLES: Dict[str, str] = {
        "BUFFER_REPAIRED": "Terminal Line Disciplines & Input Buffering",
        "BASHRC_RESTORED": "Standard Output Redirection (> and >>)",
        "LOGS_AUDITED": "Log Triaging & Stream Filtering (grep / tail)",
        "FIND_UNLOCKED": "POSIX Permissions & Execution Bits",
        "MALWARE_TERMINATED": "Process Signaling (kill -15 vs kill -9)",
        "NETWORK_ONLINE": "Network Tooling & Interface Management (ip / ping)",
        "PHOENIX_ONLINE": "Network Sockets & Service Auditing (ss / listening ports)",
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
