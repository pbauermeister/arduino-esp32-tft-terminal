# 0038 — Firmware: apply clang-format backlog

- GH issue: #38
- Branch: impl/0038-firmware-reformat
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (pure formatting; no behaviour change).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Bring `server-esp32s3-rtft/` sources in line with the committed `.clang-format` (Google, indent 4), isolated in one commit. Verify nothing semantic changed.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`make format` (clang-format `-i` over `*.ino`/`*.cpp`/`*.h`). Verify by comparing the compiled binary size against the pre-reformat baseline.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- 10 files reformatted (~1370 lines each way); no logic edits.
- **Binary unchanged**: compile is `498103` bytes (program) / `278336` bytes (globals) — identical to the pre-reformat baseline. Formatting cannot change the compiled output, and the byte counts confirm it. No re-flash needed.
- `make format-check` now exits 0 (sources are clang-format-clean).

### 3.2 Verdict

Accept.

## Governance trace

| Source                  | Clause          | Action  | Note                                        |
| ----------------------- | --------------- | ------- | ------------------------------------------- |
| CLAUDE.md (consistency) | enforce style   | applied | firmware now conforms to its own .clang-format |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~5k             | ~8 min    |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 11 (10 sources + devlog) |
