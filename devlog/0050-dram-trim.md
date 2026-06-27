# 0050 — Firmware: trim transaction DRAM, lift core pin to 3.3.10

- GH issue: #50
- Branch: impl/0050-dram-trim
- Opened: 2026-06-28
- Closed: 2026-06-28

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Free enough static DRAM that the firmware fits on a newer esp32 core, then lift the `3.3.0` pin. (Was: 84% RAM on 3.3.0; 3.3.10 overflowed `dram0_0_seg` by ~4 KB.)

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

The DRAM hog is `Transaction::actions[1000]`, each `Action` carrying `str[BUFFER_LENGTH=200]` — paid 1000×, mostly unused (only `print` uses `str`). Chose **idea 2 (shrink `str`)** over shrinking the FIFO depth: it keeps the 1000-deep frame budget, so it can't introduce mid-frame auto-flush flicker.

1. New `PRINT_LENGTH` (128) for `Action.str`; keep `BUFFER_LENGTH` (200) for the command buffers.
2. Fix `Action::set(h,text)`: `strncpy` + explicit null-terminate (the old call didn't terminate on overflow — newly relevant as `str` shrinks).
3. Fix `Transaction::add()` overflow bug: `next == sizeof(actions) - 1` compared the index against the array's **byte size** (~236007), so the auto-commit-when-full never fired. Now `next == ACTIONS_COUNT - 1`.
4. Lift the pin to `esp32:esp32@3.3.10` (Makefile + CI cache key).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- **DRAM: 84% → 62%** (`Action` 236 B → 164 B; 1000× = ~72 KB freed; 121 KB now free). `format-check` clean.
- **Fits on 3.3.10**: confirmed by this PR's `firmware-build` CI job (new cache key installs 3.3.10 and compiles).
- **Hardware test (pending)**: rebuild on 3.3.10 + flash via ROM download mode + runtime-test the draw-heavy apps. Done as a separate, user-attended step given the flash fragility seen in #48.

### 3.2 Notes

- Two latent bugs found and fixed alongside the trim (non-terminated `strncpy`, `sizeof`-vs-count FIFO overflow) — both in the buffer being shrunk.
- `PRINT_LENGTH` (firmware) and any future client-side print chunking must agree — a candidate for the protocol single-source (J).

### 3.3 Verdict

Accept once CI is green and the board is reflashed + smoke-tested.

## Governance trace

| Source                      | Clause          | Action  | Note                                          |
| --------------------------- | --------------- | ------- | --------------------------------------------- |
| CLAUDE.md (Proportionality) | simplest fit    | applied | str-shrink (no flicker) over FIFO-depth cut   |
| CLAUDE.md (Fact/inference)  | flag findings   | applied | two latent buffer bugs fixed, not hidden      |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~22k            | ~30 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 5 (config.h, transaction.h, transaction.cpp, Makefile, ci.yml, devlog) |
