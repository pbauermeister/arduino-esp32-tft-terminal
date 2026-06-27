# 0011 — Polish top-level README to reference-project finish

- GH issue: #11
- Branch: impl/0011-readme
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (doc-only carve-out). Scope from `TODO.md` item 3.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Bring the top-level `README.md` to the `dfd` reference level of finish, per `TODO.md` item 3.

### Acceptance criteria

1. Badges, tagline, hero image, structured sections mirroring `dfd/README.md`.
2. Accurate app catalogue (from `run.py` registry, incl. `claude-monitor`).
3. Three-part structure, quick start, install (hardware / firmware / client).
4. Existing motivation, videos, photos preserved; doc family linked.
5. All referenced media and file links resolve.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. Mirror `dfd` section order: title → badges → pitch → hero → apps → how-it-works → quick start → installing → docs → media → links.
2. Use absolute `raw.githubusercontent.com` image URLs (PyPI/robustness; `dfd` lesson).
3. App table by category from the `run.py` `all_apps` registry.
4. Forward-reference the not-yet-done bits honestly: pip-install (task P), CI/PyPI badges (tasks F/P) omitted rather than shown broken.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Deviations

- **Unnumbered `##` headings**, deviating from CLAUDE.md "headings always numbered in documents". Deliberate: the README mirrors `dfd/README.md` (the reference exemplar), and unnumbered headings are the README convention. Scoped to this external-facing file only.
- **CI and PyPI badges omitted** (only License/Python/Board shown): the CI workflow (task F) and PyPI release (task P) do not exist yet; showing broken badges would misrepresent state. To be added when F/P land.
- **Quick start uses source install**, not `pip install`: the package is not published yet (task P). Noted as forthcoming in the README.
- **Added scope (user request):** deleted the local duplicate `client-py/README-STATE-DETECTION.md` and redirected its two pointers (README Documentation link + `CLAUDE.md` Key documents) to the canonical copy in the `claude-busy-monitor` repo. The `CLAUDE.md` edit is a protected-file change reviewed via this PR before merge.

### 3.3 Verification

- All 13 referenced media files and 7 remaining file/doc links verified present on disk; the removed state-detection note now points to its canonical URL.

### 3.4 Retrospective

| #   | Point                                                          | Agent | User |
| --- | -------------------------------------------------------------- | ----- | ---- |
| 1   | Honest forward-references (no broken badges) over dfd-parity   | well  |      |
| 2   | App list taken from code registry, not the stale prose list    | well  |      |
| 3   | README numbering convention clashes with CLAUDE.md rule        | surprise |   |

### 3.5 Verdict

Accept (external-facing — user blesses wording before merge).

## Governance trace

| Source           | Clause                | Action  | Note                                            |
| ---------------- | --------------------- | ------- | ----------------------------------------------- |
| CLAUDE.md (Markdown formatting) | heading numbering | tension | unnumbered to match dfd README; scoped deviation |
| CLAUDE.md (YAGNI) | YAGNI               | applied | omitted broken CI/PyPI badges until F/P land    |
| CEREMONIES.md (doc-only carve-out) | doc-only fast-path | applied | dropped file-inventory/verdict-rationale subsections |

## Resource consumption

| Phase     | Tokens (approx) | Wall time |
| --------- | --------------- | --------- |
| Mandate   | ~4k             | 3 min     |
| Execution | ~14k            | 15 min    |
| Closure   | ~4k             | 4 min     |
| **Total** | **~22k**        | **~22 min** |

| Counter                | Value |
| ---------------------- | ----- |
| Pre-commit hook fails  | 0     |
| Subagent invocations   | 0     |
| `/clear` events        | 0     |
| Memory rotation events | 0     |
| LOC changed            | README rewrite (~95 → ~110 lines) |
| Files changed          | 2     |
