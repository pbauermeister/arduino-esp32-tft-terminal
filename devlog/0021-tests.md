# 0021 — Implement tests (Tier 1 units + Tier 2 snapshots)

- GH issue: #21
- Branch: impl/0021-tests
- Opened: 2026-06-27
- Closed: 2026-06-27

Implements the strategy approved in devlog 0019 (task D). Scope from `TODO.md` item E.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Implement Tier 1 (pure-logic units) and Tier 2 (command-stream snapshots) per devlog 0019, with the user-approved decisions: full-stream snapshots, N=8 frames, fake board 240×135, first apps `cube`/`fill`/`tunnel`/`starfield`, committed parser fixtures.

### Acceptance criteria

1. `FakeChannel` single seam + pytest fixtures.
2. Tier 1 unit tests (helpers, colour, physics, args/config, monitor parser).
3. Tier 2 snapshot tests for the 4 apps, golden-file based, deterministic.
4. `pyproject` pytest config + Makefile `test` / `snapshot-regenerate` wiring; `make check` green.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. `FakeChannel` (records writes, answers the synchronous protocol) + `fake_board` / `capture_stream` fixtures in `tests/conftest.py`.
2. Snapshot harness: seed RNG, patch `TimeEscaper.check` to end after N frames, run `app._run()`, capture the command stream.
3. Tier 1 unit tests.
4. Wire `pyproject` (`[tool.pytest.ini_options]`) + Makefile.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 What was built

- `tests/conftest.py` — `FakeChannel` + `fake_board` + `capture_stream`.
- `tests/snapshot/test_apps.py` + `golden/{cube,fill,starfield,tunnel}.txt` — Tier 2.
- `tests/unit/` — `test_helpers`, `test_gfx_color`, `test_physics`, `test_args`, `test_monitor_parse` (Tier 1).
- `pyproject.toml` `[tool.pytest.ini_options]`; Makefile `test` + `snapshot-regenerate`; `lint`/`format` extended to `src tests`.

### 3.2 Deviations / notes

- **Loop exit via `TimeEscaper.check` patch**, not scripted buttons: all 4 apps are `auto_read=True` and share the `auto_read_buttons()` + `escaper.check()` shape, so patching `check` to fire after N frames is uniform and app-agnostic.
- **`cube`'s geometry (`rotate_point`/`adjust_point`) is nested inside `_run()`** — not directly unit-testable. It is exercised by the `cube` snapshot instead. Pure units chosen are the genuinely module/class-level ones.
- **`config` is process-global and runtime-patched**: fixtures reset `WIDTH`/`HEIGHT`/`once`/`APPS_INTERFRAME_DELAY_MS`/`APPS_TITLE_DURATION` per test for isolation; per-frame sleep set to 0.
- **Monitor snapshot deferred** (subprocess/system state); its parser is unit-tested with a fixture + monkeypatched `shell_command` instead.

### 3.3 Verification

- `make check` → ruff clean (src + tests) + **20 passed** (4 snapshot + 16 unit).
- Snapshots are deterministic: regenerate (`SNAPSHOT_UPDATE=1`) then re-run → pass unchanged. Goldens are readable command streams (e.g. `fill` prints the glyph table, `tunnel` draws line pairs).

### 3.4 Test coverage review (§ 3.5 per CEREMONIES)

- Q's `except:`→`except Exception:` behaviour change: not directly asserted (needs the board/Ctrl-C path = Tier 3 manual). Noted as a manual-smoke item.
- The `--version` flag (#18): covered by `test_args::test_version_exits_zero`.
- The import-namespace refactor (#18): implicitly covered — every test imports the package, and the snapshot harness exercises the whole stack.

### 3.5 Retrospective

| #   | Point                                                                | Agent | User |
| --- | -------------------------------------------------------------------- | ----- | ---- |
| 1   | One seam (`FakeChannel`) exercised the whole stack as designed       | well  |      |
| 2   | `TimeEscaper.check` patch gave uniform, app-agnostic N-frame exit    | well  |      |
| 3   | Some advertised pure units were nested (cube) — snapshot covers them | surprise |   |

### 3.6 Verdict

Accept with review: deterministic and green, but the goldens are agent-generated — a glance at one (e.g. `fill.txt`) confirms they're sensible command streams, not noise.

## Governance trace

| Source                       | Clause                | Action  | Note                                            |
| ---------------------------- | --------------------- | ------- | ----------------------------------------------- |
| devlog 0019                  | approved strategy     | applied | one seam + 3 tiers, 5 decisions as approved     |
| CLAUDE.md (Preferences)      | established methods    | applied | golden-file non-regression (dfd pattern)        |
| CLAUDE.md (Proportionality)  | proportionality       | applied | monitor snapshot + broad coverage deferred      |

## Resource consumption

| Phase     | Tokens (approx) | Wall time |
| --------- | --------------- | --------- |
| Execution | ~80k (incl. subagent) | ~1 h |

| Counter              | Value |
| -------------------- | ----- |
| Subagent invocations | 1 (in D)|
| Files changed        | ~12 (tests, goldens, pyproject, Makefile) |
