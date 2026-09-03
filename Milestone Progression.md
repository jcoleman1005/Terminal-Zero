## Complete Milestone Progression Specification (Milestones 0 – 7)

---

### Milestone 0: Cold Boot (Orientation & Buffer Repair)

* **Milestone ID & Name**: Milestone 0: Cold Boot (Orientation, Buffer Repair & Narrative Ingress)


* **Primary CLI Focus**: `pwd`, `ls`, `cat`, and running the in-path recovery binary `repair_buffer`.


* **System Capability Unlocked**: Command History Navigation (Up/Down Arrow Ergonomics via `unlocked_ergonomics["history"] = True`).


* **Flags Evaluated & Set**:
* *Prerequisites*: None (Initial System State).


* *Post-Resolution*: `SYSTEM_FLAGS["BUFFER_REPAIRED"] = True`.





```
[Cold Boot MOTD: "Run 'ls' or inspect 'README.txt'"]
                        │
                        ▼
    [Action: ls] ──► List directory contents
                        │
                        ▼
      [Artifact: BOOT_FAIL.log & README.txt]
                        │
                        ▼
 [Action: cat README.txt] ──► Learn 'cat <file>' syntax & read operator notes
                        │
                        ▼
 [Action: cat BOOT_FAIL.log] ──► Discover desynced ring buffer fault
                        │
                        ▼
      [Action: repair_buffer] ──► Synchronize input line discipline registers[cite: 1, 2]
                        │
                        ▼
   [Resolution: BUFFER_REPAIRED = True] ──► Unlocks Command History[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/home/alice`, `/var/log`, `/bin`, `/usr/bin`.


* `/home/alice/BOOT_FAIL.log` (`0644`, `alice:alice`):
```text
[KERNEL ALERT] Apollo Core Subsystem Degraded (Boot ID: 0x42-INIT).
[ERR_TTY_RING] Input ring buffer desynchronized at line discipline layer.
[DIAGNOSTIC] Interactive command recall (UP/DOWN keys) disabled to prevent buffer overflow.
[ACTION REQUIRED] Run the command 'repair_buffer' to recalibrate the TTY ring registers.

```


* `/home/alice/README.txt` (`0644`, `alice:alice`):
```text
================================================================================
                    APOLLO WORKSTATION RECOVERY TERMINAL
================================================================================
BASIC NAVIGATION CHEAT SHEET:
  • ls             : Lists visible files in your current working directory.
  • cat <filename> : Prints readable text inside a target file to screen.
  • pwd            : Prints your current working directory location.
  • decrypt        : Run after any error to get human-readable troubleshooting.
  • sync           : Saves machine state to persistent disk.

OPERATOR INCIDENT NOTE:
  1. Inspect 'BOOT_FAIL.log' using 'cat' to diagnose initial hardware failure.
  2. Hidden files start with a dot (.) and require 'ls -a'.
================================================================================

```


* `/usr/bin/repair_buffer` (`0755`, `root:root`): In-path recovery binary.



**Step-by-Step Clue Path**

1. Read the MOTD hint and run `ls`.


2. Run `cat README.txt` to learn file reading syntax.
3. Run `cat BOOT_FAIL.log` to inspect the ring buffer failure.
4. Run `repair_buffer` to clear the fault, unlock history navigation, and trigger the debrief panel.



**Failure Modes & Edge Cases**

* Running `cat` without arguments returns `cat: missing file operand` (Exit Code 1).


* Pressing Up/Down arrow prior to repair prints: `[HARDWARE ERROR]: Input ring buffer desynchronized. Command history unavailable.`


---

### Milestone 1: The Operator's Cache (Traversal & Shell Config)

* **Milestone ID & Name**: Milestone 1: The Operator's Cache (Traversal & Shell Config)


* **Primary CLI Focus**: `ls -a`, `cd`, `cat`, relative/absolute path traversal, and output redirection (`>`).


* **System Capability Unlocked**: Tab Autocompletion (`unlocked_ergonomics["autocomplete"] = True`, `unlocked_ergonomics["tab_completion"] = True`).


