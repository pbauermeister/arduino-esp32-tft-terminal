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
- **D · Test strategy** — design devlog; pivoted on review from app snapshots to the protocol/button contract — #20.
- **E · Tests** — host unit tests: protocol formatting/parsing, button decoding, pure-logic units (24 tests) — #22/#23.
- **Self-test** — interactive on-board acceptance suite (`make test-board`): boot (logo + NeoPixel), primitive gallery, buttons/reset, unattended command-conformance + soak — #27.
- **Firmware host-test study** — researched; interactive self-test adopted, FW host-tests + shadow-canvas parked; pixel readback confirmed unavailable — #25.
- **F · CI** — GitHub Actions running `make check` (ruff + pytest) on Python 3.11–3.13 — #29.
- **I · De-duplicate physics** — _no-op:_ already factored. `collisions.py` holds the shared `Particle`/`Simulation`/`CollisionsElastic` base; `collisions2/3/4` are thin subclasses overriding params/methods. No duplication to extract.

## TODO Items

1. **Firmware Makefile targets** — committed `.clang-format` + `arduino-cli`
   build/upload targets for `server-esp32s3-rtft/`. _In PR #33 (require
   bootstraps `arduino-cli`; `firmware-upload` hardware-tested)._

2. **Firmware version command** — add a board command (`version`) returning the
   firmware version. Maintain the version in a firmware `CHANGES.md` (same
   `## Version X.Y.Z:` format as `client-py/`), injected into the build
   (`CHANGES.md` → generated header) so the running firmware reports it.
   Optionally surface it via the client.

3. **Retire VS Code build docs** — remove `server-esp32s3-rtft/README-VSCODE.md`
   and its references; the Arduino VS Code plugin is unmaintained. From now on
   the build/flash is shell + Makefile + `arduino-cli`, entirely and only
   (`make require` / `firmware-build` / `firmware-upload`). Repoint the server
   and top-level READMEs.

4. **Top-level signpost Makefile** — a repo-root `Makefile` that builds nothing;
   its default/help target points to the sub-makefiles: `client-py/` (client +
   the test suites — tests live there because a running app drives the board)
   and `server-esp32s3-rtft/` (firmware build/flash).

5. **Firmware clang-format backlog** — run `make format` over the firmware
   (`*.ino` / `*.cpp` / `*.h`); ~2730-line pure-formatting diff. Apply as a
   single reviewed commit, then re-verify on the board (`make firmware-build`
   + a hardware smoke). Deferred from #33 — no automated behaviour check for
   firmware, so the reformat is isolated from logic changes.

6. **Protocol single-source** (J) — deferred. Codegen a command spec
   into both `client-py` (gfx strings) and firmware (`command.cpp`
   hash-switch). Parked until the duplication actually bites.
