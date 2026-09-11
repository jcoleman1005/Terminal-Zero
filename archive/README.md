# Terminal Zero // Archive

This directory stores historical documents, early prompt specifications, and resolved audit checklists preserved for reference.

---

### Archived Documents Index

| File | Original Purpose | Reason for Archival | Current Source of Truth |
| :--- | :--- | :--- | :--- |
| `TERMINAL_ZERO_GDD_v1.md` | Initial Game Design Document (v1.0). | Superseded by GDD v2.0. Contained cut platforms (Termux), episodic missions, scoring/grading, and interactive pagers. | [`TERMINAL ZERO GDD v2.md`](../TERMINAL%20ZERO%20GDD%20v2.md) |
| `Milestone_Critiques_RESOLVED.txt` | Engineering review identifying runtime bypasses and softlocks. | All items (daemon precondition checks, socket boot sanitization, `.bashrc` write hooks, strict `kill -9` signal evaluation, and backup templates) are fully resolved in the engine. | [`terminal_zero/`](../terminal_zero/) |
| `gemini_coding_instructions_v3.md` | Technical prompt specification for the hardened prototype. | Assumed a single flat `Prototype.txt` file and old `APOLLO` naming. The codebase is now a modular Python package. | [`terminal_zero/`](../terminal_zero/) & [`scripts/bundle.py`](../scripts/bundle.py) |
| `gemini_milestone_progression_instructions.md` | Initial milestone progression prompt specification. | Superseded by v3 master instructions and current production codebase. | [`Milestone Progression.md`](../Milestone%20Progression.md) & [`GAME_NOTES_AND_CLUES.md`](../GAME_NOTES_AND_CLUES.md) |
