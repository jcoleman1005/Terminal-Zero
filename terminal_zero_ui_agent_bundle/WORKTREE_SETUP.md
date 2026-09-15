# TERMINAL ZERO — Git Worktree Setup

## 1. Add the planning bundle to your project

Copy these folders into the repository:

```text
docs/ui/
prompts/
```

## 2. Run the lead/foundation task first

Use:

```text
prompts/LEAD_FOUNDATION_PROMPT.md
```

Let the lead agent establish:
- shared contracts
- root UI scaffold
- input action names
- directory ownership
- shared types

Review the result.

Then commit it.

Recommended:

```bash
git add .
git commit -m "ui: establish Terminal Zero UI contracts and parallel agent foundation"
```

## 3. Create parallel worktrees

From the repository containing the foundation commit:

```bash
git worktree add ../tz-terminal -b ui-terminal
git worktree add ../tz-companion -b ui-companion
git worktree add ../tz-status -b ui-status
```

You now have:

```text
../terminal-zero      # integration/main worktree
../tz-terminal        # Agent A
../tz-companion       # Agent B
../tz-status          # Agent C
```

Open one coding-agent session in each worktree.

## 4. Give each agent only its prompt

Terminal:
```text
prompts/TERMINAL_AGENT_PROMPT.md
```

Companion:
```text
prompts/COMPANION_AGENT_PROMPT.md
```

Status:
```text
prompts/STATUS_AGENT_PROMPT.md
```

The prompts direct each agent to the full spec, contracts, and its own brief.

## 5. Require each agent to commit its branch

Example:

```bash
git add .
git commit -m "ui: add functional terminal core"
```

or:

```bash
git commit -m "ui: add companion document workspace"
```

or:

```bash
git commit -m "ui: add OSIRIS status strip"
```

## 6. Merge one at a time on the integration worktree

Back in the main/integration worktree:

```bash
git merge ui-terminal
```

Test.

Then:

```bash
git merge ui-status
```

Test.

Then:

```bash
git merge ui-companion
```

Test.

Recommended merge order:
1. terminal
2. status
3. companion

## 7. Resolve integration only in the integration worktree

The integration owner may modify:
- `main_ui.tscn`
- `main_ui.gd`
- `project.godot`
- shared theme
- shared contracts when a reviewed contract-change request requires it

Parallel agents should not fix cross-component integration by editing each other's files.

## 8. Start the Effects agent later

After Terminal, Status, and Companion are integrated:

```bash
git worktree add ../tz-effects -b ui-effects
```

Run:

```text
prompts/EFFECTS_AGENT_PROMPT.md
```

## 9. Clean up worktrees when finished

After branches are merged:

```bash
git worktree remove ../tz-terminal
git worktree remove ../tz-companion
git worktree remove ../tz-status
git worktree remove ../tz-effects
```

Delete branches later if desired:

```bash
git branch -d ui-terminal
git branch -d ui-companion
git branch -d ui-status
git branch -d ui-effects
```

## 10. Practical rule

Do not ask every agent to "implement the whole subsystem" in one shot.

Use one milestone at a time.

The first experiment should prove:
- agents obey directory ownership
- standalone test scenes work
- shared contracts are sufficient
- branches merge cleanly

Only then increase scope.
