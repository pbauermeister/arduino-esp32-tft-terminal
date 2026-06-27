# 0044 — Retire VS Code build docs

- GH issue: #44
- Branch: impl/0044-retire-vscode-docs
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (docs).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

The Arduino VS Code plugin is unmaintained; the build/flash is now shell + Makefile + `arduino-cli`, entirely and only. Remove `README-VSCODE.md` and repoint its references.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. Delete `server-esp32s3-rtft/README-VSCODE.md` (its content — clang-format setup, plugin install, board URLs — is superseded by `make require` + `.clang-format` + `.vscode/settings.json`).
2. Repoint the server README and top README to the `make` build (`require` / `firmware-upload`).
3. Update CLAUDE.md's two references — **held for user review** (protected file).
4. Historical devlog mentions left as-is (append-only record).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- `grep -rn README-VSCODE` returns only historical devlogs after the change.
- Server + top READMEs now show the `make require` / `make firmware-upload` flow.

### 3.2 Verdict

Accept.

## Governance trace

| Source                 | Clause             | Action  | Note                                      |
| ---------------------- | ------------------ | ------- | ----------------------------------------- |
| CLAUDE.md (Permissions) | CLAUDE.md review   | applied | CLAUDE.md edits held for user attestation |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~6k             | ~8 min    |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 4 (−README-VSCODE, 2 READMEs, devlog) + CLAUDE.md (pending review) |
