# TERMINAL ZERO
## Game Design Document — v1.0

**Genre:** Educational Terminal Adventure / Puzzle / Interactive Fiction  
**Platform:** Linux, Windows, macOS, Android/Termux  
**Primary Technology:** Python 3  
**Interface:** Terminal / CLI  
**Target Audience:** Linux beginners through early intermediate users  
**Players:** 1  
**Session Length:** 15–45 minutes per mission  
**Overall Campaign:** ~4–8 hours for first complete playthrough

---

# 1. GAME OVERVIEW

## 1.1 High Concept

**TERMINAL ZERO** is a terminal-based educational adventure in which the player learns real Linux commands and concepts while investigating a fictional global cyber crisis.

The player assumes the role of an emergency systems operator whose only functioning interface is a Linux terminal.

A catastrophic attack has disrupted critical infrastructure around the world. The player must investigate a compromised workstation, discover clues, diagnose fictional systems, and ultimately restore the emergency network.

The game teaches Linux organically by making Linux commands the player's primary problem-solving tools.

### Core design principle

> **The player should learn Linux because they need Linux to solve the game.**

The game should never feel like a Linux quiz with a story pasted on top.

---

# 2. DESIGN GOALS

## 2.1 Primary Goal

Teach practical Linux command-line fundamentals through interactive problem solving.

By the end of the campaign, a player who began with little or no Linux experience should be comfortable with:

- navigating a filesystem
- understanding paths
- inspecting files
- searching text
- finding files
- understanding permissions
- working with processes
- performing basic network diagnostics
- using pipes and redirection
- reading manual/help documentation
- combining commands to accomplish a task

---

## 2.2 Secondary Goal

Create the fantasy of being a competent terminal-based incident responder.

The player should feel like:

> "I figured that out with the command line."

rather than:

> "The game told me which answer to type."

---

## 2.3 Safety Goal

The game must operate entirely inside a simulated environment.

**The game must NEVER execute arbitrary commands on the player's real operating system.**

The simulated filesystem, processes, users, network services, and files exist only inside the game.

Do not use:

```python
os.system()
subprocess.run()
subprocess.Popen()
eval()
exec()
```

to execute player commands.

The game should implement its own command parser and virtual environment.

---

# 3. PLAYER FANTASY

The player is an emergency systems operator in the year 2042.

They have access to a damaged Linux workstation called **APOLLO**.

The player does not initially know:

- what happened
- who caused it
- what PHOENIX is
- what services remain operational
- where the recovery tools are
- what credentials or access phrases exist

They must investigate.

The terminal is their only tool.

---

# 4. STORY

## 4.1 Setting

**Year:** 2042

Global infrastructure has become highly interconnected.

A coordinated cyberattack has disrupted:

- emergency communications
- satellite networks
- power-grid monitoring
- medical infrastructure
- transportation systems

A dormant emergency recovery system called **PHOENIX** may still be capable of restoring global communications.

Unfortunately, the primary PHOENIX control terminal has been compromised.

The player is given one remaining local workstation.

---

# 5. NARRATIVE STRUCTURE

The story should unfold through:

- terminal messages
- files
- logs
- configuration files
- system messages
- mission briefings
- fictional service output
- environmental clues

Avoid long cinematic exposition.

The filesystem itself should tell the story.

Example:

```text
/home/alice/notes/meeting.txt
/var/log/system.log
/opt/phoenix/README.txt
/etc/motd
```

The player learns what happened by investigating these artifacts.

---

# 6. CORE GAMEPLAY LOOP

The fundamental loop is:

```text
STORY EVENT
     ↓
INVESTIGATE
     ↓
DISCOVER INFORMATION
     ↓
FORM HYPOTHESIS
     ↓
USE LINUX COMMAND
     ↓
OBSERVE RESULT
     ↓
SOLVE PUZZLE
     ↓
UNLOCK NEW INFORMATION
     ↓
ADVANCE STORY
```

The game should encourage experimentation.

Incorrect commands should usually provide useful feedback rather than simply saying "wrong."

---

# 7. TERMINAL INTERFACE

Example startup:

```text
╔══════════════════════════════════════════════════════════════╗
║                    TERMINAL ZERO                              ║
║               APOLLO INCIDENT TERMINAL                        ║
╚══════════════════════════════════════════════════════════════╝

SYSTEM STATUS: DEGRADED
NETWORK STATUS: OFFLINE
THREAT LEVEL: CRITICAL

USER: alice
HOST: apollo

Emergency Incident Response Protocol Active.

Type 'help' for available commands.

alice@apollo:~$
```

The terminal should support:

- command history
- scrolling output
- clear screen
- contextual prompts
- readable error messages
- optional ANSI colors

The game must remain functional if colors are unavailable.

---

# 8. VIRTUAL FILESYSTEM

The game must maintain an in-memory filesystem.

Example:

```text
/
├── home/
│   └── alice/
│       ├── .mission/
│       │   └── briefing.txt
│       ├── logs/
│       │   └── login.log
│       ├── notes/
│       │   ├── meeting.txt
│       │   └── server.txt
│       ├── readme.txt
│       └── todo.txt
│
├── etc/
│   ├── hostname
│   ├── motd
│   └── services.conf
│
├── opt/
│   └── phoenix/
│       ├── README.txt
│       ├── config/
│       └── recovery/
│
├── tmp/
│
└── var/
    └── log/
        ├── system.log
        └── auth.log
```

The filesystem should be mutable within the simulation.

For example, missions may:

- create files
- delete files
- modify files
- change permissions
- start processes
- stop processes
- change simulated network state

---

# 9. COMMAND SYSTEM

The game should implement a command interpreter.

Architecture:

```text
PLAYER INPUT
     ↓
TOKENIZER
     ↓
COMMAND PARSER
     ↓
COMMAND HANDLER
     ↓
VIRTUAL SYSTEM
     ↓
OUTPUT
     ↓
MISSION STATE UPDATE
```

Commands should return output similar to real Linux commands.

---

# 10. COMMAND PROGRESSION

Commands are introduced gradually.

## Tier 1 — Navigation

```bash
pwd
ls
ls -a
ls -l
cd
cd ..
```

Concepts:

- current working directory
- absolute paths
- relative paths
- hidden files
- directory traversal
- permissions preview

---

## Tier 2 — File Inspection

```bash
cat
head
tail
less
```

Concepts:

- reading files
- standard output
- inspecting logs

---

## Tier 3 — Searching

```bash
grep
find
```

Concepts:

- text search
- patterns
- filenames
- recursive searching
- command arguments

---

## Tier 4 — Pipes and Redirection

```bash
|
>
>>
```

Examples:

```bash
grep ERROR system.log
grep ERROR system.log | head
grep ERROR system.log > errors.txt
```

Concepts:

- standard output
- chaining commands
- redirecting output
- Unix composability

---

## Tier 5 — Permissions

```bash
ls -l
chmod
```

Teach:

```text
r = read
w = write
x = execute
```

And basic numeric permissions:

```bash
chmod 755 script.sh
```

Only introduce numeric permissions after symbolic permissions are understood.

---

## Tier 6 — Processes

```bash
ps
top
kill
```

Teach:

- process
- PID
- resource usage
- terminating processes

---

## Tier 7 — System Information

```bash
whoami
uname
hostname
```

Teach:

- user identity
- host identity
- operating system information

---

## Tier 8 — Networking

```bash
ping
ip
ss
```

These operate entirely on simulated network state.

Teach:

- IP addresses
- interfaces
- ports
- listening services
- connectivity

---

## Tier 9 — Documentation

```bash
help
man
```

Teaching players how to discover command syntax independently is an explicit game objective.

---

# 11. COMMAND MASTERY

The game tracks commands the player has successfully used.

Example:

```text
COMMAND MASTERY

pwd       ██████████  MASTERED
ls        ██████████  MASTERED
cd        ███████░░░  PRACTICING
cat       ██████████  MASTERED
grep      ████░░░░░░  LEARNING
find      ██░░░░░░░░  NEW
chmod     ░░░░░░░░░░  LOCKED
```

This is informational rather than a major progression mechanic.

---

# 12. TEACHING SYSTEM

The game follows:

> **Teach → Require → Reward**

Do not immediately provide solutions.

Example objective:

```text
SYSTEM MESSAGE

The incident logs contain thousands of entries.

Find every entry associated with the PHOENIX service.
```

The player must determine that `grep` is appropriate.

---

# 13. CONTEXTUAL LESSONS

When a player successfully uses a new command, display a short explanation.

Example:

```text
┌─────────────────────────────────────────┐
│ NEW COMMAND DISCOVERED                  │
│                                         │
│ grep                                    │
│                                         │
│ Searches text for matching patterns.    │
│                                         │
│ Example:                                │
│ grep ERROR system.log                   │
└─────────────────────────────────────────┘
```

Do not repeatedly display lessons for commands the player already knows.

---

# 14. ERROR-BASED TEACHING

Incorrect syntax should provide educational feedback.

Example:

```text
$ grepp phoenix system.log

grepp: command not found

[LEARNING TIP]

Linux does not recognize "grepp" as a command.

Check the spelling or try:

    help
```

Another example:

```text
$ grep system.log phoenix

grep: phoenix: No such file or directory

[LEARNING TIP]

grep normally follows this structure:

    grep PATTERN FILE
```

The game should turn mistakes into lessons.

---

# 15. HINT SYSTEM

Every puzzle has three hint levels.

## Hint 1 — Concept

```text
[HINT]

You need to search text inside a file.
```

## Hint 2 — Command

```text
[HINT]

Think of the Linux command used to search text.
```

## Hint 3 — Syntax

```text
[HINT]

Try:

grep phoenix system.log
```

Hints reduce the player's mission score but never prevent completion.

---

# 16. MISSION STRUCTURE

The campaign consists of eight primary missions.

---

## MISSION 0 — BOOT

### Objective

Understand the terminal and establish basic orientation.

### Commands

```bash
help
pwd
ls
whoami
hostname
```

### Linux concepts

- terminal prompt
- current directory
- user
- hostname
- command syntax

### Story

The player boots APOLLO and discovers that the global emergency network is offline.

---

# MISSION 1 — THE HIDDEN BRIEFING

### Objective

Find a hidden mission briefing.

### Commands

```bash
pwd
ls
ls -a
cd
cat
```

### Concepts

- directories
- paths
- hidden files
- `.` and `..`

### Key discovery

```text
/home/alice/.mission/briefing.txt
```

The briefing reveals that PHOENIX may still be operational.

---

# MISSION 2 — GHOST IN THE LOGS

### Objective

Identify the suspicious process responsible for the initial compromise.

### Commands

```bash
cat
head
tail
grep
```

### Concepts

- log files
- text searching
- patterns
- reading large files

Example:

```bash
grep phoenix /var/log/system.log
```

The player discovers references to:

```text
phoenix-sync
```

---

# MISSION 3 — FIND PHOENIX

### Objective

Locate the PHOENIX installation and its configuration.

### Commands

```bash
find
grep
cat
```

Example:

```bash
find /opt -name "*.conf"
```

Then inspect relevant files.

The player discovers the emergency recovery system.

---

# MISSION 4 — BROKEN PERMISSIONS

### Objective

Recover access to a disabled recovery script.

### Commands

```bash
ls -l
chmod
```

### Concepts

- ownership
- read/write/execute
- symbolic permissions
- numeric permissions

The player discovers:

```text
recovery.sh
```

but it is not executable.

They must understand why.

---

# MISSION 5 — RUNAWAY

### Objective

Identify and terminate a fictional malicious process.

### Commands

```bash
ps
top
kill
```

### Concepts

- process IDs
- processes
- CPU usage
- terminating processes

Example:

```text
PID   USER   CPU   COMMAND

101   root    2%   systemd
284   alice   1%   terminal
733   root   94%   phoenix_sync
```

The player must determine which process is abnormal.

---

# MISSION 6 — BLACKOUT

### Objective

Diagnose the fictional emergency network.

### Commands

```bash
ip
ping
ss
```

### Concepts

- network interfaces
- IP addresses
- ports
- listening services
- connectivity

The player discovers that the PHOENIX service is listening on a fictional port.

---

# MISSION 7 — RECOVERY

### Objective

Restore PHOENIX.

This is the campaign finale.

The player must combine previously learned concepts.

Potential sequence:

```text
navigate
find
grep
inspect
repair permissions
inspect processes
diagnose network
execute fictional recovery command
```

The player should NOT be given the exact sequence.

The environment should contain enough information for them to determine it.

---

# 17. FINAL SEQUENCE

After successfully solving the final puzzle:

```text
══════════════════════════════════════════════════════════════

                 CONNECTION ESTABLISHED

              PHOENIX EMERGENCY NODE

                       ONLINE

══════════════════════════════════════════════════════════════

Satellite control restored.

Emergency communications reconnecting...

Medical infrastructure: ONLINE
Emergency communications: ONLINE
Satellite network: ONLINE
Global monitoring: ONLINE

                GLOBAL NETWORK RESTORED


                       WORLD SAVED

══════════════════════════════════════════════════════════════
```

Then provide a skill summary.

---

# 18. SCORING

Score should reward learning rather than speed.

### Positive

- discovering commands independently
- completing puzzles
- using appropriate commands
- completing optional objectives
- avoiding hints

### Negative

- using hints
- repeated unnecessary commands
- excessive failed attempts

Example:

```text
MISSION COMPLETE

Mission: Ghost in the Logs

Time:        12:43
Commands:    31
Hints:       1

COMMANDS USED

grep         ★★★★★
cat          ★★★★★
head         ★★★★☆
tail         ★★★☆☆

MISSION RATING: A
```

---

# 19. OPTIONAL OBJECTIVES

Missions should contain optional discoveries.

Example:

> Find the operator's personal note.

These should provide:

- additional story
- worldbuilding
- bonus score
- command practice

They should never be required for campaign completion.

---

# 20. SAVE SYSTEM

Save game state locally.

Example:

```json
{
    "current_mission": 4,
    "completed_missions": [0, 1, 2, 3],
    "commands_discovered": [
        "pwd",
        "ls",
        "cd",
        "cat",
        "grep"
    ],
    "hints_used": 2,
    "score": 842
}
```

Commands:

```bash
save
load
reset
```

The save file itself should be ordinary JSON.

---

# 21. REAL-LINUX TRANSITION

At the end of each mission, optionally provide a **Take It to Linux** section.

Example:

```text
╔════════════════════════════════════════════╗
║ TAKE IT TO REAL LINUX                     ║
╚════════════════════════════════════════════╝

You just learned:

    pwd
    ls
    cd
    cat
    grep

Try these commands on a real Linux system:

    pwd
    ls -la
    cd /tmp
    cat /etc/hostname
```

This section should make clear that these commands will now operate on the player's actual machine.

The game itself never executes them.

---

# 22. REAL-WORLD COMMAND SAFETY

The educational material may teach normal Linux administration commands.

However, the game should remain focused on:

- filesystem navigation
- system inspection
- troubleshooting
- permissions
- processes
- networking fundamentals
- scripting fundamentals

Do not make real-world exploitation the learning objective.

The fictional "hacking" fantasy should be implemented through simulated systems.

---

# 23. OPTIONAL BASH SCRIPTING MODULE

A future expansion may introduce shell scripting.

Topics:

```bash
#!/bin/bash
echo
variables
if
then
fi
for
```

Example:

```bash
#!/bin/bash

echo "Starting Phoenix recovery..."

if [ -f /opt/phoenix/ready ]; then
    echo "Phoenix is ready."
fi
```

The game should explain the syntax rather than actually executing arbitrary scripts.

---

# 24. ACCESSIBILITY

The game should:

- work entirely from the keyboard
- require no mouse
- use readable text
- avoid relying exclusively on color
- work on small terminal windows
- support terminals without ANSI color
- provide adjustable text speed if narrative animation is implemented

---

# 25. TECHNICAL ARCHITECTURE

Recommended structure:

```text
terminal_zero/
│
├── main.py
│
├── game/
│   ├── engine.py
│   ├── parser.py
│   ├── terminal.py
│   ├── filesystem.py
│   ├── processes.py
│   ├── networking.py
│   ├── missions.py
│   ├── hints.py
│   ├── scoring.py
│   └── save.py
│
├── commands/
│   ├── pwd.py
│   ├── ls.py
│   ├── cd.py
│   ├── cat.py
│   ├── head.py
│   ├── tail.py
│   ├── grep.py
│   ├── find.py
│   ├── chmod.py
│   ├── ps.py
│   ├── kill.py
│   ├── ping.py
│   ├── ip.py
│   └── ss.py
│
├── data/
│   ├── filesystem.json
│   ├── missions.json
│   └── commands.json
│
└── README.md
```

