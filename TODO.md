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
   parked (see item 11 below).

## TODO Items

1. **Hygiene** (A) — `.gitignore` (caches, `dist/`, `.venv/`); remove
   `.mypy_cache/`; relocate `client-py/load.sh` → `scripts/`; add
   `server-featherwing--obsolete/DEPRECATED.md`. Dead apps
   (`bumps.py`, `road.py`) stay inactive/unlinked.

2. **Quality tooling** (Q) — adopt ruff (format + lint), drop mypy,
   reach green. Remove mypy config from the top-level Makefile. [cbm]

3. **Top-level README** (H1) — bring to dfd finish: badges, pitch,
   features, quick-start, per-OS install, links. Static. [dfd]

4. **Doc layer** (H2) — `CHANGES.md` (`## Version X` format, version
   source for packaging); per-subproject READMEs; consolidate the
   `README-protocol/animations/VSCODE/STATE-DETECTION` family under an
   index. [dfd]

5. **Makefile** (G) — uv + ruff, two-level targets (low does one
   thing; high composes, marked by a colon in its `##` doc). Targets:
   help, require (uv), venv-activate, format, lint, test, run, build,
   install, clean, publish. Plus `arduino-cli` firmware-build /
   firmware-upload, and a committed `.clang-format` for the firmware.
   [cbm]

6. **Packaging** (P) — make `client-py` installable and
   PyPI-publishable: src-layout
   `client-py/src/arduino_esp32_tft_terminal/`, `[project]` metadata,
   console script `arduino-esp32-tft-terminal`, `uv tool install` /
   `uv build` / `uv publish`, version extracted from `CHANGES.md`.
   Refactor the `config.py` runtime-patched global. [cbm]

7. **Test strategy** (D) — design devlog: one `RecordingChannel` seam
   (the only fake) + three tiers — pure-logic units, command-stream
   snapshot (golden) tests, manual hardware smoke. [dfd]

8. **Tests** (E) — implement the unit + snapshot tiers per the
   strategy. [dfd]

9. **CI** (F) — GitHub Actions: install uv, `make check` (lint +
   tests); light Python matrix. [cbm]

10. **De-duplicate physics** (I) — extract a shared
    `Particle`/`Simulation` base from
    `collisions{,2,3,4}.py` (rule-of-three met). No behaviour change.

11. **Protocol single-source** (J) — deferred. Codegen a command spec
    into both `client-py` (gfx strings) and firmware (`command.cpp`
    hash-switch). Parked until the duplication actually bites.
