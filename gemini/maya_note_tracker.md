# Maya Note Tracker
*Terminal Zero // Content Pipeline Status*

> [!IMPORTANT]
> **Maya's notes are not yet in the VFS.** All 5 drafted entries exist only in `Narrative/Narrative For Terminal Zero.txt`.
> When you're ready to ship them, they need to be added to `initial_vfs.py` at `/home/alice/.maya_notes/`.
> The corrected text for each shipped note is in [`gemini/maya_narrative_audit.md`](file:///home/jcoleman/Documents/Terminal-Zero/gemini/maya_narrative_audit.md).

---

## Shipped ✅ (Drafted — awaiting VFS integration)

| Note | VFS Path | Topic | Status |
|---|---|---|---|
| `Maya_00` | `/home/alice/.maya_notes/Maya_00.txt` | `cd` basics — moving around directories | ✅ Drafted, corrected |
| `Maya_01` | `/home/alice/.maya_notes/Maya_01.txt` | `ls -a` — hidden dot-files | ✅ Drafted, corrected |
| `Maya_02` | `/home/alice/.maya_notes/Maya_02.txt` | `touch` — creating blank files | ✅ Drafted, corrected |
| `Maya_03` | `/home/alice/.maya_notes/Maya_03.txt` | `cd ..` — going up a directory | ✅ Drafted, corrected |
| `Maya_04` | `/home/alice/.maya_notes/Maya_04.txt` | `.bashrc` / shell profile — why Tab/arrows break | ✅ Drafted, corrected |

---

## Needs Drafting ✍️

These notes extend Maya's arc into the investigation phases. Morgan already covers the *how* — Maya's notes should cover the *why it confused her* and what she stumbled onto.

| Note | VFS Path | Suggested Topic | Game Phase |
|---|---|---|---|
| `Maya_05` | `/home/alice/.maya_notes/Maya_05.txt` | **`head` / `tail` / `grep`** — Maya finds auth.log too big to read with `cat`, learns to filter it. Lore nugget: she sees something alarming at line 45 but doesn't know what a PID is. | Phase 2 — Log Forensics |
| `Maya_06` | `/home/alice/.maya_notes/Maya_06.txt` | **`find`** — Maya hunts for Javi's old scripts scattered in `/mnt/recovery`. Discovers that wildcards (`*.sh`) are a thing. Lore nugget: she mentions a script Javi wrote but couldn't run because "it had the wrong letters." | Phase 3 — Recovery Search |
| `Maya_07` | `/home/alice/.maya_notes/Maya_07.txt` | **`chmod` / permissions** — Maya finally figures out why Javi's script wouldn't run. Lore nugget: she describes running `ls -l` and seeing `----------` and having no idea what it meant, then finding a note from Javi explaining the `x` bit. | Phase 3 — Permissions |
| `Maya_08` | `/home/alice/.maya_notes/Maya_08.txt` | **`ps aux` / `kill`** — Maya notices the machine running hot and finds a runaway process. Lore nugget: Javi left a note warning her never to `kill -9` anything without knowing the PID first — she of course does it wrong the first time. | Phase 4 — Process Table |
| `Maya_09` | `/home/alice/.maya_notes/Maya_09.txt` | **Lore nugget — Javi** — No technical instruction. Maya finds one of Javi's older personal notes and reflects. Reveals that Javi was self-taught, learned Linux entirely from forum posts, and had been running OSIRIS alone for 9 years before he died. Emotional beat before the finale. | Between Phase 4 and Phase 5 |
| `Maya_10` | `/home/alice/.maya_notes/Maya_10.txt` | **Last entry** — Maya's goodbye. She got the machine running, sort of, but she's leaving. She's not a sysadmin. She writes instructions for whoever comes next (Alice) and says she's leaving Morgan's contact info taped to the monitor. Closes the chain: Javi → Maya → Alice. | Pre-game / ambient lore |

---

## Notes on Morgan's Existing Coverage

For reference — Maya should never duplicate Morgan's operational syntax exactly.
Morgan owns the *technical authority* voice. Maya owns the *human fumbling* voice.

| Phase | Morgan Has | Maya's Angle |
|---|---|---|
| Phase 0 | `pwd`, `ls`, `cat`, `repair_buffer` | `cd`, `ls -a`, `touch`, `cd ..`, `.bashrc` (different commands, no overlap) |
| Phase 2 | `head`, `grep -i`, exact syntax | Maya sees the same log, doesn't know what she's looking at |
| Phase 3 | `find` exact syntax, `chmod +x`, `./recovery.sh` | Maya discovers `find` by accident, can't run Javi's script |
| Phase 4 | `ps aux`, `kill 102`, `kill -9 104` | Maya's first encounter with a hot machine and a runaway process |
| Phase 5 | `ip link set osiris0 up`, `ping` | *(No Maya note needed here — network is post-Maya era)* |
| Phase 6 | `>>`, `chmod 644`, `phoenix_daemon start` | *(No Maya note needed here — this is post-Maya era)* |

---

*Last updated: 2026-09-12*
