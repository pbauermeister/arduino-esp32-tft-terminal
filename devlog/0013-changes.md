# 0013 — Add CHANGES.md (version source, 0.1.0)

- GH issue: #13
- Branch: impl/0013-changes
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (doc-only). Scope from `TODO.md` item 4 (H2a).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Add `CHANGES.md` as the single version source, mirroring the `claude-busy-monitor` format so the Makefile/packaging (Task P) can extract the version via `awk -F'[ :]' '/^## Version /'`.

### Acceptance criteria

1. `# Changes` + `## Version 0.1.0:` structure (no date on the version line, matching cbm).
2. `awk -F'[ :]' '/^## Version / {print $3; exit}'` yields `0.1.0`.
3. Initial version 0.1.0 (user decision).

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. Create `CHANGES.md` with a `0.1.0` entry summarising the first-release scope (packaging + the cleanup landed so far).
2. Verify version extraction.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Deviations

- None. The 0.1.0 entry is forward-looking on the packaging bullet (Task P not yet done); CHANGES.md top entry conventionally accrues the in-progress release's scope and will gain bullets as G/P/tests/CI land.

### 3.3 Verification

- `awk -F'[ :]' '/^## Version / {print $3; exit}' CHANGES.md` → `0.1.0`.

### 3.4 Retrospective

| #   | Point                                                  | Agent | User |
| --- | ------------------------------------------------------ | ----- | ---- |
| 1   | Mirrored cbm format so the Makefile awk works verbatim | well  |      |

### 3.5 Verdict

Accept.

## Governance trace

| Source                             | Clause             | Action  | Note                                |
| ---------------------------------- | ------------------ | ------- | ----------------------------------- |
| CEREMONIES.md (doc-only carve-out) | doc-only fast-path | applied | slim devlog                         |
| CLAUDE.md (Preferences)            | code reuse         | applied | reused cbm CHANGES format/awk contract |

## Resource consumption

| Phase     | Tokens (approx) | Wall time |
| --------- | --------------- | --------- |
| Total     | ~6k             | ~6 min    |

| Counter                | Value |
| ---------------------- | ----- |
| Files changed          | 2     |