* **Flags Evaluated & Set**:
* *Prerequisites*: `SYSTEM_FLAGS["BUFFER_REPAIRED"] == True`.


* *Post-Resolution*: `SYSTEM_FLAGS["BASHRC_RESTORED"] = True`.





```
[Prerequisite: BUFFER_REPAIRED = True]
                  │
                  ▼
   [Action: ls -a in /home/alice] ──► Reveal hidden files (.note.txt, .bash_history)[cite: 1]
                  │
                  ▼
 [Artifact: /home/alice/.note.txt] ──► Read Morgan's scratchpad on redirection & backup path[cite: 1]
                  │
                  ▼
 [Action: cd /opt/backup/profiles || cat /opt/backup/profiles/CHEAT_SHEET.txt][cite: 1]
                  │
                  ▼
 [Action: cat /opt/backup/profiles/alice.bashrc > ~/.bashrc] ──► Stream redirection[cite: 1, 2]
                  │
                  ▼
 [Resolution: BASHRC_RESTORED = True] ──► Unlock Tab Autocompletion + Debrief Panel[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/home/alice`, `/opt/backup/profiles`, `/etc/skel`.


* `/home/alice/.note.txt` (`0644`, `alice:alice`):
```text
[MORGAN'S LOG - 03:14 AM]
Line discipline is trashed and autocomplete dropped offline.
1. Don't forget that dotfiles are hidden. Use 'ls -a'.
2. Use output redirection ('>') to pipe file streams: cat <source> > <target>
3. Clean backup configs are stored in /opt/backup/profiles/.
Follow the trail of CHEAT_SHEET.txt files across /opt and /var.

```


* `/opt/backup/profiles/CHEAT_SHEET.txt` (`0644`, `root:root`):
```text
================================================================================
                    OPERATOR TRAIL: PROFILE RESTORATION
================================================================================
SYNTAX CHEAT SHEET:
  • cd <path>                 : Navigate to target directory.
  • cat <src> > <destination> : Overwrite the destination file with the source.

TO RESTORE ALICE'S ENVIRONMENT:
  cat /opt/backup/profiles/alice.bashrc > /home/alice/.bashrc
================================================================================

```


* `/opt/backup/profiles/alice.bashrc` (`0644`, `root:root`): Backup readline configuration.



**Step-by-Step Clue Path**

1. Run `ls -a` in `/home/alice` to find `.note.txt` and `.bash_history`.


2. Run `cat .note.txt` to locate backup templates in `/opt/backup/profiles/`.


3. Run `cd /opt/backup/profiles` and `cat CHEAT_SHEET.txt`.
4. Run `cat /opt/backup/profiles/alice.bashrc > /home/alice/.bashrc` to restore autocomplete.



**Failure Modes & Edge Cases**

* Running `cp` returns `bash: cp: command not found`; `decrypt` advises using stream redirection (`cat <src> > <dest>`).


* Pressing Tab prior to solving outputs: `[HARDWARE ERROR]: Readline profile missing. Autocompletion unavailable.`


---

### Milestone 2: Forensic Log Analysis (Text Filtering)

* **Milestone ID & Name**: Milestone 2: Forensic Log Analysis (Text Filtering & Incident Triage)


* **Primary CLI Focus**: `cd`, `ls`, `cat`, `head`, `tail`, `grep` (`-i`, `-n`, `-v`), and single-stage piping (`|`).


* **System Capability Unlocked**: Systemic context and breach awareness needed to inspect `/mnt/recovery` and rogue processes.


* **Flags Evaluated & Set**:
* *Prerequisites*: `SYSTEM_FLAGS["BASHRC_RESTORED"] == True`.


* *Post-Resolution*: `SYSTEM_FLAGS["LOGS_AUDITED"] = True`.





