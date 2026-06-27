# 0007 — Hygiene: .gitignore caches, relocate load.sh, deprecation note

- GH issue: #7
- Branch: impl/0007-hygiene
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (mechanical, scope from `TODO.md` item 1).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

First task of the cleanup/refactoring slate (`TODO.md`).
Scope, quoted from `TODO.md` item 1, accepted on 2026-06-27:

> **Hygiene** (A) — `.gitignore` (caches, `dist/`, `.venv/`); remove
> `.mypy_cache/`; relocate `client-py/load.sh` → `scripts/`; add
> `server-featherwing--obsolete/DEPRECATED.md`. Dead apps
> (`bumps.py`, `road.py`) stay inactive/unlinked.

### Acceptance criteria

1. `.gitignore` ignores `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `.venv/`, `dist/`, `*.egg-info/`.
2. No `.mypy_cache/` in the working tree.
3. `load.sh` lives in `scripts/`, no longer under `client-py/`.
4. `server-featherwing--obsolete/` carries a `DEPRECATED.md` note.
5. `bumps.py` and `road.py` untouched (remain inactive/unlinked).

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Mechanical, no design decisions:

1. `git mv client-py/load.sh scripts/load.sh`.
2. `rm -rf .mypy_cache` (untracked; local only).
3. Append cache/build patterns to `.gitignore`.
4. Write `server-featherwing--obsolete/DEPRECATED.md`.

Verification: `git status` shows only the intended changes; `git grep load.sh` confirms no stale references in code.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Deviations

None. `.mypy_cache/` was already untracked, so its removal is a working-tree cleanup only (no git delete).

### 3.2 File inventory

- `.gitignore` — added 6 ignore patterns.
- `client-py/load.sh` → `scripts/load.sh` — rename (content unchanged).
- `server-featherwing--obsolete/DEPRECATED.md` — new.
- `devlog/0007-hygiene.md` — this file.

### 3.3 Verification

- `git status`: only the intended rename, new files, and `.gitignore` edit.
- `git grep -n 'load.sh'`: no references in code (only `TODO.md`/devlog prose).

### 3.4 Retrospective

| #   | Point                                            | Agent | User |
| --- | ------------------------------------------------ | ----- | ---- |
| 1   | Scope fully mechanical; fast-path fit was right  | well  |      |
| 2   | `.mypy_cache` already untracked — less to do     | well  |      |

### 3.5 Verdict

Accept.

## Governance trace

| Source           | Clause                | Action  | Note                              |
| ---------------- | --------------------- | ------- | --------------------------------- |
| CEREMONIES.md:77 | fast-path task flow   | applied | mechanical scope from TODO item 1 |
| CLAUDE.md:60     | devlog + issue + branch | applied | #7, impl/0007-hygiene             |

## Resource consumption

| Phase     | Tokens (approx) | Wall time |
| --------- | --------------- | --------- |
| Mandate   | ~3k             | 2 min     |
| Execution | ~5k             | 5 min     |
| Closure   | ~3k             | 3 min     |
| **Total** | **~11k**        | **~10 min** |

| Counter                | Value |
| ---------------------- | ----- |
| Pre-commit hook fails  | 0     |
| Subagent invocations   | 0     |
| `/clear` events        | 0     |
| Memory rotation events | 0     |
| LOC changed            | small |
| Files changed          | 4     |
