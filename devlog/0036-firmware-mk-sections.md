# 0036 — Firmware Makefile: client-py-style sections

- GH issue: #36
- Branch: impl/0036-firmware-mk-sections
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (cosmetic; no behaviour change).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Restructure `server-esp32s3-rtft/Makefile` to mirror `client-py/Makefile`: CONVENTIONS header, `## TITLE:: ##` section markers, the section-rendering `help` target, and a Notes footer.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Adopt the client-py header + help target verbatim; group targets into General / Setup / Quality / Build and flash sections; move the board-settings note into a Notes footer. Targets themselves unchanged.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- `make help` renders the four sections + Notes (same layout as client-py).
- `make -n firmware-upload` still expands to compile then `upload … -t` (deps + commands unchanged).

### 3.2 Verdict

Accept.

## Governance trace

| Source                  | Clause          | Action  | Note                                   |
| ----------------------- | --------------- | ------- | -------------------------------------- |
| CLAUDE.md (consistency) | shared idioms   | applied | firmware Makefile mirrors client-py    |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~5k             | ~6 min    |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 2 (Makefile, devlog) |