```
[Prerequisite: BASHRC_RESTORED = True]
                  │
                  ▼
      [Action: cd /var/log] ──► Navigate to system log repository[cite: 1]
                  │
                  ▼
 [Artifact: /var/log/NOTE.txt & CHEAT_SHEET.txt] ──► Learn head, tail, grep & piping[cite: 1, 2]
                  │
                  ▼
 [Action: grep -i "failed" auth.log | tail -n 5] ──► Isolate breach vector & rogue binary[cite: 1, 2]
                  │
                  ▼
 [Clue Discovered: Rogue /tmp/sys_miner & unmounted volume /mnt/recovery][cite: 1, 2]
                  │
                  ▼
 [Resolution: LOGS_AUDITED = True] ──► Save checkpoint & emit Debrief Panel[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/var/log`, `/tmp`, `/mnt/recovery`.


* `/var/log/NOTE.txt` (`0644`, `root:root`):
```text
[MORGAN'S LOG - 04:22 AM]
The intrusion hit through the TTY line discipline before spreading.
auth.log is 200+ lines; use 'head', 'tail', and 'grep' rather than dumping with 'cat'.
Check CHEAT_SHEET.txt for filter and piping examples.

```


* `/var/log/CHEAT_SHEET.txt` (`0644`, `root:root`):
```text
================================================================================
                    OPERATOR TRAIL: LOG FILTERING CHEAT SHEET
================================================================================
SYNTAX OVERVIEW:
  • head -n <count> <file>   : Outputs the first <count> lines.
  • tail -n <count> <file>   : Outputs the last <count> lines.
  • grep -i <pattern> <file> : Performs a case-insensitive search.
  • <cmd1> | <cmd2>          : Pipes output of cmd1 into cmd2.
================================================================================

```


* `/var/log/auth.log` (`0640`, `root:adm`): Contains ~180 simulated PAM lines, ending with breach notifications referencing `/tmp/sys_miner` (PID `104`) and `/mnt/recovery`.



**Step-by-Step Clue Path**

1. Run `cd /var/log` and inspect `NOTE.txt` and `CHEAT_SHEET.txt`.


2. Run `tail -n 10 auth.log` or `grep -i "breach" auth.log`.


3. Run `grep -i "rogue" auth.log` to identify PID `104` and `/mnt/recovery`.



**Failure Modes & Edge Cases**

* Running plain `grep auth.log` returns POSIX stderr: `Usage: grep [OPTION]... PATTERNS [FILE]...` (Exit Code 2).


* Running `cat auth.log` outputs 200+ lines to standard output without crashing the emulator.



---

### Milestone 3: Recovery Partition Mounting (Filesystem Discovery)

* **Milestone ID & Name**: Milestone 3: Recovery Partition Mounting (Filesystem Discovery & Utilities)


* **Primary CLI Focus**: `find` (with `-name` and `-type`), `man`, path resolution, and filesystem traversal.


* **System Capability Unlocked**: Locates the recovery scripts and security tokens across nested recovery trees.


* **Flags Evaluated & Set**:
* *Prerequisites*: `SYSTEM_FLAGS["LOGS_AUDITED"] == True`.


* *Post-Resolution*: `SYSTEM_FLAGS["RECOVERY_LOCATED"] = True`.





```
[Prerequisite: LOGS_AUDITED = True]
                  │
                  ▼
   [Action: cd /mnt/recovery] ──► Navigate to recovery mount point[cite: 1]
                  │
                  ▼
 [Artifact: /mnt/recovery/NOTE.txt & CHEAT_SHEET.txt] ──► Learn find & man syntax[cite: 1, 2]
                  │
                  ▼
 [Action: find /mnt/recovery -name "*.sh" -type f] ──► Locate scripts across directory trees[cite: 1, 2]
                  │
                  ▼
 [Artifact Discovered: /mnt/recovery/bin/recovery.sh (Permissions: 000)][cite: 1, 2]
                  │
                  ▼
 [Resolution: RECOVERY_LOCATED = True] ──► Save state and trigger Debrief Panel[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/mnt/recovery`, `/mnt/recovery/bin`, `/mnt/recovery/keys`, `/mnt/recovery/docs`.


* `/mnt/recovery/NOTE.txt` (`0644`, `root:root`):
```text
[MORGAN'S LOG - 05:10 AM]
Emergency scripts and authentication keys were dumped here before isolation.
Use 'find' with '-name' and '-type' to locate them quickly. Use 'man find' for details.

```


