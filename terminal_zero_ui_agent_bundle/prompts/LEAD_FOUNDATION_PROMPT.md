# Lead / Foundation Agent Prompt

You are the lead implementation agent for TERMINAL ZERO's Godot UI migration.

Read:
- `docs/ui/TERMINAL_ZERO_UI_SPEC.md`
- `docs/ui/CONTRACTS.md`

Your task is ONLY to establish the shared foundation required for parallel agents.

Create/finalize:
- `scripts/ui/contracts/`
- shared semantic types
- backend adapter interface/stub
- directory structure for terminal/companion/status/effects
- empty or minimal root UI integration scaffold
- input action names needed by the components
- standalone test-scene conventions

Do not implement visual polish or complete UI systems.

You are the only agent allowed to modify:
- `scenes/ui/main_ui.tscn`
- `scripts/ui/main_ui.gd`
- `project.godot`
- shared contract/type files
- shared Theme resources

Before finishing:
1. Ensure all parallel agents can work without editing shared files.
2. Document exact contract filenames and APIs.
3. Create a commit suitable as the common base for all worktrees.
4. Report any mismatch between this design bundle and the existing project architecture.

Recommended commit message:
`ui: establish Terminal Zero UI contracts and parallel agent foundation`
