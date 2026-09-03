# Terminal Zero // Production Game Notes, Environmental Artifacts & Narrative Catalog

**Version:** 2.2-PROD

**Target:** Virtual Filesystem Image (`apollo-vfs-root`)

**Security Classification:** RESTRICTED // INCIDENT RESPONSE

---

## 1. Boot Screen & System Headers

### `/etc/motd`

```text
================================================================================
                    APOLLO WORKSTATION // KERNEL v5.19.0-24
================================================================================
 [ALERT] SYSTEM INTEGRITY COMPROMISED. AUTOMATIC QUARANTINE PROTOCOL ACTIVE.
 [ALERT] WAN LINK SEVERED. PRIMARY LINE DISCIPLINE DRIVERS CORRUPTED.
 
 Current Session: alice [CONSOLE TTY1]
 Security Context: RESTRICTED SANDBOX (/home/alice)

 Standard desktop services are offline. Terminal fallback active.
 Review local incident logs and recovery instructions in your home directory.
================================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/home/alice/diagnostics/BOOT_FAIL.log`

```text
[03:41:02.109] [KERNEL ALERT] Apollo Workstation Core Subsystem Degraded (Boot ID: 0x42-INIT).
[03:41:02.112] [ERR_TTY_RING] Input ring buffer desynchronized at line discipline layer.
[03:41:02.115] [HARDWARE FAULT] Interactive command recall (UP/DOWN arrow keys) suspended.
[03:41:02.120] [DIAGNOSTIC] Register mismatch in terminal driver ring registers.
[03:41:02.125] [ACTION REQUIRED] Run the maintenance utility 'repair_buffer' to recalibrate.

```

*(Permissions: `0644`, Owner: `alice:alice`)*

---

## 2. Phase 0: Cold Boot & Orientation (`/home/alice/`)

### `/home/alice/README.txt`

```text
// ============================================================================
// APOLLO WORKSTATION // EMERGENCY OPERATOR PROTOCOL
// ============================================================================
Alice—

If you're seeing this on your screen, the automated lockdown caught you at your
desk when the network dropped. Don't panic. The system put your terminal in a 
quarantine environment (/home/alice) so the attack couldn't touch your shell.

The desktop GUI is gone. You're going to have to drive this machine through the 
command line. 

Keep these three commands in your head right now:
  • 'pwd'            (Print Working Directory)
    Tells you where you are standing in the system tree.
  • 'ls'             (List)
    Shows you all visible files and folders in your current directory.
  • 'cat <filename>' (Concatenate / Read)
    Dumps the text inside a file right onto your screen.
    Example: cat README.txt

Your terminal driver took a direct hit on boot, which is why your Up/Down arrow 
keys aren't recalling previous commands. 

Inspect 'diagnostics/BOOT_FAIL.log' using 'cat' to see the exact fault, then 
run the recovery utility it specifies.

If a command fails or spits out an error you don't understand, type 'decrypt'.
I wrote it to catch whatever POSIX error the kernel just threw and translate 
the sysadmin jargon into plain English.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `alice:alice`)*

---

### `/home/alice/.note.txt`

```text
// STICKY NOTE TAPED TO MONITOR FRAME
Alice—

The attacker didn't just break the drivers; they tried to bury their tracks.

Once you fix the terminal buffer, remember that Unix hides system profiles 
and recovery caches behind a dot prefix (like this file: .note.txt). 

Plain 'ls' won't show them. You need to pass the '-a' (all) flag:
  ls -a

I left clean shell environment templates in the system backup directory:
  /opt/backup/profiles/

Follow the file path from the root directory ('/'). 
Tab autocompletion is dead until you restore your profile.

— Morgan

```

*(Permissions: `0644`, Owner: `alice:alice`)*

---

## 3. Phase 1: Shell Profile & Traversal (`/opt/backup/profiles/`)

### `/opt/backup/profiles/NOTE_FROM_MORGAN.txt`

```text
// ============================================================================
// INCIDENT SCRATCHPAD // APOLLO WORKSTATION // PRIORITY: HIGH
// HOST: apollo-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 03:42:11 AM
// FILE: /opt/backup/profiles/NOTE_FROM_MORGAN.txt
// ============================================================================