* `/mnt/recovery/CHEAT_SHEET.txt` (`0644`, `root:root`):
```text
================================================================================
                    OPERATOR TRAIL: FILESYSTEM SEARCH & MAN
================================================================================
SYNTAX OVERVIEW:
  • man <command>                 : Opens documentation for a given tool.
  • find <path> -name "<pattern>" : Recursively searches for matching names.
  • find <path> -type f           : Restricts results to regular files.
================================================================================

```


* `/mnt/recovery/bin/recovery.sh` (`0000`, `root:root`): Restoration script with zeroed mode bits.


* `/mnt/recovery/keys/phoenix.key` (`0600`, `root:root`): Security authorization token.



**Step-by-Step Clue Path**

1. Run `cd /mnt/recovery` and read `NOTE.txt`.


2. Run `find /mnt/recovery -name "*.sh" -type f` to find `/mnt/recovery/bin/recovery.sh`.


3. Run `find /mnt/recovery -name "*.key"` to locate `phoenix.key`.


4. Run `ls -la /mnt/recovery/bin/recovery.sh` to confirm permissions are zeroed (`000`).



**Failure Modes & Edge Cases**

* Executing `find . -name` without arguments returns `find: missing argument to '-name'` (Exit Code 1).


* Trying to execute `./bin/recovery.sh` directly returns `bash: ./bin/recovery.sh: Permission denied` (Exit Code 126).



---

### Milestone 4: Security Integrity & Permissions (Executable Rights & Search Index)

* **Milestone ID & Name**: Milestone 4: Security Integrity & Permissions (Executable Rights & Search Index)


* **Primary CLI Focus**: `ls -l`, `chmod` (`+x`, `755`, `700`), and binary execution (`./recovery.sh`).


* **System Capability Unlocked**: Rebuilds filesystem query registers, unlocking `find` (`SYSTEM_FLAGS["FIND_UNLOCKED"] = True`).


* **Flags Evaluated & Set**:
* *Prerequisites*: `SYSTEM_FLAGS["RECOVERY_LOCATED"] == True`.


* *Post-Resolution*: `SYSTEM_FLAGS["PERMISSIONS_RESTORED"] = True`, `SYSTEM_FLAGS["FIND_UNLOCKED"] = True`.





```
[Prerequisite: RECOVERY_LOCATED = True]
                  │
                  ▼
 [Action: cd /mnt/recovery/bin && ls -l] ──► Inspect permissions (0000 / ----------)[cite: 1, 2]
                  │
                  ▼
 [Artifact: /mnt/recovery/bin/NOTE.txt & CHEAT_SHEET.txt] ──► Learn octal & symbolic chmod[cite: 1, 2]
                  │
                  ▼
 [Action: chmod +x recovery.sh || chmod 755 recovery.sh] ──► Restore execute/read bits[cite: 1, 2]
                  │
                  ▼
 [Action: ./recovery.sh] ──► Execute script to rebuild search index & unlock find[cite: 1, 2]
                  │
                  ▼
 [Resolution: FIND_UNLOCKED = True] ──► Unlock find utility + Emit Debrief[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/mnt/recovery/bin`, `/mnt/recovery/keys`, `/tmp`.


* `/mnt/recovery/bin/NOTE.txt` (`0644`, `root:root`):
```text
[MORGAN'S LOG - 05:45 AM]
Lockdown stripped mode bits across all binaries in this partition (0000).
Use symbolic (+x) or numeric (755) chmod to make recovery.sh executable.
Check CHEAT_SHEET.txt for octal permission breakdowns.

```


* `/mnt/recovery/bin/CHEAT_SHEET.txt` (`0644`, `root:root`):
```text
================================================================================
                    OPERATOR TRAIL: POSIX PERMISSIONS & CHMOD
================================================================================
OCTAL NOTATION:
  r = Read (4)  |  w = Write (2)  |  x = Execute (1)
  • 755 = rwxr-xr-x (User: read/write/exec, Others: read/exec)
  • 644 = rw-r--r-- (User: read/write, Others: read-only)

SYNTAX:
  • chmod +x <file>
  • chmod 755 <file>
  • ./<executable>
================================================================================

```


