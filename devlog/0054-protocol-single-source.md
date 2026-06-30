# 0054 — Protocol single-source: codegen client + firmware + docs from one spec

- GH issue: #54
- Branch: impl/0054-protocol-single-source
- Opened: 2026-06-29
- Closed: 2026-06-30

### Context

- Predecessor #52/#53 made the `PRINT_LENGTH` agreement **runtime-negotiated** (`getPrintMaxLength`) — one duplicated constant removed, explicitly flagged there as a step toward this task (J).
- This task removes the structural duplication itself: the command vocabulary, today hand-maintained across three code sites plus the protocol doc.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: user

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

| Kind     | ~N  | Examples                         | Server flow                | Returns         |
| -------- | --- | -------------------------------- | -------------------------- | --------------- |
| buffered | 25  | `drawRect`, `print`, `setCursor` | enqueue `Action`, defer    | `ok`            |
| query    | 7   | `getTextBounds`, `width`         | `commit()` then read state | int / int-tuple |
| control  | 6   | `reboot`, `display`, `reset`     | immediate side-effect      | `ok` / empty    |
| button   | 4   | `readButtons`, `waitButton`      | immediate, **may block**   | string          |
| misc     | 2   | `test`, `hardcopy`               | special                    | string          |

Arg type vocabulary (already enumerated by the firmware readers): `int16` · `int` · `int8` · `uchar` · `bool` · `last-string` · `raw-rest`. An arg may carry a literal `default`; its presence makes the arg optional (e.g. `setTextSize` omits `sy`, `monitorButtons` omits `interval`).

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
- Review: user

### 2.1 New subproject `protocol/`

- `protocol.yaml` — the spec (also human-readable reference).
- generator (Python): Pydantic models validate the spec; Jinja2 templates emit each output.
- deps (dev-only, this subproject): **Pydantic** (spec validation) + **Jinja2** (templating) — battle-tested, replacing hand-rolled parsing/concatenation.
- generator asserts **`hash()` uniqueness** at gen-time (the runtime switch silently assumes no collisions).

### 2.2 Spec schema

Per command: `name`, `args`, `returns`, `category`, `doc`. Two fields are **load-bearing for codegen**, `category` is developer-facing (one load-bearing edge), `doc` is mandatory. Enumerated fields are **closed sets** — Pydantic `Enum`s in the generator (authoritative), mirrored in these tables; an out-of-enum value is a load-time error.

| field      | role                                                                 | values                                                               |
| ---------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `name`     | command keyword (wire token, also the `hash()` key)                  | —                                                                    |
| `args`     | load-bearing both ends (parse / format)                              | list of `{name, type, default?}`; a `default` makes the arg optional |
| `returns`  | **load-bearing (client)** — whether/how to read & parse the response | `ok` · `none` · `int` · `[names…]` · `string`                        |
| `category` | developer-facing cluster; sole codegen effect: `buffered` ⇒ enqueue  | `buffered` · `control` · `query` · `button` · `misc`                 |
| `doc`      | **mandatory** human description                                      | free text                                                            |