Alice—

Whoever hit our network knew exactly how to make an operator miserable.
They wiped out your user profile, which is why your shell feels unresponsive:
no search shortcuts, broken line discipline, and Tab autocompletion completely dead.

I saved a clean profile template here: 'alice.bashrc'.

To fix your environment, you need to dump this backup template directly 
into your home profile file at /home/alice/.bashrc using stream 
redirection (the '>' operator). 

Think of '>' as a one-way pipe directing output into a destination file:
  cat <SOURCE_FILE> > <DESTINATION_FILE>

Syntax rules:
1. Always put a space before and after the '>' operator.
2. If your destination is in another directory, specify the full path from root:
   /home/alice/.bashrc

Once that file is written, your Readline bindings will link back up. 
You'll get [TAB] autocompletion back so you never have to type long directory
paths by hand again.

I also added an alias for 'll' inside that profile. Use it. It runs 'ls -la'
under the hood, revealing file permissions and hidden dotfiles in one go.

I'm heading toward /var/log to see what kind of malware they dropped on us.
Fix your profile and meet me there.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/opt/backup/profiles/alice.bashrc`

```bash
# Clean Operator Profile for APOLLO Workstation (User: alice)
# Base environment initialization & Readline recovery
export PATH="/bin:/usr/bin:/opt/phoenix/bin"
export PS1="\u@apollo:\w\$ "

# Readline Ergonomics & Completion Hooks
bind 'set show-all-if-ambiguous on'
bind 'set completion-ignore-case on'
bind 'TAB:complete'

# System Aliases
alias ll='ls -la'
alias cls='clear'

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/home/alice/.bash_history`

```text
pwd
ls -la
cat diagnostics/BOOT_FAIL.log
repair_buffer
cat .note.txt
cd /opt/backup/profiles
cat NOTE_FROM_MORGAN.txt
cat alice.bashrc > /home/alice/.bashrc

```

*(Permissions: `0600`, Owner: `alice:alice`)*

---

## 4. Phase 2: Log Forensics & Triage (`/var/log/`)

### `/var/log/NOTE_FROM_MORGAN.txt`

```text
// ============================================================================
// INCIDENT SCRATCHPAD // APOLLO WORKSTATION // LOG TRIAGE
// HOST: apollo-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 04:22:08 AM
// FILE: /var/log/NOTE_FROM_MORGAN.txt
// ============================================================================

Alice—

They hit the authentication daemon hard. The compromise logged hundreds of
lines into 'auth.log', but it is far too long to read with 'cat'. If you dump
the whole file at once, it will flood your terminal and scroll past your screen.

You need to filter the noise to isolate where they breached the boundary.

Use stream inspection tools:
  • 'head -n <NUMBER> <FILE>'
    Reads only the specified number of lines from the top of a file.
  • 'tail -n <NUMBER> <FILE>'
    Reads only the most recent lines from the bottom of a file.
  • 'grep -i "<KEYWORD>" <FILE>'
    Scans a file and prints ONLY lines matching your search keyword.
    (The -i flag makes your search case-insensitive, matching 'ALERT' or 'alert').

Search 'auth.log' for breach signatures like "ALERT" or "rogue". 

Pay close attention to any Process IDs (PIDs) they spawned and any recovery 
partitions they tried to isolate. Once you know what they touched, we can 
reclaim the system.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/var/log/auth.log`

```text
[2042-10-11 03:00:12] apollo sshd[102]: Server listening on 0.0.0.0 port 22.
[2042-10-11 03:02:15] apollo login[115]: Accepted password for alice from 127.0.0.1.
[2042-10-11 03:15:22] apollo systemd[1]: Started User Manager for UID 1000.
[2042-10-11 03:22:40] apollo sudo[142]: alice : TTY=tty1 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/dmesg
[2042-10-11 03:38:19] apollo sshd[188]: Connection closed by authenticating user root 10.0.42.99 port 41220 [preauth]
[2042-10-11 03:40:02] apollo auth: PAM-WARN: Multiple authentication failures for user root from 10.0.42.99
[2042-10-11 03:41:45] apollo auth: ALERT-0x01: Ingress breach detected on line discipline TTY1.
[2042-10-11 03:42:01] apollo kernel: ALERT-0x01: Rogue miner deployed -> PID: 104 (sys_miner) in /tmp.
[2042-10-11 03:42:15] apollo kernel: ALERT-0x02: Recovery binary stripped -> /mnt/recovery/bin/recovery.sh (mode 0000).
[2042-10-11 03:42:30] apollo kernel: ALERT-0x03: apollo0 link state degraded -> Device: apollo0 (link: DOWN).
[2042-10-11 03:42:48] apollo kernel: ALERT-0x04: phoenix-sync daemon failed -> phoenix-sync terminated by signal 9.
[2042-10-11 03:43:00] apollo auth: Emergency containment active. User session sandboxed.