* `/mnt/recovery/bin/recovery.sh` (`0000` -> Modified to `0755` by player).



**Step-by-Step Clue Path**

1. Run `cd /mnt/recovery/bin` and check `ls -l`.


2. Run `cat NOTE.txt` and `cat CHEAT_SHEET.txt`.
3. Run `chmod +x recovery.sh` (or `chmod 755 recovery.sh`).


4. Run `./recovery.sh` to link kernel signal traps and activate `Ctrl+C`.



**Failure Modes & Edge Cases**

* Running `chmod 999 recovery.sh` returns `chmod: invalid mode: '999'` (Exit Code 1).


* Pressing `Ctrl+C` prior to resolution prints: `[HARDWARE ERROR]: Signal trap handler offline. SIGINT unavailable.`


---

### Milestone 5: Runaway Mitigation (Process Signaling)

* **Milestone ID & Name**: Milestone 5: Runaway Mitigation (Process Signaling & Incident Remediation)


* **Primary CLI Focus**: `ps aux`, `grep`, `kill` (`-15` / `SIGTERM` and `-9` / `SIGKILL`), and pipeline auditing (`ps aux | grep miner`).


* **System Capability Unlocked**: Clears CPU thermal throttling and releases blocked socket ports for network operations.


* **Flags Evaluated & Set**:
* *Prerequisites*: `SYSTEM_FLAGS["SIGINT_UNLOCKED"] == True`.


* *Post-Resolution*: `SYSTEM_FLAGS["MALWARE_TERMINATED"] = True`.





```
[Prerequisite: SIGINT_UNLOCKED = True]
                  │
                  ▼
 [Action: cd /tmp && ls -la] ──► Locate rogue binary artifacts & Morgan's log[cite: 1, 2]
                  │
                  ▼
 [Artifact: /tmp/NOTE.txt & CHEAT_SHEET.txt] ──► Learn ps flags and kill signal numbers[cite: 1, 2]
                  │
                  ▼
 [Action: ps aux | grep miner] ──► Identify PID 104 consuming 98.2% CPU[cite: 1, 2]
                  │
                  ▼
 [Action: kill -15 104] ──► Graceful termination refused by malware[cite: 1, 2]
                  │
                  ▼
 [Action: kill -9 104] ──► Force SIGKILL to clear process table entry[cite: 1, 2]
                  │
                  ▼
 [Resolution: MALWARE_TERMINATED = True] ──► CPU normalizes + Emit Debrief Panel[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/tmp`, `/proc`, `/var/log`.


* `/tmp/NOTE.txt` (`0644`, `root:root`):
```text
[MORGAN'S LOG - 06:15 AM]
The breach injected a miner into /tmp/sys_miner, taking 98% CPU.
Standard kill -15 will be trapped and ignored by the daemon.
Use unconditional kill (kill -9) on its PID to reclaim CPU cycles.

```


* `/tmp/CHEAT_SHEET.txt` (`0644`, `root:root`):
```text
================================================================================
                    OPERATOR TRAIL: PROCESS AUDITING & SIGNALS
================================================================================
SYNTAX OVERVIEW:
  • ps aux               : Displays active processes and CPU usage.
  • ps aux | grep <name> : Filters process table directly.
  • kill <PID>           : Sends SIGTERM (-15).
  • kill -9 <PID>        : Sends SIGKILL (-9).
================================================================================

```


* Process Table State: `PID 104` (`sys_miner`, CPU: `98.2%`, status: `"running"`).



**Step-by-Step Clue Path**

1. Run `cd /tmp` and read `NOTE.txt` and `CHEAT_SHEET.txt`.


2. Run `ps aux | grep miner` to locate PID `104`.


3. Run `kill 104` to observe the daemon trapping `SIGTERM`.


4. Run `kill -9 104` to force termination and normalize CPU usage.



**Failure Modes & Edge Cases**

