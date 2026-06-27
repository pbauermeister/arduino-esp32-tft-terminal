# 0046 — Top-level signpost Makefile

- GH issue: #46
- Branch: impl/0046-top-makefile
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

A repo-root `Makefile` that builds nothing; running `make` points to where the real work lives (the sub-makefiles), and hints that the tests are in `client-py/` (a running app is needed to drive the board).

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`Makefile` with `.DEFAULT_GOAL := help`; `help` echoes the two sub-projects (`client-py/`, `server-esp32s3-rtft/`) and their `make help`, with the tests-live-in-client-py note. No build targets.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- `make` (default goal) prints the signpost; no build is attempted.

### 3.2 Verdict

Accept.

## Governance trace

| Source                | Clause          | Action  | Note                                  |
| --------------------- | --------------- | ------- | ------------------------------------- |
| CLAUDE.md (Naming)    | outcome-named   | applied | root `make` = discoverability signpost |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~4k             | ~5 min    |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 2 (Makefile, devlog) |
