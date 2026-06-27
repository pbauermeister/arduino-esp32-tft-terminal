# 0015 — Per-subproject READMEs; tidy doc cross-linking

- GH issue: #15
- Branch: impl/0015-subproject-readmes
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (doc-only). Scope from `TODO.md` item 4 (H2b + H2c).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Add a README to each subproject and make the doc family coherently indexed.

### Acceptance criteria

1. `client-py/README.md`, `server-esp32s3-rtft/README.md`, `case-esp32s3-rtft/README.md` exist.
2. Each links back to the top README and the relevant `README-*` docs.
3. Top README's three-parts bullets link into each subproject (top README = doc index).
4. All links resolve.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. Write three bullet-first subproject READMEs (purpose, requirements/build, layout, cross-links).
2. Link the top README's three-parts bullets to the subproject directories.
3. Keep `client-py/README.md` usage-focused (its layout changes in packaging/Task P).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Deviations

- **H2c done without moving files**: the top README's Documentation section + the new subproject cross-links already form the index. Moving `README-protocol`/`README-animations`/`README-VSCODE` into a `docs/` folder was rejected (YAGNI — breaks URLs and history for no gain).

### 3.3 Verification

- All inter-file links in the new READMEs and the top README verified to resolve on disk.

### 3.4 Retrospective

| #   | Point                                                       | Agent | User |
| --- | ----------------------------------------------------------- | ----- | ---- |
| 1   | client-py README kept usage-focused to survive the P restructure | well |   |
| 2   | No file moves for H2c (index already emergent)              | well  |      |

### 3.5 Verdict

Accept.

## Governance trace

| Source                             | Clause             | Action  | Note                          |
| ---------------------------------- | ------------------ | ------- | ----------------------------- |
| CEREMONIES.md (doc-only carve-out) | doc-only fast-path | applied | slim devlog                   |
| CLAUDE.md (YAGNI)                  | YAGNI              | applied | no `docs/` move for H2c       |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~12k            | ~12 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 5     |