* Running `kill -9 1` returns `kill: (1) - Operation not permitted`.


* Running `kill` without a target returns standard POSIX stderr: `kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ...` (Exit Code 1).



---

### Milestone 6: Network Uplink Diagnostic (Sockets & Routing)

* **Milestone ID & Name**: Milestone 6: Network Uplink Diagnostic (Sockets & Routing)


* **Primary CLI Focus**: `ip addr`, `ip link set <iface> up`, `ss -tulpn`, `ping -c <count>`, and `apollo-net`.


* **System Capability Unlocked**: `apollo0` brought to `UP` status; routing confirmed with gateway `10.0.42.1`.


* **Flags Evaluated & Set**:
* *Prerequisites*: `SYSTEM_FLAGS["MALWARE_TERMINATED"] == True`.


* *Post-Resolution*: `SYSTEM_FLAGS["NETWORK_ONLINE"] = True`.





```
[Prerequisite: MALWARE_TERMINATED = True]
                  │
                  ▼
 [Action: cd /etc/network && ls] ──► Inspect network configuration tree[cite: 1]
                  │
                  ▼
 [Artifact: /etc/network/NOTE.txt & CHEAT_SHEET.txt] ──► Learn ip, ss, and ping syntax[cite: 1, 2]
                  │
                  ▼
 [Action: ip addr || apollo-net] ──► Discover apollo0 link state is DOWN[cite: 1, 2]
                  │
                  ▼
 [Action: ip link set apollo0 up] ──► Bring link state online[cite: 1, 2]
                  │
                  ▼
 [Action: ss -tulpn] ──► Verify socket ports and confirm port 8080 is available[cite: 1, 2]
                  │
                  ▼
 [Action: ping -c 4 10.0.42.1] ──► Test link connectivity to Phoenix Gateway[cite: 1, 2]
                  │
                  ▼
 [Resolution: NETWORK_ONLINE = True] ──► Persist state & emit Debrief Panel[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/etc/network`, `/etc/phoenix`, `/var/run`.


* `/etc/network/NOTE.txt` (`0644`, `root:root`):
```text
[MORGAN'S LOG - 07:05 AM]
The malware administratively disabled interface apollo0.
1. Inspect network devices with 'ip addr'.
2. Bring the interface online: 'ip link set apollo0 up'.
3. Audit open listening ports with 'ss -tulpn'.
4. Ping gateway 10.0.42.1 to confirm routing.

```


* `/etc/network/CHEAT_SHEET.txt` (`0644`, `root:root`):
```text
================================================================================
                    OPERATOR TRAIL: NETWORK OPERATIONS
================================================================================
SYNTAX OVERVIEW:
  • ip addr                   : Displays IP addresses and link states.
  • ip link set <dev> <state> : Sets interface state ('up' or 'down').
  • ss -tulpn                 : Audits active TCP/UDP listening sockets.
  • ping -c <count> <target>  : Sends ICMP echo requests to target host.
================================================================================

```


* `/etc/network/interfaces` (`0644`, `root:root`): Network map defining `apollo0` on `10.0.42.15/24` with gateway `10.0.42.1`.



**Step-by-Step Clue Path**

1. Run `cd /etc/network` and read `NOTE.txt`.


2. Run `ip addr` or `apollo-net` to verify `apollo0` is `DOWN`.


3. Run `ip link set apollo0 up`.


4. Run `ss -tulpn` to verify open sockets.


5. Run `ping -c 4 10.0.42.1` to confirm gateway reachability and unlock network state.



**Failure Modes & Edge Cases**

* Running `ping 10.0.42.1` prior to bringing the link up outputs: `ping: connect: Network is unreachable` (Exit Code 2).
* Running `ip link set eth0 up` returns: `Cannot find device "eth0"` (Exit Code 1).



---

### Milestone 7: PHOENIX Restoration (Campaign Finale)

* **Milestone ID & Name**: Milestone 7: PHOENIX Restoration (Campaign Finale & Multi-Tool Synthesis)