For the initial prototype, a single-file implementation is acceptable.

Refactor into modules only after the gameplay loop is working.

---

# 26. DEVELOPMENT PHASES

## Phase 1 — Prototype

Implement:

```text
virtual filesystem
terminal prompt
command parser
pwd
ls
ls -a
cd
cat
help
```

Create Mission 1.

**Do not implement the whole campaign yet.**

---

## Phase 2 — Core Linux Mechanics

Add:

```text
head
tail
grep
find
```

Implement Mission 2 and Mission 3.

---

## Phase 3 — Shell Mechanics

Add:

```text
pipes
>
>>
```

Implement a mission specifically designed around command composition.

---

## Phase 4 — System Administration

Add:

```text
ls -l
chmod
ps
top
kill
```

Implement Missions 4 and 5.

---

## Phase 5 — Networking

Add simulated:

```text
ip
ping
ss
```

Implement Mission 6.

---

## Phase 6 — Campaign Finale

Implement Mission 7.

Add:

- final sequence
- campaign completion
- skill report
- save system
- replay capability

---

# 27. MVP DEFINITION

The first playable build is successful if a completely new player can:

1. start the game
2. understand the terminal prompt
3. use `pwd`
4. use `ls`
5. discover `ls -a`
6. navigate with `cd`
7. locate a hidden directory
8. read a file with `cat`
9. complete Mission 1
10. understand what each of those commands actually does

The MVP does **not** need:

- networking
- processes
- permissions
- sophisticated scoring
- complex narrative
- Bash scripting

Those come later.

---

# 28. DESIGN RULES FOR FUTURE CONTENT

Every new mission must answer three questions:

### 1. What Linux skill does this teach?

If there isn't a clear answer, don't add the mechanic.

### 2. Why does the player need this skill?

The command should solve an actual in-game problem.

### 3. Does the player have enough information to discover the solution?

The game should encourage reasoning rather than guessing.

---

# 29. ANTI-PATTERNS

Avoid:

### Command quizzes

```text
What command lists files?

A) cat
B) ls
C) grep
D) cd
```

Use actual terminal interaction instead.

### Artificial command locks

Don't make:

```text
grep
```

literally unavailable because the player hasn't unlocked it.

The player should be able to experiment.

### Excessive hand-holding

Don't constantly say:

```text
Now type ls.
Now type cd.
Now type cat.
```

Give the player an objective and let them determine the tool.

### Fake complexity

Don't add commands just because they sound "hacker-ish."

Every command should contribute to Linux competency.

### Real shell execution

Never pass player input to the host operating system.

---

# 30. SUCCESS CRITERIA

TERMINAL ZERO is successful if a player finishes the campaign and naturally thinks:

> "I should probably `grep` that."

or:

> "I need to `find` the file."

or:

> "Let me check `ls -l` and see the permissions."

That behavioral change is more important than whether they memorized a list of commands.

---

# 31. LONG-TERM EXPANSION

Potential future campaigns:

## Campaign 2 — SYSADMIN

Focus:

- users
- groups
- permissions
- services
- logs
- package management
- systemd concepts

## Campaign 3 — DEVOPS

Focus:

- Git
- SSH
- environment variables
- configuration
- Docker concepts
- deployment
- logs

## Campaign 4 — NETWORK OPERATIONS

Focus:

- routing
- DNS
- ports
- sockets
- interfaces
- troubleshooting

## Campaign 5 — SHELL

Focus:

- Bash
- variables
- loops
- conditionals
- functions
- scripts
- automation

The same virtual Linux environment could eventually become a full **Linux command-line RPG/training simulator**.

---

# 32. ONE-SENTENCE PRODUCT DEFINITION

> **TERMINAL ZERO is a fictional cyber-incident adventure where the player learns real Linux command-line skills by using a simulated terminal to investigate and ultimately save the world.**