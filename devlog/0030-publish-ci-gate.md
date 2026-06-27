# 0030 — publish-quality gates on green GitHub CI

- GH issue: #30
- Branch: impl/0030-publish-ci-gate
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (mechanical). Scope from issue #30 / user request.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`make publish-quality` must confirm GitHub CI for HEAD has finished and passed before a release — never publish a commit CI hasn't blessed. Pattern from pikett-ai-mvp `release-manage.py` (`gh ... checks --watch`).

### Acceptance criteria

1. New low-level `ci-green` target: find the CI run(s) for HEAD and wait, failing if any didn't succeed.
2. `publish-quality` runs `ci-green` first.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`ci-green`: `gh run list` filtered by `headSha` → `gh run watch <id> --exit-status` per run (waits + fails if not successful); error if no run exists (HEAD not pushed). Compose into `publish-quality`.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Notes

- `gh run watch --exit-status` returns immediately for a completed run, or blocks until completion — covers both "CI still running" and "CI done".
- Requires `gh` authenticated and HEAD pushed (footnote (3) in the Makefile).

### 3.2 Verification

- `make help` lists `ci-green`; `publish-quality` doc updated.
- `make ci-green` on a commit with a green run → finds it, watches, "all CI runs for HEAD passed", exit 0 (validated against the merged-F CI run).
- No-run guard: empty run list → exit 1 with a push-first message.

### 3.3 Retrospective

| #   | Point                                                | Agent | User |
| --- | ---------------------------------------------------- | ----- | ---- |
| 1   | Reused the pikett `gh ... --watch` release pattern   | well  |      |

### 3.4 Verdict

Accept.

## Governance trace

| Source                  | Clause           | Action  | Note                                |
| ----------------------- | ---------------- | ------- | ----------------------------------- |
| CLAUDE.md (Preferences) | established methods | applied | reused pikett release-gate pattern  |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~8k             | ~10 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 2 (Makefile, devlog) |