```

*(Permissions: `0640`, Owner: `root:adm`)*

---

## 5. Phase 3: Recovery Partition & Search (`/mnt/recovery/`)

### `/mnt/recovery/NOTE_FROM_MORGAN.txt`

```text
// ============================================================================
// INCIDENT SCRATCHPAD // APOLLO WORKSTATION // RECOVERY MOUNT
// HOST: apollo-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 05:10:44 AM
// FILE: /mnt/recovery/NOTE_FROM_MORGAN.txt
// ============================================================================

Alice—

Before the quarantine locked me out, I mirrored our fallback tools and cluster
authorization keys to this partition (/mnt/recovery). 

The problem: the automated unmount scramble threw directory branches all over
the place. Hunting through every subfolder by hand with 'cd' and 'ls' will take
hours we don't have.

Use the recursive search utility 'find':
  find <START_DIRECTORY> -name "<SEARCH_PATTERN>" -type f

How it works:
  • <START_DIRECTORY> : Where to begin searching (use '.' for here, or '/mnt/recovery').
  • -name "<PATTERN>" : The filename you want. You can use wildcards like "*.sh" or "*.key".
  • -type f           : Restricts the output to regular files (ignoring folders).

We need two critical assets from this partition:
1. Our subsystem recovery shell script (ends in .sh).
2. The cryptographic PHOENIX access token (ends in .key).

Locate them. If you need full option lists for the search utility, run 'man find'.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/mnt/recovery/keys/phoenix.key`

```text
-----BEGIN PHOENIX CLUSTER AUTHORIZATION TOKEN-----
AUTH_TOKEN=PX-KEY-7701-ALPHA-SIGINT-TRAP-VECTOR-ENABLED
CLUSTER_ID=APOLLO-GRID-01
ISSUED=2042-10-11T03:30:00Z
SIGNATURE=d8e8fca2dc018b63b7e411b9802de922c091ad55
-----END PHOENIX CLUSTER AUTHORIZATION TOKEN-----

```

*(Permissions: `0600`, Owner: `root:root`)*

---

## 6. Phase 4: Permissions & Process Supervision (`/mnt/recovery/bin/` & `/tmp/`)

### `/mnt/recovery/bin/PERMISSIONS_NOTE.txt`

```text
// ============================================================================
// INCIDENT SCRATCHPAD // APOLLO WORKSTATION // SECURITY LOCKDOWN
// HOST: apollo-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 05:45:19 AM
// FILE: /mnt/recovery/bin/PERMISSIONS_NOTE.txt
// ============================================================================

Alice—

The containment protocol panicked and zeroed the permission mode bits on 
'recovery.sh'. Inspect it with 'ls -l' and you'll see:
  ---------- 1 root root recovery.sh

Linux will not execute any file unless its execute bit ('x') is explicitly 
flipped on. If you try to run it right now (./recovery.sh), the shell will 
refuse with 'Permission denied'.

You have to grant execution rights using 'chmod' (Change Mode):
  chmod +x <FILE_PATH>

Alternatively, you can set full standard permissions numerically:
  chmod 755 <FILE_PATH>
  (7 = Read/Write/Execute for Owner, 5 = Read/Execute for Group & Others)

Once 'recovery.sh' has execute bits, run it with:
  ./recovery.sh
(The './' tells the terminal: "look in the directory I am currently standing in".)

