# 0032 — Firmware Makefile targets + .clang-format

- GH issue: #32
- Branch: impl/0032-firmware-targets
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (mechanical). Scope from `TODO.md` (split out of G).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Give the firmware (`server-esp32s3-rtft/`) the same `make` ergonomics as the client: a committed `.clang-format` and `arduino-cli` build/upload targets.

### Acceptance criteria

1. `.clang-format` matching the documented style (Google, IndentWidth 4).
2. `server-esp32s3-rtft/Makefile`: `help`, `format`, `format-check`, `firmware-build`, `firmware-upload`, `require`.
3. Targets use the correct FQBN/options (from `.vscode/arduino.json`).
4. `require` bootstraps the whole toolchain (installs `arduino-cli` itself, not just the core).
5. `firmware-upload` is proven against real hardware, not just present.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`.clang-format` (Google/indent-4); Makefile with clang-format format/check + `arduino-cli compile`/`upload` (FQBN `esp32:esp32:adafruit_feather_esp32s3_reversetft` + key board options) + a `require` (core install).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- `make help` lists all targets.
- `make format-check` runs clang-format and reports violations (the tool works).
- `make firmware-build` invokes `arduino-cli compile -b <fqbn:opts> .` correctly (reaches the compiler).
- `require` now installs `arduino-cli` (official script → `~/.local/bin`) if absent, then the esp32 core.
- **`firmware-upload` tested on real hardware** (needed the #35 build fix, merged in): build → flash → `-t` verify (`Hash of data verified`, hard reset, exit 0). Post-flash the board answers the protocol: `width → 240`, `height → 135`, `display → OK`.

### 3.2 Two findings (NOT fixed here — flagged)

1. **Firmware isn't clang-format-clean** (~2730 lines would change). The `.clang-format` + `format` target are committed, but the existing sources were never strictly formatted. Not reformatted here: it's a large diff with no automated behaviour check, and reformatting working firmware deserves a separate, on-board-reverified step (`make format`, then a hardware smoke).
2. **Firmware does not compile on esp32 core 3.3.0** — `command.cpp`'s `case hash("…"):` labels are `unsigned int` values above `INT_MAX` (e.g. 4071076125); the newer core's `-Werror=narrowing` rejects them. The current VS Code build must use an older core / laxer flags. The fix is small (make the hash/switch consistently `unsigned`), but it's a firmware **code** change, out of this task's scope and unverifiable without the board.

### 3.3 Retrospective

| #   | Point                                                          | Agent | User     |
| --- | -------------------------------------------------------------- | ----- | -------- |
| 1   | `firmware-build` immediately surfaced a real core-compat bug   | well  |          |
| 2   | Did not reformat 2730 lines blind / did not fix firmware here  | well  |          |

### 3.4 Verdict

Accept (targets correct and verified to run). The two findings are follow-up candidates, not blockers.

## Governance trace

| Source                  | Clause          | Action  | Note                                         |
| ----------------------- | --------------- | ------- | -------------------------------------------- |
| CLAUDE.md (Proportionality) | proportionality | applied | tooling only; no blind reformat / firmware fix |
| CLAUDE.md (Fact/inference)  | mark findings   | applied | narrowing + non-conformance flagged, not hidden |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~14k            | ~15 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 3 (.clang-format, Makefile, devlog) |
