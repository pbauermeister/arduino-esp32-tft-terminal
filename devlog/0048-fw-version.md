# 0048 — Firmware: version command + CHANGES.md (build-injected)

- GH issue: #48
- Branch: impl/0048-fw-version
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task. Flashed as its own checkpoint (before the riskier DRAM trim).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Add a board `version` command returning the firmware version, maintained in a firmware `CHANGES.md` (same `## Version X.Y.Z:` format as `client-py/`) and injected at build time.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. `server-esp32s3-rtft/CHANGES.md` — `## Version 0.1.0:`.
2. Makefile: `version.h` generated from CHANGES.md (`#define FW_VERSION`); `firmware-build` depends on it; `version.h` excluded from `SRC` (format) and git-ignored.
3. `command.cpp`: `#include "version.h"` + `case hash("version"): return FW_VERSION;`.
4. Client: on connect (`board._configure`), print the firmware version alongside the resolution. Query the new command with a try/except fallback to `unknown` for older firmware.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- Build: `version.h` → `FW_VERSION "0.1.0"`; compiles 498187 bytes flash, **278336 globals (DRAM unchanged** — the string lives in flash). `format-check` clean.
- **Hardware-verified** (after a flash-recovery detour, see Notes): via `client-py`, the board answers `width 240`, `height 135`, **`version 0.1.0`**.
- Client on connect now prints `firmware version: 0.1.0` under the resolution (hardware-confirmed). Host suite: ruff clean, 24 tests pass.

### 3.2 Notes — flash recovery

- The first esptool flash hit "chip stopped responding" mid-write, leaving a partial app → the board fell into a reboot loop / tinyuf2 disk mode. Recovered by entering **ROM download mode** (hold BOOT, tap RESET) and re-flashing — completed cleanly. Then a physical RESET booted the app.
- Verification must use `client-py` (which handles the reset/READY handshake), not raw pyserial — opening the CDC port with DTR asserted re-triggers the bootloader.

### 3.3 Verdict

Accept.

## Governance trace

| Source                  | Clause            | Action  | Note                                      |
| ----------------------- | ----------------- | ------- | ----------------------------------------- |
| CLAUDE.md (consistency) | shared versioning | applied | firmware version maintained like client-py |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~16k            | ~25 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 5 (CHANGES.md, .gitignore, Makefile, command.cpp, devlog) |