Executing this script restores our kernel signal traps. Once it completes, you'll
get Ctrl+C (SIGINT) back so you can break out of hung processes.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/mnt/recovery/bin/recovery.sh`

```bash
#!/bin/bash
# APOLLO WORKSTATION // SUBSYSTEM RESTORATION SCRIPT
# Re-links kernel signal handlers and line disciplines.

echo "[RECOVERY]: Probing line discipline vector registers..."
sleep 0.5
echo "[RECOVERY]: Restoring trap handler for SIGINT (Signal 2 / Ctrl+C)..."
sleep 0.5
echo "[SUCCESS]: Kernel signal table recalibrated. Interactive break handling online."

```

*(Permissions: `0000`, Owner: `root:root` -> Modified by player to `0755`)*

---

### `/tmp/NOTE_FROM_MORGAN.txt`

```text
// ============================================================================
// INCIDENT SCRATCHPAD // APOLLO WORKSTATION // PROCESS REMEDIATION
// HOST: apollo-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 06:15:33 AM
// FILE: /tmp/NOTE_FROM_MORGAN.txt
// ============================================================================

Alice—

Our CPU thermal alarm is firing. The intruder dropped a persistent background
miner into /tmp (sys_miner) that is consuming nearly 100% of our compute cycles
and locking socket memory.

Ctrl+C works for foreground programs, but this miner is running detached in the
background. You have to locate it in the system process table and stop it directly.

1. Inspect active processes:
   ps aux
   (Look for the program burning ~98% CPU and note its Process ID / PID).

2. Do not bother with a polite termination request:
   kill -15 <PID>
   The miner was designed to intercept and ignore standard SIGTERM (Signal 15) signals.

3. Use the unconditional kernel termination signal:
   kill -9 <PID>
   SIGKILL (Signal 9) cannot be caught, ignored, or blocked. The Linux kernel 
   will forcefully drop the process from the process table.

Kill the miner so our CPU cools down and frees up the network stack.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

## 7. Phase 5: Network Interfaces & Gateway (`/etc/network/`)

### `/etc/network/NOTE_FROM_MORGAN.txt`

```text
// ============================================================================
// INCIDENT SCRATCHPAD // APOLLO WORKSTATION // NETWORK RECOVERY
// HOST: apollo-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 06:50:02 AM
// FILE: /etc/network/NOTE_FROM_MORGAN.txt
// ============================================================================

Alice—

The miner is dead and CPU load is back to normal, but the machine is still 
isolated. The attack toggled our primary network adapter off at the driver level.

Check the hardware definitions in 'interfaces' using 'cat'.

You'll see our interface name is 'apollo0' and our local subnet gateway is 
located at 10.0.42.1.

To restore connectivity:
1. Inspect the current adapter link state:
   ip addr
2. Bring the physical interface link online:
   ip link set <DEVICE_NAME> up
3. Verify that network packets can actually reach the gateway:
   ping -c 4 <GATEWAY_IP>
   (The '-c 4' flag tells ping to send exactly 4 test packets and stop).

Once the ping probe confirms packet round-trips to 10.0.42.1, the network
uplink is secure. Meet me at /etc/phoenix for the finale.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/etc/network/interfaces`

```text
# APOLLO WORKSTATION NETWORK INTERFACE CONFIGURATION
# Local loopback interface
auto lo
iface lo inet loopback

# Primary Ethernet uplink (Degraded by automated containment)
# Hardware MAC: 52:54:00:12:34:56
auto apollo0
iface apollo0 inet static
    address 10.0.42.15/24
    gateway 10.0.42.1
    dns-nameservers 10.0.42.1

```

*(Permissions: `0644`, Owner: `root:root`)*

---

## 8. Phase 6: Phoenix Cluster Restoration (`/etc/phoenix/`)

### `/etc/phoenix/NOTE_FROM_MORGAN.txt`