Why this split (per discussion #54):

- The **client** keys off `returns` alone — read-and-parse (`int`/`ints`/`string`), read-and-discard (`ok`), or don't read (`none`). `category` is invisible to it.
- The **server** keys off `category == buffered`: buffered ⇒ generated enqueue (`action()->set(…); add(); ok()`) + generated replay dispatch calling the hand-written `tft.*()` binding; every other category ⇒ generated parse + call the hand-written handler returning the response. So `control`/`query`/`button`/`misc` are indistinguishable to the generator — they are documentation.
- **Commit-before-read is not in the spec**: `getRotation` commits, `width` does not — but that lives inside the hand-written query handler (hand-written regardless). No `commit` field.
- **Async button reporting is not in the spec**: the OK-suffix and `watchButtons` streaming are the client's low-level channel strategy (`command.py` `auto_btn_handler`), not per-command codegen. `readButtons`/`waitButton` are just `returns: string` to the generator.

**`type`** — arg type (parse + the C++ cast / handler type):

| value         | wire form                                                 | C++ reader      | C++ type        | Python |
| ------------- | --------------------------------------------------------- | --------------- | --------------- | ------ |
| `int16`       | integer                                                   | `read_int`      | `int16_t`       | `int`  |
| `int`         | integer                                                   | `read_int`      | `int`           | `int`  |
| `int8`        | integer                                                   | `read_int`      | `int8_t`        | `int`  |
| `uchar`       | integer                                                   | `read_int`      | `unsigned char` | `int`  |
| `bool`        | `0`/`1`                                                   | `read_bool`     | `bool`          | `bool` |
| `last-string` | trailing text, **required** (errors if absent)            | `read_last_str` | `const char*`   | `str`  |
| `raw-rest`    | line remainder, **verbatim, may be empty** (e.g. `print`) | `rest`          | `const char*`   | `str`  |

(`last-string` vs `raw-rest`: the former missing-arg-checks one trailing string — `getTextBounds`; the latter passes the unparsed remainder straight to `Action.str` and accepts empty — `print`. `int8` is `drawChar.size`; per-arg C++ type also lets `drawPixel.color` be `int16_t` while other `color`s are `int`.)

**`returns`** — response shape (omitted ⇒ `ok`), independent of `category`:

| spec value       | response shape                                      | example                       |
| ---------------- | --------------------------------------------------- | ----------------------------- |
| _omitted_ / `ok` | `OK` sentinel (+ optional auto-button suffix)       | most buffered, `display`      |
| `none`           | no response read                                    | `reboot`, `watchButtons`      |
| `int`            | single integer                                      | `width`, `getRotation`        |
| `[a, b, …]`      | fixed named-integer tuple, space-separated (`ints`) | `getTextBounds` → `x1 y1 w h` |
| `string`         | opaque string                                       | `version`, `readButtons`      |

Sketch (the hard cases that prove expressiveness):

```yaml
- name: drawRect
  category: buffered
  args:
    [
      { name: x, type: int16 },
      { name: y, type: int16 },
      { name: w, type: int16 },
      { name: h, type: int16 },
      { name: color, type: int },
    ]
  doc: Outline rectangle at (x,y), size w×h, in palette colour `color`.
  # returns omitted ⇒ ok

- name: setTextSize # trailing arg with a default ⇒ optional
  category: buffered
  args: [{ name: sx, type: int }, { name: sy, type: int, default: -1 }]
  doc: Set text magnification; omit sy (default -1) for square.

- name: getTextBounds # query: trailing required string + ints tuple
  category: query
  args:
    [
      { name: x, type: int16 },
      { name: y, type: int16 },
      { name: text, type: last-string },
    ]
  returns: [x1, y1, w, h]
  doc: Pixel bounding box of `text` rendered at (x,y).

- name: version # query returning a string; no commit (handler detail)
  category: query
  returns: string
  doc: Firmware version string.

- name: waitButton # button, blocking, string return
  category: button
  args: [{ name: during, type: int }, { name: up, type: int }]
  returns: string
  doc: Block up to `during` ms for a button; `up` selects press/release edge.
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
- Review: user

### 3.0 Scope addenda (in-flight)

- **`test` fall-through fix (agreed in-task):** `command.cpp:511` `case hash("test")` lacks a `break`/`return`, so it falls through into `hardcopy` and returns `"ERROR hardcopy not implemented"`. The Phase-3 generated dispatch emits a `return` per case, so the fall-through is **eliminated by construction**; `test` will invoke the diagnostic and return its own response. Deliberate exception to acceptance criterion 4 (functional equivalence) — confirm at closure.

### 3.1 Implementation

Delivered in four phases; one source (`protocol/protocol.yaml`, 45 commands) feeds every surface.

- **Generator** (`protocol/`): Pydantic schema (`schema.py`) + loader/`fw_hash` (`load.py`) + emitters (`generate.py`) — Jinja for the client, string-builders for C++ and the doc table. `validate` / `generate` CLIs.
- **Client**: generated `CommandLine` (`command_line_autogen.py`); `Gfx` rewired to delegate (public API + conveniences intact); `Command`→`CommandExecutor`, module names aligned to classes.
- **Docs**: `README-protocol.md` command table in a managed block (prose preserved).
- **Server**: generated parse + replay dispatch (`*.autogen.inc`) + handler header (free-fn protos → linker-enforced); hand-written arsenal (`replay_*` TFT bindings, `handle_*` immediate handlers); `config` captured file-scope; `test`→`hardcopy` fall-through removed.
- **Tooling**: `make protocol-gen`, drift gate (`make -C protocol check`), generator goldens, CI `protocol` job.

Two user-led refinements improved the design mid-flight: naming converged on the codebase's ubiquitous term (`CommandLine`/`CommandExecutor`, module↔class alignment); the schema dropped a redundant `optional` flag (presence of `default` implies it) and spelled out `n`/`t` → `name`/`type`.

### 3.2 File inventory

33 files, +3086 / −736, 17 commits (`git diff --stat main...HEAD`).

- New `protocol/` subproject: spec, generator (`src/tft_protocol/`), `Makefile`, goldens (`tests/`), `uv.lock`.
- Generated stubs (committed): `command_line_autogen.py`, `command_dispatch.autogen.inc`, `replay_dispatch.autogen.inc`, `protocol_handlers.autogen.h`, the `README-protocol.md` table.
- `command.cpp` / `transaction.cpp`: switches → `#include` + hand-written arsenal (net large reduction).
- Client: `command_executor.py` (rename), `gfx.py` rewire, `tests/unit/test_command_line.py`.
- `Makefile` (`protocol-gen`), `.github/workflows/ci.yml` (`protocol` job).

### 3.3 Verification commands

| Command                                      | Checks                                        |
| -------------------------------------------- | --------------------------------------------- |
| `make -C protocol validate`                  | spec valid; 45 names + hashes unique          |
| `make -C protocol lint`                      | ruff check + format-check                     |
| `make -C protocol test`                      | generator goldens (5 outputs)                 |
| `make -C protocol check`                     | drift gate: regenerate+format == committed    |
| `make -C client-py check`                    | ruff + 36 host tests                          |
| `make -C server-esp32s3-rtft firmware-build` | compiles; flash 34%, DRAM 67%                 |
| `make -C server-esp32s3-rtft test-board`     | **hardware self-test — passed** (criterion 4) |

### 3.4 Demo scenario

Replayable at the merge commit:

```
# 1. one source defines a command end-to-end
grep -A4 'name: drawRect' protocol/protocol.yaml

# 2. regenerate every surface — nothing drifts
make protocol-gen && git diff --stat        # → no changes

# 3. the gate catches a stale / invalid spec
printf '\n- name: bogus\n' >> protocol/protocol.yaml
make -C protocol check                       # → ERROR (validation / stale stubs)
git checkout protocol/protocol.yaml

# 4. client + firmware build from the generated stubs
make -C client-py test                       # 36 pass
make -C server-esp32s3-rtft firmware-build   # DRAM 67%
```

### 3.5 Test coverage review

| Change                   | Decision                                                                                                                                             |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Generator emitters       | **Added** `tests/test_goldens.py` — feature-fixture spec → expected emission, all 5 outputs.                                                         |
| Real-spec regeneration   | **Added** drift gate (`make -C protocol check`) in CI — committed stubs must equal regenerated.                                                      |
| Client `CommandLine`     | **Added** `test_command_line.py` (bool→0/1, optional defaults, ints-tuple parse).                                                                    |
| `Gfx` rewire             | **Existing** `test_protocol.py` asserts wire strings (byte-identical) — exercises the new layer; still passes.                                       |
| Server codegen + arsenal | **Justified (no host test)**: firmware host-testing was parked (#25); covered by the compile gate + interactive `make test-board` (hardware-passed). |

### 3.6 Retrospective

Agent votes filled; User column for the reviewer (well / not well / surprise / don't care).

| #   | Point                                                                          | Agent    | User       |
| --- | ------------------------------------------------------------------------------ | -------- | ---------- |
| 1   | Single source across all four surfaces; drift gate enforces it                 | well     | well       |
| 2   | DRAM unchanged (67%), flash comparable — firmware equivalence held             | well     | well       |
| 3   | `handle_*`/`replay_*` split kept the spec free of C++ binding detail           | well     | well       |
| 4   | config-as-global over threading — cleaner handler signatures                   | well     | well       |
| 5   | `test`→`hardcopy` fall-through fixed by construction, not patched              | well     | well       |
| 6   | Drift gate is generate **+ format** + diff (not generate alone) — found late   | surprise | don't care |
| 7   | `.inc` clang-format non-idempotent → left generator-emitted, indented          | surprise | don't care |
| 8   | ruff reformatted a golden `.py` → late test failure; fixed via ruff exclude    | not well | ended well |
| 9   | Caught the optional-arg-dropped-from-`set()` generator bug before regen        | well     | well       |
| 10  | Naming + schema converged over several user-led rounds — productive refinement | well     | well       |

### 3.7 Verdict

Accept. Acceptance criteria 1–6 met; criterion 4 (functional equivalence) confirmed on hardware. The sole deliberate exception — the `test` fall-through (§ 3.0) — is a fix, not a regression.

## Governance trace

| Source                        | Clause                 | Action  | Note                                                                                        |
| ----------------------------- | ---------------------- | ------- | ------------------------------------------------------------------------------------------- |
| CLAUDE.md (Code-reuse)        | frameworks/libs        | applied | Pydantic + Jinja2 surfaced and confirmed before plan finalised                              |
| CLAUDE.md (Research methods)  | established methods    | applied | IDL/stub-gen is the standard cross-language single-source pattern                           |
| CLAUDE.md (YAGNI)             | drop unneeded          | applied | goldens scoped to feature axes, not params×returns cross-product                            |
| CLAUDE.md (Proportionality)   | cost vs problem        | applied | "now is the time" — user confirmed after triple-site cost shown                             |
| CLAUDE.md (Multiple interp)   | rank options           | applied | free-fns vs pure-virtual ranked → linker enforcement chosen                                 |
| CEREMONIES.md:13              | mandate gate           | applied | §1 + §2 user-attested before implementation; re-attested after schema edits                 |
| CLAUDE.md (Naming discipline) | what-not-how           | applied | converged on ubiquitous term: CommandLine / CommandExecutor                                 |
| CLAUDE.md (Convergence check) | reaching vs retreating | tension | naming ran several rounds — judged productive (added clarity), not scope-narrowing; mundane |
| CLAUDE.md (YAGNI)             | drop unneeded          | applied | dropped redundant `optional` flag + unused cross-arg defaults                               |
| CLAUDE.md (Task execution)    | massive → debrief      | applied | paused at each phase boundary for review                                                    |
| CLAUDE.md (Fact/inference)    | flag findings          | applied | surfaced + fixed the optional-arg-dropped-from-`set()` generator bug                        |
| CEREMONIES.md (test coverage) | §3.5 review            | applied | firmware host-test skipped — justified (#25), hardware self-test instead                    |

## Resource consumption

| Phase                            | Tokens (approx) | Wall time              |
| -------------------------------- | --------------- | ---------------------- |
| Mandate + plan (incl. revisions) | ~60k            | ~2 h                   |
| Phase 1 — client                 | ~70k            | ~1.5 h                 |
| Phase 2 — docs                   | ~25k            | ~30 min                |
| Phase 3 — server + hardware      | ~90k            | ~2 h                   |
| Phase 4 — tooling + goldens      | ~50k            | ~1 h                   |
| Closure                          | ~25k            | ~30 min                |
| **Total**                        | **~320k**       | **~7.5 h** over 2 days |

| Counter                | Value                              |
| ---------------------- | ---------------------------------- |
| Pre-commit hook fails  | ~3 (ruff format-check after edits) |
| Subagent invocations   | 0                                  |
| `/clear` events        | 0                                  |
| Memory rotation events | 0                                  |
| LOC changed            | +3086 / −736 (`git diff main...`)  |
| Files changed          | 33                                 |
