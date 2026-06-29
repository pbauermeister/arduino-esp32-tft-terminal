# 0054 — Protocol single-source: codegen client + firmware + docs from one spec

- GH issue: #54
- Branch: impl/0054-protocol-single-source
- Opened: 2026-06-29
- Closed: —

### Context

- Predecessor #52/#53 made the `PRINT_LENGTH` agreement **runtime-negotiated** (`getPrintMaxLength`) — one duplicated constant removed, explicitly flagged there as a step toward this task (J).
- This task removes the structural duplication itself: the command vocabulary, today hand-maintained across three code sites plus the protocol doc.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Make the command vocabulary **single-sourced**: define each command once, generate every mechanical surface, so adding or changing a command is one spec edit — no silent drift.

- **Task nature:** execution.
- **Criticality:** mixed.
  - Generator + client raw layer + docs — low-risk, reversible, host-tested → aggressive automation.
  - Firmware — flash + hardware retest, must stay byte-comparable → strict human oversight.

### 1.1 The duplication (what single-sourcing must cover)

Four surfaces encode the same per-command facts (name, arg order, arg types, return shape):

1. Client formatter — `gfx.py` (`f'drawRect {x} {y} {w} {h} {fg}'`).
2. Server parse/validate/enqueue — `command.cpp` `interpret()` `hash()` switch.
3. Server replay/execute — `transaction.cpp` `do_action()` second `hash()` switch.
4. `README-protocol.md` table (hand-maintained).

The two server switches are separate by design (flicker-avoidance: parse now, execute at `commit()`); both are derivable from one arg-typed spec.

### 1.2 Command kinds (the spec must model shape, not just arg lists)

| Kind     | ~N | Examples                         | Server flow                  | Returns        |
| -------- | -- | -------------------------------- | ---------------------------- | -------------- |
| buffered | 25 | `drawRect`, `print`, `setCursor` | enqueue `Action`, defer      | `ok`           |
| query    | 7  | `getTextBounds`, `width`         | `commit()` then read state   | int / int-tuple |
| control  | 6  | `reboot`, `display`, `reset`     | immediate side-effect        | `ok` / empty   |
| button   | 4  | `readButtons`, `waitButton`      | immediate, **may block**     | string         |
| misc     | 2  | `test`, `hardcopy`               | special                      | string         |

Arg type vocabulary (already enumerated by the firmware readers): `int16` · `int` · `uchar` · `bool` · `last-string` · `raw-rest`, each optionally with a default (incl. cross-arg defaults, e.g. `setTextSize sy=sx`).

### 1.3 Acceptance criteria

1. One `protocol.yaml` is the sole source; all four surfaces (§ 1.1) are generated from it.
2. Generated stubs are formatted by the existing per-subproject tools and **committed**; `make protocol-gen && git diff --exit-code` is clean (CI drift gate).
3. Server completeness is **linker-enforced**: a missing hardware handler fails the build (no vtable, handlers remain inlinable).
4. Firmware stays functionally equivalent and size-comparable to the hand-written build (DRAM ≈ current; hardware self-test passes).
5. Apps are unchanged — they keep calling the hand-written `Gfx` facade.
6. Generator regression is covered by goldens (§ 2.6); client host tests still pass; firmware CI still compiles.

### 1.4 Input documents

- `README-protocol.md` (the contract being single-sourced).
- `server-esp32s3-rtft/command.cpp`, `transaction.cpp`, `transaction.h`, `config.h`.
- `client-py/src/arduino_esp32_tft_terminal/lib/{gfx.py,command.py}`.
- Devlog `0052` (§ 2.5 names J as the target); `TODO.md` item 1.

### 1.5 Out of scope

