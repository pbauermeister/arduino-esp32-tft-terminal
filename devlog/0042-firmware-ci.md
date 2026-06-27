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
- The core install pins to whatever `esp32:esp32` is current; if a future core breaks the build, this job is exactly what flags it.

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