```text
// ============================================================================
// INCIDENT SCRATCHPAD // APOLLO WORKSTATION // PHOENIX CLUSTER DAEMON
// HOST: apollo-ws-01 | USER: morgan [SYSADMIN] | TIMESTAMP: 07:35:14 AM
// FILE: /etc/phoenix/NOTE_FROM_MORGAN.txt
// ============================================================================

Alice—

This is it. The gateway is reachable and the workstation is stable. 
The final step is bringing the PHOENIX cluster restoration daemon online.

The daemon reads its configuration from 'phoenix.conf', but it's currently 
missing its authorization token.

CRITICAL SYNTAX WARNING:
You need to append the key you found earlier (/mnt/recovery/keys/phoenix.key)
to the bottom of 'phoenix.conf'.
  • A single '>' OVERWRITES the file, erasing all the listener settings.
  • A double '>>' APPENDS the data cleanly to the end of the file.

Syntax Template:
  cat <SOURCE_KEY_FILE> >> <DESTINATION_CONFIG_FILE>

(If you accidentally overwrite the file, do not panic: I left a pristine backup
template at /etc/phoenix/phoenix.conf.default).

After appending the key:
1. Secure the configuration permissions. The daemon will refuse to start if the
   file is world-writable. Set it to read-only for others:
   chmod 644 /etc/phoenix/phoenix.conf

2. Launch the restoration daemon:
   phoenix_daemon start

3. Verify that the daemon socket is actively listening on port 8080:
   ss -tulpn | grep 8080

You brought this terminal back from zero, Alice. Bring us home.

— Morgan
// ============================================================================

```

*(Permissions: `0644`, Owner: `root:root`)*

---

### `/etc/phoenix/phoenix.conf`

```text
# PHOENIX EMERGENCY CLUSTER RESTORATION DAEMON CONFIG
LISTEN_ADDR=127.0.0.1
LISTEN_PORT=8080
GATEWAY_TARGET=10.0.42.1
LOG_LEVEL=VERBOSE
FAILOVER_MODE=AUTONOMOUS
# --- APPEND BEARER TOKEN BELOW ---

```

*(Permissions: `0600`, Owner: `root:root` -> Modified by player to `0644`)*

---

### `/etc/phoenix/phoenix.conf.default`

```text
# PHOENIX EMERGENCY CLUSTER RESTORATION DAEMON CONFIG (FAILSAFE BACKUP)
LISTEN_ADDR=127.0.0.1
LISTEN_PORT=8080
GATEWAY_TARGET=10.0.42.1
LOG_LEVEL=VERBOSE
FAILOVER_MODE=AUTONOMOUS
# --- APPEND BEARER TOKEN BELOW ---

```

*(Permissions: `0644`, Owner: `root:root`)*

---

## 9. Dynamic System Telemetry & Tracking

### `/home/alice/diagnostics/INCIDENT_REPORT.log`

*(Rendered dynamically via `get_incident_dossier()` based on `CLUE_SIGNATURES` in `/var/log/auth.log`)*

```text
================================================================================
        APOLLO WORKSTATION // INCIDENT RECOVERY DOSSIER [{STATUS_HEADER}]
================================================================================
 [ALERT-0x01] INTRUDER PROCESS : Attacker deployed rogue miner -> {c1}
 [ALERT-0x02] TAMPERED SECTOR  : Core recovery binary stripped   -> {c2}
 [ALERT-0x03] HARDWARE STATUS  : Network interface knocked DOWN  -> {c3}
 [ALERT-0x04] DAEMON STATUS    : Cluster service terminated      -> {c4}
================================================================================
INVESTIGATION DIRECTIVE: Audit compromised logs in /var/log/ with 'head',
'tail', or 'grep' to confirm matching breach signatures.
================================================================================

```

*(Dynamic formatting: Unmasked entries render green; missing entries render dimmed `[ REDACTED ]`)*

---

### `/home/alice/TODO.txt`

*(Generated dynamically by runtime engine to match active `SYSTEM_FLAGS`)*

