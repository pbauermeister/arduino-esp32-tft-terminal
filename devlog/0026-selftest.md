# 0026 — On-board self-test (primitive gallery + buttons)

- GH issue: #26
- Branch: impl/0026-selftest
- Opened: 2026-06-27

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

An on-board acceptance suite (`make test-board`) verifying the firmware implements the USB protocol primitives, with no firmware change. Interactive parts front-loaded so the user is needed only briefly. Design settled across the 0024 study discussion.

### Acceptance criteria

1. Phase 1 interactive (attended): primitive gallery (glance y/n) + guided button presses (A/B/C + reset→`R`).
2. Phase 2 unattended: every client primitive sent and checked for a non-error response; query sanity; short soak (no comm errors / spurious reboots).
3. `make test-board` (opt-in, needs board; not CI). `make test` stays host-only.
4. Board-model-agnostic: coordinates derive from queried `WIDTH`/`HEIGHT` (only resolution/colour differ across boards; the obsolete FeatherWing is the precedent).

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`selftest.py` module: `connect()` (Channel+Board+configure), Phase 1 (`phase1_gallery`, `phase1_buttons`), Phase 2 (`phase2_unattended`), `main()` orchestrating interactive-then-unattended with a pass/fail `Results` summary and exit code. Makefile `test-board` target.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 What was built

- `src/arduino_esp32_tft_terminal/selftest.py` — the two-phase driver (24 primitive conformance checks, 3 gallery screens, A/B/C + reset button checks, 5 s soak).
- `Makefile` — `test-board` target; `test` relabelled "host unit tests (no board)".
- Gallery coordinates derive from `config.WIDTH`/`HEIGHT` → board-agnostic.

### 3.2 Verification done (agent, off-board)

- ruff clean; host pytest suite still 24/24.
- `FakeChannel` sanity run: all 3 gallery screens draw, all 24 primitives dispatch (no wrong method names), queries return values. Confirms the command set + structure.

### 3.3 Verification NOT done (needs the gadget — user)

- Phase 1 visual glance (rendering correctness) and the physical A/B/C/reset prompts — by definition need the board and a human.
- The reset→reboot→`R` detection across a serial drop is hardware-timing-dependent and may need tuning after a real run.

### 3.4 Retrospective

| #   | Point                                                        | Agent | User     |
| --- | ------------------------------------------------------------ | ----- | -------- |
| 1   | "board-dependent" conflated "needs hardware" with "board-specific" | not well | surprise |
| 2   | Gallery made resolution-driven once the protocol-agnostic point landed | well |    |
| 3   | Off-board sanity (FakeChannel) caught method-name risk pre-hardware | well |     |

### 3.5 Verdict

Accept pending the user's on-board run: structurally verified off-board; the interactive/hardware behaviour is theirs to confirm (and tune the reset detection if needed).

## Governance trace

| Source                       | Clause                  | Action  | Note                                              |
| ---------------------------- | ----------------------- | ------- | ------------------------------------------------- |
| CLAUDE.md (Proportionality)  | proportionality         | applied | human-in-the-loop, no FW change, no shadow buffer |
| CLAUDE.md (Fact/inference)   | mark unknowns           | applied | flagged the hardware-only verification gap        |
| devlog 0024                  | study outcome           | applied | interactive-first on-board suite as designed      |

## Resource consumption

| Phase     | Tokens (approx) | Wall time |
| --------- | --------------- | --------- |
| Implement | ~40k            | ~35 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 3 (selftest.py, Makefile, devlog) |
