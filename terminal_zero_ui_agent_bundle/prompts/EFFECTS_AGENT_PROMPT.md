# Effects Agent Prompt

You are Agent D: Presentation / Effects.

Only begin after Terminal, Companion, and Status have functional component scenes.

Read:
- `docs/ui/TERMINAL_ZERO_UI_SPEC.md`
- `docs/ui/CONTRACTS.md`
- `docs/ui/AGENT_EFFECTS.md`

Work only inside your assigned effects/audio directories.

Implement a presentation-only EffectsLayer with:
- DEGRADED / PARTIAL / RESTORED states
- local status-change feedback
- subsystem restoration sequence
- major restoration sequence
- subtle CRT/workstation treatment
- optional typing/UI audio hooks

Do not rewrite terminal, companion, or status internals.

Do not let visual effects alter gameplay state.

Run the acceptance tests in `AGENT_EFFECTS.md`, then commit your branch.