```text
================================================================================
               APOLLO WORKSTATION // INCIDENT RECOVERY CHECKLIST
================================================================================
[{p0}] PHASE 0: COLD BOOT & MEMORY RECALL
    • [{p0_1}] Inspect diagnostics/BOOT_FAIL.log for ring buffer fault
    • [{p0_2}] Execute 'repair_buffer' to restore command history (Up/Down keys)

[{p1}] PHASE 1: USER SHELL ENVIRONMENT
    • [{p1_1}] Locate backup profile template in /opt/backup/profiles/
    • [{p1_2}] Redirect clean config into ~/.bashrc to unlock Tab autocompletion

[{p2}] PHASE 2: INCIDENT LOG FORENSICS
    • [{p2_1}] Audit security logs in /var/log/ with 'tail' or 'grep'
    • [{p2_2}] Identify breach signatures and unmask dossier leads

[{p3}] PHASE 3: RECOVERY PARTITION & RECURSIVE SEARCH
    • [{p3_1}] Use 'find' in /mnt/recovery to locate recovery script and cluster key
    • [{p3_2}] Grant execute permissions ('chmod +x') to /mnt/recovery/bin/recovery.sh
    • [{p3_3}] Run './recovery.sh' to link signal handlers and unlock Ctrl+C

[{p4}] PHASE 4: PROCESS SUPERVISOR & ROGUE MINER
    • [{p4_1}] Audit process table with 'ps aux' to locate high-CPU rogue worker
    • [{p4_2}] Force-terminate miner process using unconditional signal ('kill -9')

[{p5}] PHASE 5: NETWORK HARDWARE & GATEWAY UPLINK
    • [{p5_1}] Inspect interface definitions in /etc/network/interfaces
    • [{p5_2}] Bring physical interface 'apollo0' online via 'ip link'
    • [{p5_3}] Verify gateway reachability with ping probe ('ping -c 4 10.0.42.1')

[{p6}] PHASE 6: CLUSTER SUPERVISOR DAEMON
    • [{p6_1}] Safely append cluster key into /etc/phoenix/phoenix.conf using '>>'
    • [{p6_2}] Lock down configuration permissions ('chmod 644')
    • [{p6_3}] Launch 'phoenix_daemon start' and verify listener socket on port 8080
================================================================================
[STATUS]: Type 'todo' from any folder to review active workstation objectives.
================================================================================

```

*(Permissions: `0644`, Owner: `alice:alice`)*

---

## 10. Victory Sequence & System Debrief

### Terminal Victory Emulation (Triggered upon `PHOENIX_ONLINE = True`)

```text
[PHOENIX-DAEMON]: Handshake verified with gateway node 10.0.42.1:8080.
[PHOENIX-DAEMON]: Ingress routing tables broadcasted across subnet.
[PHOENIX-DAEMON]: Workstation APOLLO verified as AUTHENTIC ROOT CLUSTER NODE.

================================================================================
                        APOLLO WORKSTATION RECOVERED
================================================================================
  All local subsystems operational. Global mesh synchronization initialized.
  Workstation containment lifted. Terminal session secured.
================================================================================

[INCOMING SYSTEM BROADCAST // MORGAN]
"Alice... the gateway just responded. The entire Phoenix mesh is lighting up 
across the northern grid. 

I don't know who you were before this system crashed, but you just audited logs, 
re-linked POSIX line disciplines, managed processes, and brought a dead 
infrastructure cluster back to life from a raw command prompt.

Take a breath. You're no longer typing in the dark. 

I'll see you on the network."

```

*(Emitted to stdout prior to Field Guide summary)*

---

## 11. "Take It to Linux" Field Guide Reference Cards

These modules unlock dynamically in the system manual reader (`manuals` / `fieldguide`) as milestones resolve:

### Vault Card 01: Line Disciplines & Input Buffering

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [TAKE IT TO LINUX]: Terminal Line Disciplines & Input Buffering              │
├──────────────────────────────────────────────────────────────────────────────┤
│ What you fixed in the game:                                                  │
│ You ran 'repair_buffer' to restore your Up and Down arrow key history.       │
│                                                                              │
│ How real Linux systems handle this:                                          │
│ • Terminal Emulators communicate with the Linux kernel through a software    │
│   layer called the TTY Line Discipline.                                      │
│ • In 'cooked mode', the line discipline buffers characters until Enter is    │
│   pressed, allowing backspace editing. In 'raw mode', characters pass        │
│   directly to the program.                                                   │
│ • Arrow key command history is managed in user-space by GNU Readline.        │
│   Readline saves previous entries to a hidden file (~/.bash_history) and     │
│   navigates them via terminal escape sequences.                              │
└──────────────────────────────────────────────────────────────────────────────┘

