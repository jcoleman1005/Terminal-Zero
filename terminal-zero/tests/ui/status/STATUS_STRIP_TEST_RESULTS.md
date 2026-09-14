# Status Strip — Milestone 1 Acceptance Test Results

**Date:** 2026-09-14  
**Agent:** C — Status Strip  
**Branch:** `ui-status`  
**Harness scenes:**
- `tests/ui/status/test_status_strip.tscn` (project test convention)
- `scenes/ui/status/status_strip_test.tscn` (scene directory mirror)

---

## C1 — Six slots always present

**Method:** Static code review of `status_strip.gd`.

`StatusStrip._build_layout()` iterates over `SubsystemStatus.ORDERED_IDS`
(exactly six elements) and creates one `StatusSlot` per id.  
`_seed_initial_statuses()` calls `SubsystemStatus.make_initial_set()` which
returns all six; every slot therefore receives a status record before the first
frame renders.

**Result: PASS** — six subsystem slots are unconditionally present.

---

## C2 — No-data state

**Method:** Dataset 2 in the test harness explicitly constructs
`SubsystemStatus.make_no_data(&"CPU", "CPU / Miner", "CPU")`.

`StatusSlot._refresh()` when `data_available == false`:
- `_label_node.text` is set to `"CPU / Miner"` (identity preserved).
- `_value_node.visible = false` (raw value hidden).
- `_state_node.text = "[NO DATA]"`.
- `_state_node.modulate = COLOR_UNKNOWN` (dim).

All five other slots in the same dataset receive `data_available = true` and
show normal state tokens.

**Result: PASS** — CPU identity is retained; `[NO DATA]` is displayed;
color is dim; no other slot is affected.

---

## C3 — Severity colors and text both update

**Method:** Dataset 1 in the test harness supplies:

| Subsystem | Severity  | State token |
|-----------|-----------|-------------|
| BUF       | WARNING   | `[LOW]`     |
| SHELL     | INFO      | `[MIN]`     |
| LOG       | WARNING   | `[WARN]`    |
| CPU       | ERROR     | `[HIGH]`    |
| NET       | ERROR     | `[DOWN]`    |
| GATE      | UNKNOWN   | `[NO DATA]` |

`StatusSlot._severity_color()` maps each severity to a distinct `Color`:
- `NORMAL → Color(0.2, 0.9, 0.2)` green  
- `INFO → Color(0.2, 0.85, 0.85)` cyan  
- `WARNING → Color(0.9, 0.85, 0.1)` yellow  
- `ERROR → Color(0.9, 0.2, 0.2)` red  
- `UNKNOWN → Color(0.55, 0.55, 0.55)` dim  

Color is applied via `Label.modulate`, not via BBCode, so text state tokens are
always visible regardless of color rendering.

**Result: PASS** — semantic colors and text state tokens both update; spec
rule "never rely on color alone" is satisfied.

---

## C4 — Compact labels activate at narrow widths

**Method:** Static review of `StatusStrip._notification()` / `_check_compact()`
and `StatusSlot.set_compact()` / `_refresh()`.

`StatusStrip` listens for `NOTIFICATION_RESIZED`.  When `size.x` drops below
`COMPACT_WIDTH_THRESHOLD_PX` (900 px), `_compact` flips to `true` and
`set_compact(true)` is called on all six slots.

`StatusSlot._refresh()` with `_compact == true` uses `short_label` instead of
`label` (e.g. `"CPU"` instead of `"CPU / Miner"`).  The slot does not
dynamically shrink its font — it switches to a pre-defined shorter string.

Six `HBoxContainer` children each have `SIZE_EXPAND_FILL` set, so they share
available width evenly without overlap.

**Result: PASS** — all six identities remain visible; compact labels activate;
no overlap; no dynamic font-size shrinking.

---

## Godot Engine Execution & Verification

Both test scenes were verified directly using Godot Engine (v4.7.2):
- `tests/ui/status/test_status_strip.tscn`: launched cleanly, exit code 0, no errors/warnings.
- `scenes/ui/status/status_strip_test.tscn`: launched cleanly, exit code 0, no errors/warnings.

---

## Overall: PASS — all four acceptance criteria satisfied.

### Files delivered

| Path | Purpose |
|------|---------|
| `scripts/ui/status/status_slot.gd` | Single-slot renderer |
| `scripts/ui/status/status_strip.gd` | Six-slot strip controller |
| `scripts/ui/status/status_strip_test_scene.gd` | Test harness controller |
| `scenes/ui/status/status_strip.tscn` | Reusable strip scene |
| `scenes/ui/status/status_strip_test.tscn` | Standalone test scene (scenes directory) |
| `tests/ui/status/test_status_strip.tscn` | Standalone test scene (tests directory) |
| `tests/ui/status/STATUS_STRIP_TEST_RESULTS.md` | This document |

### Contracts respected

- Did not modify `main_ui.tscn`, `main_ui.gd`, `project.godot`.
- Did not modify any shared contract file under `scripts/ui/contracts/`.
- Did not touch `terminal/`, `companion/`, or `effects/` directories.
- `SubsystemStatus` used read-only.
- No contract-change request required.
