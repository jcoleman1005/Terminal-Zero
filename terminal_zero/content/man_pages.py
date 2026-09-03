from typing import Dict

MAN_PAGES: Dict[str, str] = {
    "ls": "NAME\n    ls - list directory contents\n\nSYNOPSIS\n    ls [-a] [-l] [FILE]...\n\nEXAMPLES\n    ls -la /var/log\n    ls -a ~\n",
    "ll": "NAME\n    ll - shell alias for 'ls -la'\n\nSYNOPSIS\n    ll [FILE]...\n\nDESCRIPTION\n    Custom shell shortcut defined in ~/.bashrc to list files in long format including hidden files.\n\nEXAMPLES\n    ll\n    ll /var/log\n",
    "cd": "NAME\n    cd - change the working directory\n\nSYNOPSIS\n    cd [DIRECTORY]\n\nEXAMPLES\n    cd /opt/phoenix\n    cd ..\n",
    "cat": "NAME\n    cat - concatenate files and print on the standard output\n\nSYNOPSIS\n    cat [FILE]...\n\nEXAMPLES\n    cat /home/alice/README.txt\n",
    "head": "NAME\n    head - output the first part of files\n\nSYNOPSIS\n    head [-n LINES] [FILE]...\n\nEXAMPLES\n    head -n 5 /var/log/system.log\n",
    "tail": "NAME\n    tail - output the last part of files\n\nSYNOPSIS\n    tail [-n LINES] [-f] [FILE]...\n\nEXAMPLES\n    tail -n 20 /var/log/system.log\n    tail -f /var/log/syslog\n",
    "grep": (
        "NAME\n"
        "    grep - print lines that match patterns\n\n"
        "SYNOPSIS\n"
        "    grep [OPTION]... PATTERN [FILE]...\n\n"
        "DESCRIPTION\n"
        "    grep searches input files for lines containing a match to the given PATTERN.\n"
        "    A PATTERN is a keyword, search string, or expression you want to isolate.\n"
        "    Matching lines are printed to standard output.\n\n"
        "OPTIONS\n"
        "    -i, --ignore-case\n"
        "        Ignore case distinctions in patterns and input data (e.g. 'ALERT' matches 'alert').\n\n"
        "    -v, --invert-match\n"
        "        Invert the sense of matching, selecting lines that do NOT match the pattern.\n\n"
        "    -n, --line-number\n"
        "        Prefix each line of output with its 1-based line number within the file.\n\n"
        "    -r, --recursive\n"
        "        Read all files under each directory, recursively.\n\n"
        "EXAMPLES\n"
        "    grep -i 'alert' /var/log/auth.log\n"
        "    grep -i 'miner' /var/log/syslog\n"
        "    grep -v 'systemd' /var/log/syslog\n"
        "    grep -r 'PHOENIX' /opt\n"
    ),
    "manuals": "NAME\n    manuals - index recovered field manuals and cheat sheets\n\nSYNOPSIS\n    manuals\n\nDESCRIPTION\n    Displays a catalog of all discovered operational guides, cheat sheets, and field notes that have been read with 'cat'.\n",
    "docs": "NAME\n    docs - alias for manuals\n\nSYNOPSIS\n    docs\n",
    "find": "NAME\n    find - search for files in a directory hierarchy\n\nSYNOPSIS\n    find [PATH] -name PATTERN [-type f|d]\n\nEXAMPLES\n    find / -name '*.sh'\n    find /home/alice -type f\n",
    "chmod": "NAME\n    chmod - change file mode bits\n\nSYNOPSIS\n    chmod MODE FILE...\n\nEXAMPLES\n    chmod +x script.sh\n    chmod 755 /bin/tool\n    chmod 644 config.conf\n",
    "decrypt": "NAME\n    decrypt - Apollo diagnostic error translation daemon\n\nSYNOPSIS\n    decrypt\n\nDESCRIPTION\n    Analyzes the last stderr fault and emits plain-language recovery procedures.\n",
    "apollo-diagnostics": "NAME\n    apollo-diagnostics - Apollo diagnostic error translation daemon\n\nSYNOPSIS\n    apollo-diagnostics\n\nDESCRIPTION\n    Analyzes the last stderr fault and emits plain-language recovery procedures.\n",
    "sync": "NAME\n    sync - flush file system buffers\n\nSYNOPSIS\n    sync\n\nDESCRIPTION\n    Flushes in-memory buffers to persistent storage.\n",
    "ps": "NAME\n    ps - report a snapshot of the current processes\n\nSYNOPSIS\n    ps [aux] [-ef]\n\nEXAMPLES\n    ps aux\n    ps aux | grep miner\n",
    "kill": "NAME\n    kill - send a signal to a process\n\nSYNOPSIS\n    kill [-s sigspec | -n signum | -sigspec] pid...\n\nEXAMPLES\n    kill 104\n    kill -9 104\n    kill -15 210\n",
    "ip": "NAME\n    ip - show / manipulate routing, network devices, interfaces and tunnels\n\nSYNOPSIS\n    ip [addr | link | route] [COMMAND]\n\nEXAMPLES\n    ip addr\n    ip link set apollo0 up\n    ip route\n",
    "ss": "NAME\n    ss - another utility to investigate sockets\n\nSYNOPSIS\n    ss [-tulpn] [-t] [-u] [-l]\n\nEXAMPLES\n    ss -tulpn\n    ss -l\n",
    "ping": "NAME\n    ping - send ICMP ECHO_REQUEST to network hosts\n\nSYNOPSIS\n    ping [-c count] destination\n\nEXAMPLES\n    ping 10.0.42.1\n    ping -c 4 10.0.42.1\n",
    "echo": "NAME\n    echo - display a line of text\n\nSYNOPSIS\n    echo [STRING]...\n",
    "repair_buffer": "NAME\n    repair_buffer - patch terminal input ring buffer\n\nSYNOPSIS\n    repair_buffer\n",
    "phoenix_daemon": "NAME\n    phoenix_daemon - PHOENIX emergency restoration daemon\n\nSYNOPSIS\n    phoenix_daemon [start | --sync]\n",
    "phoenix_ctl": "NAME\n    phoenix_ctl - PHOENIX control utility\n\nSYNOPSIS\n    phoenix_ctl [COMMAND]\n",
    "apollo-net": "NAME\n    apollo-net - Apollo network interface diagnostic tool\n\nSYNOPSIS\n    apollo-net\n",
    "help": "NAME\n    help - display information about builtin recovery commands\n\nSYNOPSIS\n    help [command]\n\nDESCRIPTION\n    Provides emergency guidance and a list of essential shell utilities.\n",
    "restore": "NAME\n    restore - diegetic profile recovery advisory\n\nSYNOPSIS\n    restore [file]\n\nDESCRIPTION\n    Advisory on using redirection to restore template profiles from /opt/backup/profiles/.\n",
    "reboot": "NAME\n    reboot - restart workstation and reset recovery state\n\nSYNOPSIS\n    reboot\n\nDESCRIPTION\n    Flushes transient memory, removes save state, and restores workstation APOLLO to initial cold boot state.\n",
    "reset": "NAME\n    reset - reinitialize terminal and workstation state\n\nSYNOPSIS\n    reset\n\nDESCRIPTION\n    Alias for reboot.\n",
    "note": "NAME\n    note - record playtest feedback and observations\n\nSYNOPSIS\n    note MESSAGE...\n\nDESCRIPTION\n    Logs playtester notes directly to playtest_notes.txt with timestamps and sector data without requiring quotation marks.\n\nEXAMPLES\n    note I found the puzzle clear\n    note this error message is confusing\n",
    "feedback": "NAME\n    feedback - alias for note\n\nSYNOPSIS\n    feedback MESSAGE...\n",
    "taskctl": "NAME\n    taskctl - Apollo task checklist link and control daemon\n\nSYNOPSIS\n    taskctl [link]\n\nDESCRIPTION\n    Links /home/alice/TODO.txt to the active shell session, enabling the global 'todo' and 'tasks' shortcut commands.\n\nEXAMPLES\n    taskctl link\n",
    "todo": "NAME\n    todo - display active incident recovery checklist\n\nSYNOPSIS\n    todo\n\nDESCRIPTION\n    Prints current workstation recovery objectives from anywhere in the filesystem.\n",
    "tasks": "NAME\n    tasks - alias for todo\n\nSYNOPSIS\n    tasks\n",
    "triage_process": "NAME\n    triage_process - register rogue intruder process in incident dossier\n\nSYNOPSIS\n    triage_process <PID>\n\nEXAMPLES\n    triage_process 104\n",
    "triage_sector": "NAME\n    triage_sector - register tampered recovery sector in incident dossier\n\nSYNOPSIS\n    triage_sector <FILE_PATH>\n\nEXAMPLES\n    triage_sector /mnt/recovery/bin/recovery.sh\n",
    "triage_interface": "NAME\n    triage_interface - register degraded network interface in incident dossier\n\nSYNOPSIS\n    triage_interface <DEVICE_NAME>\n\nEXAMPLES\n    triage_interface apollo0\n",
    "triage_service": "NAME\n    triage_service - register terminated cluster daemon in incident dossier\n\nSYNOPSIS\n    triage_service <SERVICE_NAME>\n\nEXAMPLES\n    triage_service phoenix-sync.service\n",
}