```

*(Triggered by: `BUFFER_REPAIRED = True`)*

---

### Vault Card 02: Stream Redirection (`>` vs `>>`)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [TAKE IT TO LINUX]: Standard Output Redirection (> and >>)                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ What you fixed in the game:                                                  │
│ You used '>' to restore ~/.bashrc and '>>' to append a cryptographic key.    │
│                                                                              │
│ How real Linux systems handle this:                                          │
│ • Every Linux process has three standard data streams: Standard Input        │
│   (stdin / fd 0), Standard Output (stdout / fd 1), and Standard Error        │
│   (stderr / fd 2).                                                           │
│ • The single right arrow '>' redirects stdout into a file, completely        │
│   TRUNCATING (erasing) any previous content inside that file.                │
│ • The double right arrow '>>' opens the destination file in APPEND mode,      │
│   writing new data strictly after the final line without touching old data.  │
└──────────────────────────────────────────────────────────────────────────────┘

```

*(Triggered by: `BASHRC_RESTORED = True`)*

---

### Vault Card 03: File Mode Bits & Execution Rights (`chmod`)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [TAKE IT TO LINUX]: POSIX Permissions & Execution Bits                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ What you fixed in the game:                                                  │
│ You used 'chmod +x' to make a recovery script runnable.                       │
│                                                                              │
│ How real Linux systems handle this:                                          │
│ • Unix filesystems store access rights in mode bits split into triplets:     │
│   User (Owner), Group, and Others.                                           │
│ • The three permissions represent octal numbers:                             │
│   r (Read) = 4  |  w (Write) = 2  |  x (Execute) = 1                          │
│ • A script cannot execute unless the operating system sees the 'x' bit.      │
│   'chmod 755' gives the owner rwx (4+2+1=7) and everyone else r-x (4+1=5).   │
│   'chmod 644' sets rw-r--r-- (ideal for read-only configs like phoenix.conf).│
└──────────────────────────────────────────────────────────────────────────────┘

```

*(Triggered by: `SIGINT_UNLOCKED = True`)*

---

### Vault Card 04: Process Signals (`SIGTERM` vs `SIGKILL`)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [TAKE IT TO LINUX]: Process Signaling (kill -15 vs kill -9)                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ What you fixed in the game:                                                  │
│ You used 'kill -9' to eliminate a rogue process that ignored shutdown.       │
│                                                                              │
│ How real Linux systems handle this:                                          │
│ • In Linux, the 'kill' command does not simply delete a program; it sends an │
│   asynchronous signal to a Process ID (PID).                                 │
│ • SIGTERM (Signal 15) is a polite termination request. The application can   │
│   trap the signal, flush caches, close database sockets, or even ignore it.  │
│ • SIGKILL (Signal 9) cannot be caught, handled, or ignored by any program.   │
│   The kernel immediately intercepts Signal 9, halts program execution, and  │
│   reclaims its memory pages unconditionally.                                 │
└──────────────────────────────────────────────────────────────────────────────┘

```

*(Triggered by: `MALWARE_TERMINATED = True`)*

---

### Vault Card 05: Modern Network State & Socket Auditing

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [TAKE IT TO LINUX]: Network Tooling & Socket Inspection                      │
├──────────────────────────────────────────────────────────────────────────────┤
│ What you fixed in the game:                                                  │
│ You brought up an interface with 'ip link' and verified listeners with 'ss'. │
│                                                                              │
│ How real Linux systems handle this:                                          │
│ • Modern Linux distributions deprecate old net-tools ('ifconfig', 'netstat')  │
│   in favor of the iproute2 suite: 'ip addr', 'ip link', and 'ip route'.      │
│ • Network sockets represent communication endpoints binding an IP address to │
│   a TCP/UDP port number.                                                     │
│ • 'ss -tulpn' directly dumps kernel socket tables:                           │
│   -t (TCP) | -u (UDP) | -l (Listening) | -p (Show PID) | -n (Numeric ports).  │
│ • Chaining 'ss' with 'grep' allows operators to immediately determine if a   │
│   service daemon is successfully bound to its assigned port.                 │
└──────────────────────────────────────────────────────────────────────────────┘

```

*(Triggered by: `PHOENIX_ONLINE = True`)*