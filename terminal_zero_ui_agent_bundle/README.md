# TERMINAL ZERO — Parallel UI Agent Bundle

This bundle is designed to help you migrate TERMINAL ZERO's working Python CLI prototype into a Godot-based terminal/TUI presentation using multiple parallel coding agents and Git worktrees.

## What this bundle contains

- `docs/ui/TERMINAL_ZERO_UI_SPEC.md` — the full design source of truth.
- `docs/ui/CONTRACTS.md` — shared interfaces and ownership rules that all agents must obey.
- `docs/ui/AGENT_TERMINAL.md` — scope and milestones for the Terminal Core agent.
- `docs/ui/AGENT_COMPANION.md` — scope and milestones for the Companion Workspace agent.
- `docs/ui/AGENT_STATUS.md` — scope and milestones for the Status Strip agent.
- `docs/ui/AGENT_EFFECTS.md` — later-stage scope for the Presentation / Effects agent.
- `prompts/LEAD_FOUNDATION_PROMPT.md` — prompt for the lead/foundation agent.
- `prompts/TERMINAL_AGENT_PROMPT.md` — first prompt for the Terminal Core agent.
- `prompts/COMPANION_AGENT_PROMPT.md` — first prompt for the Companion Workspace agent.
- `prompts/STATUS_AGENT_PROMPT.md` — first prompt for the Status Strip agent.
- `prompts/EFFECTS_AGENT_PROMPT.md` — prompt for the Effects agent after the other UI pieces exist.
- `WORKTREE_SETUP.md` — recommended Git worktree flow.

## Recommended order

1. Copy the `docs/ui` and `prompts` folders into your project.
2. Run the lead/foundation task first.
3. Commit the shared contracts and directory structure.
4. Create three worktrees from that exact commit:
   - terminal
   - companion
   - status
5. Run one agent in each worktree using the matching prompt.
6. Each agent should build a standalone test scene and commit its own branch.
7. Merge them back one at a time on the integration branch.
8. Only after A/B/C work together, start the Effects agent.

## Core rule

The full UI spec is the source of truth, but agents should normally work from their smaller agent brief plus `CONTRACTS.md`.

If an agent needs a shared contract changed, it should document the requested change instead of independently editing shared interfaces.
