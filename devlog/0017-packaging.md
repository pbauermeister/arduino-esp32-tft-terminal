# 0017 — Package client-py (src-layout, console script, version from CHANGES.md)

- GH issue: #17
- Branch: impl/0017-packaging
- Opened: 2026-06-27
- Closed: 2026-06-27

Standard-flow task (structural; touches protected `CLAUDE.md`). Scope from `TODO.md` item 6 (Task P). Reordered ahead of G (Makefile) per dependency — the uv Makefile needs the package to exist.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Make `client-py` an installable, PyPI-publishable package.

### Acceptance criteria

1. src-layout `client-py/src/arduino_esp32_tft_terminal/`; flat `config`/`app`/`lib` imports rewritten to the package namespace.
2. `pyproject.toml [project]` with console script `arduino-esp32-tft-terminal`, deps (`numpy`, `pyserial`, `claude-busy-monitor`), dynamic version from `CHANGES.md`.
3. `uv build` succeeds; `uv tool install .` + `arduino-esp32-tft-terminal --help` work without a board.
4. ruff stays green; docs updated for the new invocation.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. `git mv` `config.py`, `app/`, `lib/` under `src/arduino_esp32_tft_terminal/`; `run.py` → `cli.py`; add `__init__.py`, `__main__.py`.
2. Rewrite imports (`import config` → `from arduino_esp32_tft_terminal import config`; `app`/`lib` likewise) via scripted sed across the package.
3. Wrap `cli.py`'s module-level code into `main()` (pass `board` explicitly); add `__main__` guard.
4. `pyproject.toml`: hatchling backend, `[project]`, `[tool.hatch.version]` regex on `CHANGES.md`, console script.
5. Move `CHANGES.md` next to `pyproject.toml` (hatchling version source must be inside the project dir).
6. Update READMEs + `CLAUDE.md` for the new invocation and layout.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Deviations / decisions

- **CHANGES.md moved root → `client-py/`**: hatchling's regex version source `path` is resolved inside the project (pyproject) dir and must be in the sdist; `../CHANGES.md` would break the sdist. This makes it the client's release changelog (the client is the only versioned/published artefact). No markdown links pointed at the old location.
- **`config.py` runtime-patched global kept** (not refactored): it works correctly as a packaged module singleton (`config.WIDTH = …` mutates the shared module). Refactor was YAGNI.
- **License as classifier, not bundled file**: `LICENSE` lives at the repo root (covers firmware/case too), outside the `client-py/` project dir — bundling it would hit the same sdist-boundary issue. The GPLv3 classifier carries the metadata; bundling the file is a minor follow-up.
- **`run.py` → `cli.py`** broke the documented `./run.py` commands; READMEs/CLAUDE.md updated to `uv tool install .` + the `arduino-esp32-tft-terminal` console command.
- **`requirements.txt` retained** (added `claude-busy-monitor`) for the editable-dev path; `pyproject` deps are canonical.
- **Task G (Makefile) folded in** (user request — to test the package via `make`): added `client-py/Makefile` (cbm-based, two-level targets, `Build and install::` + `Publish to PyPI::` groups in call order); removed the superseded interim root `Makefile`; added a `--version` flag to the CLI so `make verify-installed` can match `CHANGES.md`. Firmware `arduino-cli` targets + `.clang-format` deferred (separate follow-up).
- **`requires-python` corrected `>=3.10` → `>=3.11`**: `claude-busy-monitor` only supports `>=3.11`, so `uv sync` (via `make lint`) could not resolve at the 3.10 floor. Classifiers, ruff `target-version`, and the "Python 3.10+" doc/badge mentions updated to 3.11.

### 3.2 Verification

- `uv build` → wheel + sdist, version `0.1.0` (from `CHANGES.md`).
- Makefile cycle: `make help` / `lint` / `build` / `install` / `verify-installed` (version matches `CHANGES.md`) / `uninstall` / `verify-uninstalled` / `clean` all succeed; `arduino-esp32-tft-terminal --version` → `0.1.0`. System left clean.
- `uv pip install <wheel>` into a throwaway venv pulled `claude-busy-monitor==1.0.5`, `numpy`, `pyserial` from PyPI.
- `arduino-esp32-tft-terminal --help` → exit 0 (exercises every import + the app registry + config reflection; board-free).
- `python -m arduino_esp32_tft_terminal --help` → exit 0.
- `importlib.metadata.version('arduino-esp32-tft-terminal')` → `0.1.0`.
- `--only nope` → argparse rejects with the full app-choice list.
- `ruff check src` → All checks passed.

No hardware path exercised (no board; that needs the manual smoke tier from task D/E).

### 3.3 Retrospective

| #   | Point                                                                 | Agent | User |
| --- | --------------------------------------------------------------------- | ----- | ---- |
| 1   | `--help` smoke is a strong board-free import-integrity test           | well  |      |
| 2   | sed import rewrite + ruff isort kept the 26-file move mechanical      | well  |      |
| 3   | CHANGES.md/LICENSE sdist-boundary forced structural calls mid-task    | surprise |   |
| 4   | Reordering P ahead of G (dependency) was the right call               | well  |      |

### 3.4 Verdict

Accept with review: structural change, no hardware test, and it edits the protected `CLAUDE.md` and the user-reviewed READMEs — warrants a human eye before merge.

## Governance trace

| Source                          | Clause                  | Action  | Note                                              |
| ------------------------------- | ----------------------- | ------- | ------------------------------------------------- |
| CLAUDE.md (Permissions)         | protected-file review   | applied | P edits CLAUDE.md → pushed for review, not auto-merged |
| CLAUDE.md (Code reuse)          | frameworks/libraries    | applied | hatchling + cbm packaging pattern reused          |
| CLAUDE.md (YAGNI)               | YAGNI                   | applied | config.py global kept; license-file bundling deferred |
| CEREMONIES.md (task order)      | reorder for dependency  | applied | P before G (user-authorised)                      |

## Resource consumption

| Phase     | Tokens (approx) | Wall time |
| --------- | --------------- | --------- |
| Mandate   | ~6k             | 5 min     |
| Execution | ~70k            | 50 min    |
| Closure   | ~10k            | 8 min     |
| **Total** | **~86k**        | **~1 h**  |

| Counter                | Value |
| ---------------------- | ----- |
| Pre-commit hook fails  | 0     |
| Subagent invocations   | 0     |
| `/clear` events        | 0     |
| Memory rotation events | 0     |
| Files changed          | ~34 (mostly renames) |
