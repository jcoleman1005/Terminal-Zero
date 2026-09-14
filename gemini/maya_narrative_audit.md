# Narrative Architect Audit — Maya Character Draft
*Terminal Zero // Continuity Audit v1.0*

---

## Framing: What Maya Is and What She Needs to Be

Maya is a brilliant narrative invention. She fills a gap the current lore doesn't cover: **the human cost of institutional knowledge loss**. Morgan speaks as a sysadmin authority figure. Maya speaks as *the player was before they started*. She is the honest mirror — panicked, resourceful by accident, learning by stumbling — and her voice gives players permission to feel confused because the last person on this machine felt confused too.

Her role as a **bridge character** (Alice reads Maya's notes to learn what Maya learned from Javi's notes) also sets up a recursive archaeology structure that pays off emotionally: by the end, the player is the third link in a chain of operators keeping something alive.

This is strong. The audit below is not about discarding it — it's about locking it to canon before it ships.

---

## 1. Continuity Scorecard

| Dimension | Status |
|---|---|
| **Continuity Status** | ⚠️ MINOR DRIFT — No critical contradictions, but Maya's existence needs anchoring to the canonical incident timeline |
| **Diegetic Authenticity** | ✅ High — Notes are delivered as personal diary/log entries, fully diegetic |
| **Tonal Alignment** | ✅ Consistent with Pitch — Panicked, human, non-gamified voice is exactly right |

---

## 2. Discrepancy & Risk Analysis

### Canonical Contradictions

| # | Issue | Risk | Location |
|---|---|---|---|
| **C1** | Maya refers to `cd <filename>` — the correct term is **directory**, not filename. She correctly learns this later, but the typo in the note itself (`cd <filename>`) will embed wrong syntax in a *readable in-game file*. Players will copy it. | **Medium** — pedagogical collision | Maya_00 |
| **C2** | `cd . .` (with a space) is incorrect POSIX syntax — the command is `cd ..` (no space). If Alice executes this from seeing Maya's note, she'll get an error. | **High** — real command, wrong syntax | Maya_03 |
| **C3** | Maya_04 references "tab key" triggering errors because Javi lost his `$PATH`. In the canonical lore, Tab autocompletion is broken because `~/.bashrc` is missing — not because of `$PATH`. These are different faults. The `$PATH` is referenced in `alice.bashrc` (the backup template), not as a separate incident. This conflation could mislead players about what they need to fix. | **Medium** — lore drift | Maya_04 |
| **C4** | Maya says Javi "lost his `$PATH`… and had to restore it from a backup" and "it was in the bin." In canonical lore, the backup is at `/opt/backup/profiles/alice.bashrc` — not in `/bin`. A player reading this and exploring `/bin` will be confused. | **Medium** — wrong path hint | Maya_04 |
| **C5** | Maya is not yet placed in the incident timeline. When did she use OSIRIS? Before the 2042-10-11 attack? Was she Javi's successor and then also left before Alice arrived? This needs one anchoring line to prevent lore questions. | **Low** — no contradiction yet, but becomes one if you add more Maya notes | All |

### Spoke-Order Dependency Violations

None found. Maya's notes cover fundamentals (`cd`, `ls -a`, `touch`, `cd ..`, `$PATH`) that precede any spoke. This is safe.

### Pedagogical Collisions

- `cd <filename>` (Maya_00) — players will try this literally and get `bash: cd: filename: No such file or directory`
- `cd . .` (Maya_03) — players will get an error and assume the game is broken

---

## 3. Voice & Tone Critique

**What works extremely well:**

- *"God this sucks."* — perfect opening line. Instantly human.
- *"Javi never got around to training anybody how to do this."* — loads backstory and tragedy into one sentence without over-explaining.
- *"I read one, but I wasn't interested in learning about his weird rash."* — this is genuinely funny and reveals character without breaking immersion.
- *"He was always kind of lazy. But so am I."* — earned self-awareness. Great.
- The escalating competence arc across 5 notes is exactly right.

**Minor tone notes:**

