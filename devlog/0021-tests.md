# 0021 — Implement tests (protocol/button contract + pure-logic units)

- GH issue: #21
- Branch: impl/0021-tests
- Opened: 2026-06-27
- Closed: 2026-06-27

Implements the testing strategy (devlog 0019, task D), **revised mid-task by user review**: the app command-stream snapshots were dropped as low-value; the focus moved to the protocol/button contract.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Test the client where the bug surface is — the USB **protocol contract** (command formatting, response parsing, button decoding) — plus the genuinely pure logic. Fake only the serial boundary.

### Review pivot (supersedes part of 0019)

User review of the first cut: app command-stream **golden snapshots are superfluous** — the apps are straightforward and/or RNG-driven, so a pinned stream is change-detection, not testing. Dropped. The real value is the gadget + USB comms; the visual cumulative effect isn't automatable (no framebuffer readback), but the protocol and button layers are. Firmware-side host tests are split into a separate study (task: firmware host tests).

### Acceptance criteria

1. `FakeChannel` single seam (records writes, scripts answers) + fixtures.
2. Protocol tests: command formatting, query/response parsing, error rejection.
3. Button tests: state decoding (`readButtons`), event accumulation (auto-read `OK <codes>`).
4. Pure-logic unit tests (helpers, colour, physics, args/config, mpstat parser).
5. `pyproject` pytest config + Makefile `test` wiring; `make check` green.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

`FakeChannel` with a `responses` override (to script button reads / errors) + `fake_board` / `make_board` fixtures; protocol + button + unit tests; Makefile/pyproject wiring.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 What was built

- `tests/conftest.py` — `FakeChannel` (records writes; `responses` override) + `fake_board` / `make_board` fixtures.
- `tests/unit/test_protocol.py` — draw-command formatting, `width`/`height`/`getTextBounds` parsing, `ERROR` rejection.
- `tests/unit/test_buttons.py` — `readButtons` state decoding (none / multiple / invalid-ignored), auto-read event accumulation.
- `tests/unit/test_{helpers,gfx_color,physics,args,monitor_parse}.py` — pure logic.
- `pyproject.toml` `[tool.pytest.ini_options]`; Makefile `test`; `lint`/`format` over `src tests`.

### 3.2 Deviations / notes

- **App golden snapshots removed** (the harness + `golden/*.txt`) per review. The `FakeChannel` seam is kept, repurposed to script protocol/button answers rather than capture rendering streams.
- **`config` is process-global**: fixtures reset it per test; per-frame sleep set to 0.

### 3.3 Verification

- `make check` → ruff clean (src + tests) + **24 passed** in ~0.3 s (no app loops; pure protocol/logic).

### 3.4 Test coverage review (per CEREMONIES § 3.5)

- Q's `except:`→`except Exception:` (Ctrl-C) behaviour: needs the board/Ctrl-C path → Tier 3 manual smoke (unchanged).
- `--version` (#18): covered (`test_args`).
- Protocol/button decoding: now directly covered (`test_protocol`, `test_buttons`).
- Firmware command interpretation (the gadget's real logic): not covered here → the firmware host-test study.

### 3.5 Retrospective

| #   | Point                                                            | Agent | User     |
| --- | ---------------------------------------------------------------- | ----- | -------- |
| 1   | First cut over-indexed on app snapshots; review corrected course | not well | surprise |
| 2   | `FakeChannel` seam still right — repurposed to protocol/buttons  | well  |          |
| 3   | Suite now fast + meaningful (protocol contract, not pinned bytes)| well  |          |

### 3.6 Verdict

Accept: green, fast, targets the real bug surface. The deeper gadget verification moves to the firmware host-test study.

## Governance trace

| Source                       | Clause                   | Action  | Note                                        |
| ---------------------------- | ------------------------ | ------- | ------------------------------------------- |
| devlog 0019                  | approved strategy        | tension | Tier 2 (app snapshots) dropped on review    |
| CLAUDE.md (Proportionality)  | proportionality          | applied | dropped low-value goldens; protocol focus   |
| CLAUDE.md (Iterative review) | human review corrects    | applied | review pivot mid-task                       |

## Resource consumption

| Phase     | Tokens (approx) | Wall time |
| --------- | --------------- | --------- |
| Execution | ~95k (incl. subagent + revision) | ~1.5 h |

| Counter              | Value |
| -------------------- | ----- |
| Subagent invocations | 1 (in D) |
| Files changed        | ~10 (tests, pyproject, Makefile) |
