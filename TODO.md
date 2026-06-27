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
- **Firmware build toolchain** — `server-esp32s3-rtft/` `.clang-format` + Makefile (`require` bootstraps `arduino-cli` + core; `firmware-build`; `firmware-upload` build+flash+verify, **hardware-tested**) — #33. Build fix for esp32 core 3.3.0 (hash narrowing + `hardcopy` stub) — #35.
- **Firmware clang-format backlog applied** — `make format` over all sources; binary-identical (498103 bytes), `format-check` clean — #39.
- **Firmware VS Code format-on-save** — `.vscode/settings.json` clang-formats `.cpp`/`.h`/`.ino` on save with the same binary + `.clang-format` as `make format` (zero diff) — #41.
- **Firmware CI compile gate** — `firmware-build` job (cache + `make require` + `make firmware-build`); `require` installs the libs; core pinned `3.3.0` — #43.
- **Retire VS Code build docs** — removed `README-VSCODE.md`; server/top READMEs + CLAUDE.md repointed to the `make` build — #45.
- **Top-level signpost Makefile** — root `make` points to the sub-makefiles (tests live in client-py) — #47.

## TODO Items

1. **Firmware version command** — add a board command (`version`) returning the
   firmware version. Maintain the version in a firmware `CHANGES.md` (same
   `## Version X.Y.Z:` format as `client-py/`), injected into the build
   (`CHANGES.md` → generated header) so the running firmware reports it.
   Optionally surface it via the client.

2. **Firmware DRAM headroom / lift the core pin** — pinned to
   `esp32:esp32@3.3.0` (`require` + CI cache key) because `3.3.10` overflows
   `dram0_0_seg` by ~4 KB. Lifting the pin needs a (non-trivial) DRAM trim first.

   _Why 3.3.10 overflows but 3.3.0 fits:_ our firmware's DRAM is identical on
   both cores — the esp32 **core's own** static RAM (USB-CDC stack, IDF /
   FreeRTOS / driver buffers) grew ~4 KB between `3.3.0` and `3.3.10`. The
   firmware already sat at 84% (~49 KB free), so the core's growth tipped the
   _combined_ static data over the internal-DRAM region. We didn't grow; the
   floor under us rose.

   _Where our DRAM goes:_ one global dominates — `Transaction transaction`
   (`transaction.h`) = **236 KB = 72% of the 320 KB DRAM**. It is
   `Action actions[1000]` (a draw FIFO); each `Action` ≈ 236 B =
   `hash` (4) + `args[8]` (32) + **`str[BUFFER_LENGTH=200]`**. Most buffered
   actions are draws that never touch `str`, so ~200 KB is unused text buffers.

   _Fix ideas (each non-trivial; pick one, verify on 3.3.10, then lift the pin):_
   1. Shrink the FIFO depth (`actions[1000]` → e.g. 512). One line, frees
      ~115 KB. Risk: an app buffering more draws than the depth between
      `display` calls overflows — pick a depth no app exceeds.
   2. Small `Action.str` + span long prints over multiple `print` calls (the
      client already has `chunkize`; the firmware caps text per action). Cuts
      the per-slot waste without dropping long-text support.
   3. Decouple `str` from `Action` entirely (only `print` actions carry text).
      The principled fix; most invasive.

   _Verify:_ compile against `3.3.10`, confirm it fits, lift the pin in
   `require` + the CI cache key, flash via ROM download mode, runtime-test the
   draw-heavy apps (`monitor-graph`, `asteriods`).

3. **Protocol single-source** (J) — deferred. Codegen a command spec
   into both `client-py` (gfx strings) and firmware (`command.cpp`
   hash-switch). Parked until the duplication actually bites.
