# Terminal Zero — Elevator Pitch

---

## The Hook

It's 2042. A cyber incident has crippled workstation **OSIRIS** — the last node tethering the PHOENIX emergency power grid to the northern district. You are operator **Alice**. You wake up to a blinking cursor, a shell with no history recall, no `.bashrc`, and six subsystems in the red. There is no tutorial pop-up. There is no quest marker. There is only the terminal.

---

## The Game

**Terminal Zero** is a *terminal metroidvania* — an investigation game played entirely inside a real Linux shell. You learn the command line not through drills or exercises, but because the story **requires** it. Auditing `/var/log/auth.log` exposes a breach. `kill`ing a rogue miner frees the CPU. `chmod +x recovery.sh` arms a dormant payload. `ip link set osiris0 up` brings the network back from the dead. Every command is authentic POSIX. Every error message is real. Every discovery is yours.

Three decoupled investigation spokes — Compute, Storage, Network — can be tackled in any order. Solve all three and you earn the right to fire `cluster_probe`, handing control of OSIRIS back to the PHOENIX mesh. The final words belong to Morgan, your unseen handler:

> *"I don't know who you were before this system crashed, but you just audited logs, re-linked POSIX line disciplines, managed processes, and brought a dead infrastructure cluster back to life from a raw command prompt. Take a breath. You're no longer typing in the dark."*

---

## The Audience

Terminal Zero is for **complete beginners who learn by doing**, gamers who love environmental storytelling (*Outer Wilds*, *Hacknet*), and educators who want a tool that respects the learner's intelligence. There are no artificial gates, no XP bars, no syntax hints on a HUD. The game trusts you to explore — and when you finally get it, it feels earned.

---

*Genre: Terminal Metroidvania / Educational CLI Investigation*
*Stack: Python 3, pure POSIX emulation, zero external dependencies at runtime*
*Status: Vertical slice complete — 13 playtests, 1,013 recorded commands, zero crashes*
