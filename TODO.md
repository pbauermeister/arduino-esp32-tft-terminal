# TODO

Recognized tasks are recorded as GitHub issues and managed in detail
in corresponding `devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is
forgotten without diverting the current discussion or reasoning. Items
collected here can later be specified as tasks, grouped together, or
discarded. If a TODO item becomes significant effort, it must be
turned into a standard task (GH ticket, PR, devlog).

Cleanup/refactoring slate (no new features). Reference templates:
`cbm` = ~/dev-pb/claude-busy-monitor (uv + ruff tooling, Makefile,
packaging, install/publish); `dfd` = ~/dev-pb/dfd (README polish,
CHANGES.md, doc layer, test tiers).

## Won't do

1. mypy / static type checking — dropped; ruff covers format + lint.
   Existing type hints stay as documentation, unenforced.
2. tox multi-version matrix — CI matrix is enough at this scale.
3. README auto-generation (`<!-- AUTO: -->` + tooling) — no CLI help
   worth embedding; write the README static.
4. pre-commit hooks — disproportionate here (cbm and dfd both skip).
5. Rename `Asteriods` → `Asteroids` — the spelling is intentional.
6. Single-source protocol (codegen for client + firmware) — real fix
   for the double-definition, but needs codegen on both sides;
   parked (see the **Protocol single-source** TODO item below).

## Done

- **A · Hygiene** — #8.
- **Q · Quality tooling** (ruff format + lint, mypy dropped) — #10.
- **H1 · Top-level README** (dfd finish) — #12.
- **H2 · Doc layer** — `CHANGES.md` (#14), per-subproject READMEs + index (#16), install-methods refresh (#18). The `README-STATE-DETECTION` family member moved upstream to `claude-busy-monitor`.
- **G · Makefile** (uv + ruff, two-level; build/install/publish groups) — #18 (folded with P). _Firmware targets split out — see below._
- **P · Packaging** — src-layout, console script, version from `CHANGES.md`, deps incl. `claude-busy-monitor` — #18. **Published 0.1.0 to PyPI.**

## TODO Items

1. **Test strategy** (D) — design devlog: one `RecordingChannel` seam
   (the only fake) + three tiers — pure-logic units, command-stream
   snapshot (golden) tests, manual hardware smoke. [dfd]

2. **Tests** (E) — implement the unit + snapshot tiers per the
   strategy. [dfd]

3. **CI** (F) — GitHub Actions: install uv, `make check` (lint +
   tests); light Python matrix. [cbm]

4. **De-duplicate physics** (I) — extract a shared
   `Particle`/`Simulation` base from
   `collisions{,2,3,4}.py` (rule-of-three met). No behaviour change.

5. **Firmware Makefile targets** — split out of G: a committed
   `.clang-format` for `server-esp32s3-rtft/`, plus `arduino-cli`
   firmware-build / firmware-upload targets.

6. **Protocol single-source** (J) — deferred. Codegen a command spec
   into both `client-py` (gfx strings) and firmware (`command.cpp`
   hash-switch). Parked until the duplication actually bites.
