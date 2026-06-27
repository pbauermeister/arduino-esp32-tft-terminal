# 0019 — Test strategy (design)

- GH issue: #19
- Branch: impl/0019-test-strategy
- Opened: 2026-06-27

Design task. Deliverable is this devlog (the strategy); no tests implemented here — that is task E. Scope from `TODO.md` item D.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: user

Design a minimal, proportionate automated-test strategy for the Python client.
Hard constraint: everything ultimately talks to a hardware board over USB. The brief (from the assessment) is **one seam, don't over-mock** — fake only the serial boundary, run everything above it as real code.

### Acceptance criteria

1. A named single fake at the serial boundary, justified against the real `Channel` interface.
2. Tiered tests, each with a clear what/how and concrete targets from the real code.
3. Test layout + pytest wiring + Makefile `test` target defined.
4. Explicit scope, deferrals, and open decisions for the user.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: user

This is the design. On approval, task E implements Tier 1 + Tier 2 (and wires the Makefile/CI); Tier 3 is a manual checklist.

## 3. Design

- Author: agent
- Model: Claude Opus 4.8
- Review: user

### 3.1 Principle — one seam

`lib/channel.py::Channel` is the **only** I/O boundary: a 7-method synchronous serial port (`open`, `close`, `clear`, `set_callback`, `write`, `read`, `flush_in`, plus the `self.ser` attribute). Everything above it — `Command`, `Gfx`, `Board`, `App`, the apps — is pure Python orchestration.

So the single fake is **`FakeChannel`**, a drop-in for `Channel`:

- `write(s)` records the command and prepares the board's answer.
- `read()` returns that answer.
- Response policy: `width`/`height` → fixed board size (the real **240×135**); `getTextBounds …` → deterministic metrics (char-count × fixed glyph size); `readButtons` → a **scripted** sequence (drives app termination, see 3.3); every other (draw) command → `OK`.

The protocol is synchronous request→response, so a 1-write→1-response model covers it; the blocking-vs-fire-and-forget and auto-read-button nuances are an E implementation detail, not a design risk.

Faking this one class exercises the entire client stack (command formatting, gfx string generation, board configuration, app frame logic) with no hardware.

### 3.2 Tier 1 — pure-logic units (no seam)

Direct unit tests on pure computation. Highest ROI, no board, no fake.

- **Geometry / physics**: `cube.rotate_point` / `adjust_point`; `starfield.Star.compute`; `tunnel.compute`; `collisions.Particle.advance` + `Simulation.change_velocities` / `handle_wall_collisions` (numpy); `app.__init__.Bouncer.advance` / `bump`; `ColorComponent.advance`.
- **Timing**: `app.__init__.TimeEscaper.check` (inject a clock, or assert the boundary).
- **Helpers**: `camel_to_snake` / `camel_to_kebab` / `camel_to_title`.
- **CLI/config**: `lib/args.py` `get_config_args_specs`, `get_args` (arg parsing, config merge, `--only` choices, `--version`).
- **Monitor parsers** (pure once fed captured text): mpstat-JSON parsing in `monitor_cpus` / `monitor_graph`; `free` / `netstat` regex parsing. Fixtures = captured sample output (no live system).

RNG-touching units (`Bouncer.bump`, `ColorComponent.advance`, `Particle`) are tested with a seeded RNG.

### 3.3 Tier 2 — command-stream snapshot (golden) via `FakeChannel`

The dfd non-regression idea, retargeted from DOT output to the **USB command stream**.

Mechanism:

1. Build `Board(FakeChannel())`; seed `random` and `numpy.random`.
2. Instantiate one app; drive it so `readButtons` returns `NONE` for **N** frames, then a button → the app's `_run()` loop exits deterministically after exactly N frames. (No real board latency, so `TimeEscaper` never fires first.)
3. `FakeChannel` has recorded every written command → that's the **command stream**.
4. Snapshot it to a golden file; the test diffs new output against the golden. A `make` target regenerates goldens after a reviewed visual/behavioural change (dfd's `nr-regenerate` pattern).

In scope (deterministic): **`cube`, `fill`, `tunnel`** (no RNG); **`starfield`, `quix`, `collisions*`** (seeded RNG).

Out of scope for this tier: **monitor apps** — their command stream depends on live CPU/mem/net/date, so snapshots aren't stable. Their _logic_ is covered by the Tier-1 parser tests instead.

This catches rendering-logic regressions (a maths bug in the cube projection, a changed draw order) with zero hardware.

### 3.4 Tier 3 — manual hardware smoke (not automated, not CI)

A short documented checklist run against a real board before a release, e.g.:

- `arduino-esp32-tft-terminal --only cube` (and a couple of others) renders and responds to buttons;
- `--demo` cycles; Ctrl-C exits cleanly (guards #3).

Recorded in the devlog / a README section; bit-rot accepted.

### 3.5 Layout & wiring

```
client-py/
  tests/
    conftest.py            # FakeChannel, board fixture, seeded-RNG fixture
    unit/                  # Tier 1
    snapshot/
      __init__.py          # Tier 2 harness (run N frames, capture stream)
      golden/<app>.txt     # golden command streams
```

- `pyproject.toml`: `[tool.pytest.ini_options]` (`testpaths`, `pythonpath = ["src"]`). `pytest` already in `[project.optional-dependencies].dev`.
- `Makefile`: replace the placeholder `test` target with `uv run pytest tests`; add `snapshot-regenerate` (writes goldens). `check` and `publish-quality` already call `test`.

### 3.6 Scope / deferrals

- No coverage-percentage gate initially (YAGNI; revisit if it adds signal).
- Monitor command-stream snapshots deferred (subprocess mocking is disproportionate now).
- Hardware tier stays manual.

### 3.7 Open decisions (for review)

1. **Snapshot form** — full command stream (readable diffs, small for N frames) vs. a digest/hash (tiny, opaque). _Recommend full stream._
2. **Frames per snapshot N** — _recommend ~8._
3. **Fake board size** — match the real **240×135** vs a round number. _Recommend 240×135._
4. **E's first apps** — all deterministic apps at once, or start with `cube` + `fill` + `tunnel` + `starfield` then expand. _Recommend the 4-app subset first._
5. **Monitor parser fixtures** — OK to capture sample `mpstat -o JSON` / `free` / `netstat` output as committed fixtures?

## Governance trace

| Source                      | Clause                       | Action  | Note                                                  |
| --------------------------- | ---------------------------- | ------- | ----------------------------------------------------- |
| CLAUDE.md (Task nature)     | exploratory vs execution     | applied | flagged design task; deliverable is the strategy      |
| CLAUDE.md (Proportionality) | proportionality              | applied | one seam; monitor snapshots + coverage gate deferred  |
| CLAUDE.md (Preferences)     | research established methods | applied | reuse dfd non-regression pattern (golden files)       |
| CLAUDE.md (Framing)         | desired-outcome framing      | applied | "exercise the stack via one seam", not per-part mocks |

## Resource consumption

| Phase  | Tokens (approx)       | Wall time |
| ------ | --------------------- | --------- |
| Design | ~45k (incl. subagent) | ~30 min   |

| Counter              | Value           |
| -------------------- | --------------- |
| Subagent invocations | 1               |
| Files changed        | 1 (this devlog) |
