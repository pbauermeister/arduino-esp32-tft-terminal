# 0042 — Firmware: CI compile gate + require installs libraries

- GH issue: #42
- Branch: impl/0042-firmware-ci
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

A CI job must verify the firmware compiles (would have caught the esp32-core narrowing regression, #35). For reproducibility, `make require` must install the firmware's libraries too.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. `require`: one shell block, PATH-robust (works right after a fresh `arduino-cli` install); add `arduino-cli lib install` for Adafruit GFX, ST7735/ST7789, NeoPixel, TestBed, Button (BusIO + SdFat pulled as deps).
2. `ci.yml`: a `firmware-build` job — cache `~/.arduino15` + `~/Arduino`, then `make require` + `make firmware-build`.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- `make -n require` expands cleanly; `make help` shows the updated doc.
- `ci.yml` is valid YAML (`jobs: check, firmware-build`).
- All five library names resolve in the arduino-cli registry (checked locally).
- The job itself is validated by this PR's own CI run (first run populates the cache).

### 3.2 Notes

- `require` is one shell block so the `PATH` export reaches the `arduino-cli` calls whether it was just installed or pre-existing.
- **DRAM finding (CI surfaced it immediately):** the first CI run pulled core `3.3.10` (latest 3.3.x) and the link **failed** — `dram0_0_seg overflowed by 4224 bytes`. The firmware is near the static-RAM ceiling (84 % on 3.3.0), and 3.3.10 tips it over. Fix: **pin `esp32:esp32@3.3.0`** (the core the board is validated on) in `require` + the cache key, so dev/CI/board build the same. Reducing the firmware's DRAM headroom is a separate concern, parked.

### 3.3 Verdict

Accept once the PR's CI run is green.

## Governance trace

| Source                  | Clause          | Action  | Note                                       |
| ----------------------- | --------------- | ------- | ------------------------------------------ |
| CLAUDE.md (reproducibility) | one setup path | applied | CI and dev share `make require` for libs   |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~9k             | ~12 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 3 (Makefile, ci.yml, devlog) |