- Maya_00 ends with a raw code fragment (`cd <filename>`) that reads like a note-to-self rather than prose. Consider wrapping it: *"Apparently I type 'cd' and then the directory name after it."*
- Maya_04's final line trails off (file ends mid-thought). This is either intentional atmosphere or a draft artifact — flag for completion.
- Morgan and Maya should not share the same note locations (e.g., both can't have a note at `/home/alice/`). Maya's notes should feel like they predate the incident — personal diaries, not operational scratchpads.

---

## 4. Production-Ready Rewrite

All five entries below fix the POSIX syntax errors, anchor Maya to the timeline, and preserve every beat of the original voice.

---

### Maya_00

```text
// ============================================================================
// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]
// TIMESTAMP: 2042-07-14 // FILE: /home/alice/.maya_notes/Maya_00.txt
// ============================================================================

God this sucks. They threw me on this thing when Javi kicked the bucket, just
because I knew how to turn it on. Javi never got around to training anybody
how to do this.

Anyway I found a sticky note taped to the terminal that says if I type 'cd'
followed by the name of a directory — which is apparently a different "room"
in the system — I can move there. I've been trying to hop around but I keep
getting errors saying things like "no such file or directory."

At least I figured out that typing:
  cd ~
...always drops me back in my home folder. I'll take it.

— Maya
// ============================================================================
```

---

### Maya_01

```text
// ============================================================================
// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]
// TIMESTAMP: 2042-07-15 // FILE: /home/alice/.maya_notes/Maya_01.txt
// ============================================================================

Ok I figured out why cd kept failing! You have to type the directory name
EXACTLY as it appears — weird forward-slashes and dots included. The system
is very literal.

Oh yeah — I also found out that if I type 'ls -a', a whole extra bunch of
files and folders appear. Javi apparently stashed some of his more... personal
notes in those dot-folders. I read one. I was not interested in learning about
his weird rash.

— Maya
// ============================================================================
```

---

### Maya_02

```text
// ============================================================================
// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]
// TIMESTAMP: 2042-07-17 // FILE: /home/alice/.maya_notes/Maya_02.txt
// ============================================================================

Oh yeah! Just made my own secret file!

Turns out when Javi wrote "touching" in one of his notes, he was literally
talking about the command that creates a new empty file:
  touch <filename>

I definitely thought he meant something else. Anyway. I'm going to go back
and leave some notes for myself in my home folder so I don't forget how to
move around.

— Maya
// ============================================================================
```

---

### Maya_03

```text
// ============================================================================
// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]
// TIMESTAMP: 2042-07-18 // FILE: /home/alice/.maya_notes/Maya_03.txt
// ============================================================================

Ok I'm starting to get lost. I went four directories deep trying to find where
Javi kept his tool notes and had no idea how to backtrack.

Luckily I mistyped something and discovered that 'cd ..' (two dots, no space)
goes up one level to the parent folder. Accidentally stumbling into solutions
is basically my whole strategy at this point.

— Maya
// ============================================================================
```

---

### Maya_04

```text
// ============================================================================
// PERSONAL LOG // OSIRIS WORKSTATION // USER: maya [OPERATOR-TEMP]
// TIMESTAMP: 2042-07-20 // FILE: /home/alice/.maya_notes/Maya_04.txt
// ============================================================================

Javi kept writing about how the up and down arrow keys and the tab key "saved
my fingers from having to type more than I need to." He was always kind of lazy.

But so am I. So I tried using them and kept getting errors — nothing was
completing, nothing was recalling.

Buried in one of his technical notes he explained that his shell profile had
gotten wiped once. A file called '.bashrc' in his home folder — the one that
configures how the terminal behaves — was missing. Without it, Tab and the
arrow keys basically go dead. He said he had to restore it from a backup he
kept at /opt/backup/profiles/.

I patched mine from there. If you're reading this and your terminal feels
broken: check /opt/backup/profiles/ first.

— Maya
// ============================================================================
```

---

## 5. Integration Recommendations

### File Placement
Maya's notes should live at `/home/alice/.maya_notes/` — a hidden directory (dot-prefix) the player finds after running `ls -a`. This gives them a **natural reward** for using the flag Morgan's note teaches them, and distinguishes Maya's personal archive from Morgan's operational scratchpads.

### Discovery Trigger
The first note (`Maya_00`) could be surfaced by Morgan's Phase 0 `.note.txt`, with a line like:
> *"You're not the first person to sit at this terminal confused. Someone named Maya left personal logs in '.maya_notes/' — her notes are less technical than mine, but they might help you get your bearings."*

### Arc Potential
Maya's notes currently cover Phase 0 fundamentals. If you extend the arc, consider:
- **Maya_05**: She discovers `grep` and starts auditing Javi's logs
- **Maya_06**: She finds something she wasn't supposed to — a hint at what eventually becomes the 2042 breach
- This makes Maya's story not just educational scaffolding but a **foreshadowing thread** woven into the investigation

---

*Audit by: Narrative Architect Persona // Terminal Zero Continuity Review*
