# 0040 — Firmware: VS Code clang-format on save

- GH issue: #40
- Branch: impl/0040-vscode-format
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task (editor config).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

VS Code must format C++ (`.cpp`/`.h`/`.ino`) exactly like `make format` — zero diff — on save.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`server-esp32s3-rtft/.vscode/settings.json`: associate `*.ino` → `cpp`; point `C_Cpp.clang_format_path` at the same `/usr/bin/clang-format` the Makefile uses; `C_Cpp.clang_format_style: file` (the project `.clang-format`); `editor.formatOnSave` for `[cpp]`.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- **Zero diff by construction**: same binary (`/usr/bin/clang-format` 18.1.3 — the one `make format` resolves to) + same style file (`.clang-format`, `style: file`). #38 already proved the sources are clean under that pair, so on-save formatting reproduces it exactly.
- `*.ino` formatted because it is associated as `cpp` (the C/C++ extension's formatter then applies).
- Not runnable headless (needs the VS Code C/C++ extension); correctness rests on the identical binary+style.

### 3.2 Verdict

Accept.

## Governance trace

| Source                  | Clause          | Action  | Note                                          |
| ----------------------- | --------------- | ------- | --------------------------------------------- |
| CLAUDE.md (consistency) | one source of truth | applied | editor + Makefile share clang-format binary + style |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~5k             | ~6 min    |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 2 (.vscode/settings.json, devlog) |