- The text wire protocol stays human-readable (serial-console debuggability) — **no** binary IDL (protobuf/Cap'n Proto) that would replace it.
- App-level conveniences (`set_text_size` scaling, `print` slicing, `hsv_to_rgb`, `R`-on-recovery) stay **hand-written** in `Gfx` — they are not protocol.
- `Action.args[8]` stays an `intptr_t` array (no typed-struct redesign) — keeps the firmware diff byte-comparable.

## 2. Execution plan (design)

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 2.1 New subproject `protocol/`

- `protocol.yaml` — the spec (also human-readable reference).
- generator (Python): Pydantic models validate the spec; Jinja2 templates emit each output.
- deps (dev-only, this subproject): **Pydantic** (spec validation) + **Jinja2** (templating) — battle-tested, replacing hand-rolled parsing/concatenation.
- generator asserts **`hash()` uniqueness** at gen-time (the runtime switch silently assumes no collisions).

### 2.2 Spec schema

Per command: `name`, `kind`, `args` (each `{n, t, optional?, default?}`), `returns`, `doc`. Sketch (the four hard cases that prove expressiveness):

```yaml
- name: drawRect
  kind: buffered
  args: [{n: x, t: int16}, {n: y, t: int16}, {n: w, t: int16},
         {n: h, t: int16}, {n: color, t: int}]
  doc: Outline rectangle at (x,y), size w×h, palette color.

- name: setTextSize          # optional trailing arg, cross-arg default
  kind: buffered
  args: [{n: sx, t: int}, {n: sy, t: int, optional: true, default: sx}]

- name: getTextBounds        # query: trailing raw string + multi-int return
  kind: query
  args: [{n: x, t: int16}, {n: y, t: int16}, {n: text, t: last-string}]
  returns: [x1, y1, w, h]

- name: waitButton           # blocking, string return
  kind: button
  args: [{n: during, t: int}, {n: up, t: int}]
  returns: string
```

### 2.3 Generated outputs — the symmetric split

Generate the **raw protocol surface** on both ends; keep **semantics** hand-written on both ends.

- **Client** (`protocol/` → `client-py`):
  - generated: one typed raw method per command (formats wire string, parses typed response).
  - hand-written: `Gfx` facade over the raw layer (conveniences in § 1.5). Apps call `Gfx`, unchanged.
- **Server** (`protocol/` → `server-esp32s3-rtft`):
  - generated: arg-read + validate + dispatch switch (site 2); the **uniform enqueue handler** for buffered cmds (`action()->set(hh, …); add(); return ok();`); the replay dispatch skeleton (site 3).
  - hand-written "arsenal": the irreducible hardware bodies — `do_action`'s actual `tft.*()` calls, and the query / button / control handlers.
- **Docs:** `README-protocol.md` command table.

Net: buffered commands become **fully generated** on the server bar the one `tft.*()` line; hand-written shrinks to ~15 small bodies.

### 2.4 Server completeness — linker-enforced

- generated header declares hardware-handler prototypes (free functions, e.g. `handle_getTextBounds(...)`).
- generated dispatch calls them; a missing handler → **undefined reference at link** (build fails).
- no virtual dispatch → no vtable cost, handlers stay inlinable under LTO (meets criterion § 1.3.4).

### 2.5 Formatting · commit · drift gate

- generator writes into the target dirs; the make target runs the **projects' own** formatters over the output — no formatting logic in the generator:
  - Python → `ruff format` + `ruff check --fix` (client `pyproject.toml`).
  - C++ → `clang-format -style=file` (`server-esp32s3-rtft/.clang-format`, same as `make format`).
  - Markdown → Prettier (`implementation/.prettierrc`).
- generated files carry a heading comment: "auto-generated, do not edit; regenerate via `make protocol-gen`".
- **committed**; CI gate: `make protocol-gen && git diff --exit-code`.

### 2.6 Test strategy / goldens

Two complementary layers (avoid a params × returns cross-product — feature axes, not real-command combinatorics):

1. **Real-spec drift gate** — regenerate from `protocol.yaml`, `git diff --exit-code`. Covers every real command; proves spec→output reproducible & committed.
2. **Feature-fixture goldens** (pytest, in `protocol/`) — one small synthetic spec exercising each schema feature once (every arg type, optional + cross-arg default, each kind, each return shape); committed expected outputs (**post-format**) per emitted file. Tests generator logic decoupled from the live protocol — so generator refactors show exactly what changed in emission.

Plus, unchanged: client host tests (`Gfx` behaviour), firmware compile + DRAM check, hardware self-test (`make test-board`).

### 2.7 Phased delivery (client-first)

Lowest-risk half first; firmware (flash + retest) second.

1. **Spec + generator + client raw layer.** `Gfx` re-expressed over the raw layer, app-facing behaviour identical. Host-tested. Early proof the spec is expressive before betting firmware on it.
2. **Docs generation.** `README-protocol.md` table from the spec; diff vs current to confirm parity.
3. **Server codegen.** Parser + enqueue + replay skeletons + handler header; hand-written arsenal concretises it. Compile + DRAM check; **hardware self-test re-run** (ROM-download-mode flash).
4. **CI wiring.** Drift gate + fixture goldens in CI.

Each phase is independently verifiable; phases 1–2 can land before 3–4 if scope warrants splitting the PR.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

_(pending implementation)_

## Governance trace

| Source                          | Clause             | Action  | Note                                                              |
| ------------------------------- | ------------------ | ------- | ---------------------------------------------------------------- |
| CLAUDE.md (Code-reuse)          | frameworks/libs    | applied | Pydantic + Jinja2 surfaced and confirmed before plan finalised   |
| CLAUDE.md (Research methods)    | established methods | applied | IDL/stub-gen is the standard cross-language single-source pattern |
| CLAUDE.md (YAGNI)               | drop unneeded      | applied | goldens scoped to feature axes, not params×returns cross-product |
| CLAUDE.md (Proportionality)     | cost vs problem    | applied | "now is the time" — user confirmed after triple-site cost shown  |
| CLAUDE.md (Multiple interp)     | rank options       | applied | free-fns vs pure-virtual ranked → linker enforcement chosen      |
| CEREMONIES.md:13                | mandate gate       | applied | §1 + §2 to be user-attested before implementation                |

## Resource consumption

| Phase  | Tokens (approx) | Wall time |
| ------ | --------------- | --------- |
| Design | ~30k            | ~50 min   |

| Counter       | Value                    |
| ------------- | ------------------------ |
| Files changed | 1 (devlog — design only) |
