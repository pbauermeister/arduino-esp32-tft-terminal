# 0057 — Protocol CI lint: ruff 0.16 findings, honour uv.lock

- GH issue: #57
- Branch: impl/0057-protocol-ci-lint
- Opened: 2026-10-07
- Closed: 2026-10-07

Fast-path task (brief in chat).

## 1. Mandate

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

Scope source: chat brief, accepted on 2026-10-07 — "Do the fix as a new task, fast path. It will be part of version 0.2.1."

Context: `make publish-quality` for client-py 0.2.1 (commit 7c6dff6) failed at `ci-green`.
The `protocol` CI job failed on `make lint` with three ruff findings; the client-py matrix jobs passed.
Last green CI run was 2026-06-30; ruff 0.16 shipped in between.

Cause: `protocol/Makefile` `require` installs dev deps with `uv pip install -e '.[dev]'`, which ignores `uv.lock` and pulls the newest ruff (0.16.10 in CI, 0.15.20 locked locally).

Acceptance criteria:

1. `make lint` in `protocol/` passes under both ruff 0.15.20 (locked) and 0.16.10 (CI).
2. `make require` installs from `uv.lock`.
3. Drift gate (`make check`) unchanged: no generated stub differs.
4. Noted in `client-py/CHANGES.md` under 0.2.1.

## 2. Execution plan

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

Steps as taken:

1. `src/tft_protocol/load.py:28` — `ValueError` → `TypeError` for the top-level isinstance check (TRY004).
2. `src/tft_protocol/schema.py:115,141` — unquoted the two self-referencing return annotations (UP037); both files already have `from __future__ import annotations`, so this is runtime-safe.
3. `protocol/Makefile` `require` — replaced `uv venv` + `uv pip install -e '.[dev]'` with `uv sync -q --extra dev`, matching the client-py Makefile.
4. Changelog line under 0.2.1.

Not done: bumping the locked ruff to 0.16. The lock stays at 0.15.20; the source fixes make the code clean under both, so a later `uv lock --upgrade` is a no-op for lint.

## 3. Closure

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

### 3.1 Deviations

None.

### 3.2 File inventory

1. `protocol/Makefile` — `require` recipe.
2. `protocol/src/tft_protocol/load.py` — exception type.
3. `protocol/src/tft_protocol/schema.py` — two annotations.
4. `client-py/CHANGES.md` — 0.2.1 entry.
5. `devlog/0057-protocol-ci-lint.md` — this file.

### 3.3 Verification

1. `rm -rf .venv && make require lint test check` in `protocol/` — green, "protocol stubs are up to date".
2. `uv tool run ruff@0.16.10 check .` and `format --check .` — "All checks passed!", 6 files already formatted.
3. CI on the PR branch — see PR.

### 3.4 Retrospective

1. CI drift went unnoticed for three months because nothing was pushed; `ci-green` caught it on the first release attempt, which is what it is for.
2. The two sub-project Makefiles had diverged on how they install dev deps; now aligned on `uv sync`.

### 3.5 Verdict

Accept.

## Governance trace

| Source       | Clause                 | Action  | Note                                        |
| ------------ | ---------------------- | ------- | ------------------------------------------- |
| CEREMONIES   | Fast-path task flow    | applied | brief in chat; single-pass devlog           |
| CLAUDE.md    | Task nature            | applied | execution                                   |
| CLAUDE.md    | Code-reuse             | n/a     | no new code                                 |
| CLAUDE.md    | Devlog + GH issue      | applied | #57                                         |

## Resource consumption

| Phase          | Tokens (approx) | Wall time |
| -------------- | --------------- | --------- |
| Diagnosis      | ~8k             | ~5 min    |
| Fix + verify   | ~6k             | ~5 min    |
| Devlog + PR    | ~4k             | ~3 min    |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 5     |
| Commits       | 1     |
