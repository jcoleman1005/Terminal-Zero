# Agent Brief — Presentation / Effects

## Mission

Add OSIRIS visual and audio polish after Terminal, Companion, and Status components exist.

Start this agent later than the other three.

## Read first

- `docs/ui/TERMINAL_ZERO_UI_SPEC.md`
- `docs/ui/CONTRACTS.md`

## Owned directories

```text
scenes/ui/effects/
scripts/ui/effects/
assets/ui/effects/
audio/ui/
tests/ui/effects/
```

Do not rewrite terminal, companion, or status internals to achieve effects.

## First milestone

Implement a presentation-only EffectsLayer supporting:

```text
set_damage_state(state)
play_local_status_change(subsystem_id)
play_subsystem_restoration(subsystem_id)
play_major_restoration(event_id)
```

## Damage states

Start with only:
- DEGRADED
- PARTIAL
- RESTORED

Do not create a large progression matrix yet.

## Visual priorities

Resting OSIRIS:
- subtle phosphor bloom
- restrained scanline/noise texture
- very faint vignette
- almost no ambient movement

Routine changes:
- local pulse
- small sound cue

Subsystem restoration:
- stronger local animation
- brief ASCII diagnostic sequence
- phosphor bloom
- satisfying sound

Major restoration:
- full-screen ASCII sequence
- OSIRIS branding
- stronger but controlled distortion
- immediate return to readable workstation

## Hard rules

- no effect may hide puzzle-critical text
- no effect owns gameplay state
- all effects can be disabled
- avoid constant random glitches
- typing sound is optional/presentation-only

## Acceptance tests

### D1 — Disabled
Disable all effects.
Expected:
- UI remains completely usable

### D2 — Damage states
Switch DEGRADED → PARTIAL → RESTORED.
Expected:
- presentation changes
- layout does not break
- text remains readable

### D3 — Restoration
Trigger subsystem restoration.
Expected:
- presentation runs
- no game state changes
- no terminal output is injected