* **Primary CLI Focus**: `cd`, `ls -la`, `cat`, `chmod`, stream appending (`>>`), piping (`|`), and daemon orchestration (`phoenix_daemon start` / `phoenix_ctl start`).


* **System Capability Unlocked**: Complete workstation recovery; global cluster gateway link confirmed; campaign victory.


* **Flags Evaluated & Set**:
* *Prerequisites*: `SYSTEM_FLAGS["NETWORK_ONLINE"] == True`.


* *Post-Resolution*: `SYSTEM_FLAGS["PHOENIX_ONLINE"] = True`.





```
[Prerequisite: NETWORK_ONLINE = True]
                  │
                  ▼
   [Action: cd /etc/phoenix && ls -la] ──► Inspect locked configuration files[cite: 1]
                  │
                  ▼
 [Artifact: /etc/phoenix/NOTE.txt & CHEAT_SHEET.txt] ──► Morgan's synthesis briefing[cite: 1]
                  │
                  ▼
 [Action: cat /mnt/recovery/keys/phoenix.key] ──► Retrieve authorization token[cite: 1]
                  │
                  ▼
 [Action: Append key token to /etc/phoenix/phoenix.conf via >>] ──► Authorize daemon
                  │
                  ▼
 [Action: chmod 644 /etc/phoenix/phoenix.conf] ──► Lock down configuration permissions[cite: 1]
                  │
                  ▼
 [Action: phoenix_daemon start || phoenix_ctl start] ──► Launch emergency daemon service[cite: 1, 2]
                  │
                  ▼
 [Action: ss -tulpn | grep 8080] ──► Verify daemon socket listening on 127.0.0.1:8080[cite: 1, 2]
                  │
                  ▼
 [Resolution: PHOENIX_ONLINE = True] ──► Trigger Victory Sequence & Final Linux Debrief[cite: 1, 2]

```

**File Manifest & Initial Machine State**

* Directories: `/etc/phoenix`, `/mnt/recovery/keys`, `/var/log`.


* `/etc/phoenix/NOTE.txt` (`0644`, `root:root`):
```text
[MORGAN'S FINAL LOG - 07:40 AM]
Final hurdle: bringing the PHOENIX cluster restoration daemon online.
1. Retrieve key from /mnt/recovery/keys/phoenix.key and append it to 
   /etc/phoenix/phoenix.conf using '>>'.
2. Secure config permissions: chmod 644 /etc/phoenix/phoenix.conf.
3. Start daemon: 'phoenix_daemon start' (or 'phoenix_ctl start').
4. Verify socket on port 8080: 'ss -tulpn | grep 8080'.

```


* `/etc/phoenix/CHEAT_SHEET.txt` (`0644`, `root:root`):
```text
================================================================================
                    OPERATOR TRAIL: SYNTHESIS & ORCHESTRATION
================================================================================
PRACTICAL PIPELINE:
  1. cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf
  2. chmod 644 /etc/phoenix/phoenix.conf
  3. phoenix_daemon start
  4. ss -tulpn | grep 8080
================================================================================

```


* `/etc/phoenix/phoenix.conf` (`0600`, `root:root`): Initial daemon config missing `AUTH_TOKEN`.



**Step-by-Step Clue Path**

1. Run `cd /etc/phoenix` and read `NOTE.txt` and `CHEAT_SHEET.txt`.


2. Run `cat /mnt/recovery/keys/phoenix.key >> /etc/phoenix/phoenix.conf` to insert the authorization token.


3. Run `chmod 644 /etc/phoenix/phoenix.conf` to set appropriate file rights.


4. Run `phoenix_daemon start` (or `phoenix_ctl start`).


5. Run `ss -tulpn | grep 8080` to confirm listening state and trigger the victory sequence.



**Failure Modes & Edge Cases**

* Overwriting the file via `>` rather than appending with `>>` strips existing daemon configuration parameters; `decrypt` flags the missing parameters and suggests restoring from backup.


* Running `phoenix_daemon start` without appending `phoenix.key` returns `[PHOENIX ERROR]: Authentication token missing in /etc/phoenix/phoenix.conf` (Exit Code 1).