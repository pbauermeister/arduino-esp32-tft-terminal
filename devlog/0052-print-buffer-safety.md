# 0052 — Print/buffer total safety: getPrintMaxLength query + client slicing

- GH issue: #52
- Branch: impl/0052-print-buffer-safety
- Opened: 2026-06-28
- Closed: —

### Context

Predecessors: #50 (DRAM trim — shrank `Action.str` to `PRINT_LENGTH=128`, fixed the non-terminating `strncpy`, and fixed the `sizeof`-vs-count `add()` overflow so the FIFO **auto-commits when full**). This task removes the last truncation risk (long prints) and makes the print-text capacity runtime-negotiated.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Make the buffered draw/print path **totally safe** — no silent truncation of printed text, no dropped or lost buffered action — regardless of text length, frame size, or which firmware version the client talks to.

Three parts:

1. **Capability query (firmware → client):** `getPrintMaxLength` reports the per-`print` text capacity, already accounting for the `\0` terminator. If the query errors (firmware too old to support it), the client assumes a **default safe for every no-query firmware** (§ 2.2).
2. **Client slicing:** the Python library splits a `print` whose text exceeds that capacity into multiple `print` calls, each within it — long text spans calls, never truncated.
3. **Firmware flow control (fix):** when the action FIFO is full, auto-commit the buffer, **then** queue the new action (currently the triggering action is dropped, § 1.3). The client is back-pressured for free: the OK response only arrives after the auto-commit completes.

### 1.1 Acceptance criteria

1. `getPrintMaxLength` returns the usable text length = `PRINT_LENGTH - 1` (the `\0` is subtracted firmware-side).
2. New client + new firmware: a `print` of arbitrary length renders in full (hardware-verified).
3. New client + a **no-query** firmware (old pre-Claude _or_ #51's build): prints render without truncation (client default fallback).
4. A frame with more buffered actions than the FIFO depth executes **all** of them (none dropped): the firmware auto-commits then queues the new action; the client is back-pressured by the delayed response. No overflow/corruption.
5. Host tests cover the slicing logic (incl. escape-sequence boundaries) and the default fallback; firmware CI still compiles.

### 1.2 Scope — `str` is print-only

`Action.str` is written **only** by `print`; all other buffered commands carry numeric args. `getTextBounds` also takes text but reads it from the **command-line buffer** (`read_last_str`, bounded by `BUFFER_LENGTH=200`), not `Action.str` — unaffected by this capacity and out of slicing scope.

### 1.3 Flow control is firmware-side (no depth query) — and needs a fix

The client needs **no** buffer-depth query and does no budgeting: when the FIFO fills, the firmware auto-commits (flushes) and the client is naturally back-pressured by the OK response arriving only after the commit. _But_ #50's `add()` auto-commit has an off-by-one: it commits `actions[0..next-1]` and **drops the just-written `actions[next]`** that triggered the flush. This task fixes it (§ 2.1) so the triggering action is queued after the flush, not lost. A single frame exceeding `ACTIONS_COUNT=1000` still flushes mid-frame (rare flicker) — inherent and accepted; true incremental drain would need a `commit()` redesign, out of scope.

## 2. Execution plan (design)

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 2.1 Firmware — query + flow-control fix

**(a) New query command** (`get…`-style, like `getRotation` / `getTextBounds`):

- **`getPrintMaxLength`** → maximum **unescaped** text length one buffered `print` stores. The firmware subtracts the terminator: `PRINT_LENGTH - 1` (currently `128 - 1 = 127`). Reporting usable characters means the client slices to exactly this value, with no off-by-one and no knowledge of the terminator.

**(b) Auto-commit flow-control fix** — flush when full and **keep** the new action (currently it is dropped). Move the full-check into `action()` (flush to make room), leaving `add()` to only advance:

```c
Action* action() { if (next == ACTIONS_COUNT) commit(); return &actions[next]; }
void    add()    { if (!enabled) { do_action(&actions[next]); return; } next++; }
```

The overflowing command triggers `action()` → `commit()` (executes all `ACTIONS_COUNT`), then writes the new action into the fresh `actions[0]`; its OK response returns only after the commit, halting the client. This replaces #50's `add()` full-check, which committed `0..next-1` and dropped `actions[next]`.

Bump the firmware `CHANGES.md` (new command + behaviour change = new firmware version).

### 2.2 Default when the query errors (the key safety point)

Used when the firmware lacks `getPrintMaxLength` (→ `ERROR unknown cmd`). The no-query firmwares:

| Firmware | `str` capacity | usable text | terminator |
| --- | --- | --- | --- |
| pre-Claude (≤ #6) | `BUFFER_LENGTH = 200` | 199 | **buggy** (`strncpy`, no NUL) |
| #51 (DRAM trim) | `PRINT_LENGTH = 128` | 127 | fixed |

Safe default = the **minimum usable text across all no-query firmwares = 127** (the floor is #51's 128, _not_ pre-Claude's 199). 127 is also ≤ pre-Claude's 199, so it stays "compatible with all old (pre-Claude) firmware" as required — just more conservative.

**Decision to confirm:** the mandate says "compatible with all _old_ (pre-Claude) FW", which alone would allow 199. But #51 (a no-query Claude-era build already on the board, `str=128`) is the real floor; defaulting to 199 would silently truncate prints > 127 on a #51 board. Recommend **127**. Prints are typically ≤ one screen line (~37 chars), so the conservative default costs nothing in practice.

### 2.3 Client — capability negotiation

On connect (in `board._configure`, beside the resolution/version query): query `getPrintMaxLength`, wrapped in try/except → default `127` on error. Store on `gfx`/board; print it in the connect banner.

### 2.4 Client — print slicing

`Gfx.print(s)` splits `s` so each transmitted `print` stores ≤ `getPrintMaxLength` **unescaped** characters:

- Measure by the firmware's stored (unescaped) length, and **never split an escape sequence** (e.g. between `\` and `n`). Approach: slice the logical text into ≤ N runs, then escape each chunk for the wire — satisfies both invariants.
- Chunks render sequentially (the cursor advances) — on-screen result identical to one long print.
- **Prerequisite:** pin the escaping contract (today `gfx.print` sends `print {s}` raw and the firmware `unescape_inplace`s `\n` / `\\`); the slicer must agree. Clarifying it is part of this task.

### 2.5 Relation to J

`getPrintMaxLength` makes the firmware/client `PRINT_LENGTH` agreement **runtime-negotiated** instead of a duplicated constant — one less client/firmware duplication, a step toward **Protocol single-source (J)**. Note it there.

### 2.6 Phased implementation (each independently verifiable)

1. **FW:** add `getPrintMaxLength` + the `action()`/`add()` flow-control fix; bump firmware `CHANGES.md`. Verify by compile + raw query (expect `127`).
2. **Client:** negotiate the cap on connect (default `127`); host-test the default-fallback path.
3. **Client:** print slicing (escaping-safe); host-test chunk boundaries + escape sequences.
4. **Hardware:** flash (ROM download mode); runtime-test (a) a > 127-char print renders in full, (b) a > 1000-action frame draws fully with no dropped action.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Implementation

Implemented per the user's explicit verbal "go, implement" — the in-file review gate was waived by the user for this task; no attestation is fabricated (this section stays `Review: pending`).

- **FW:** `getPrintMaxLength` (= `PRINT_LENGTH - 1`); `action()` flush-when-full + `add()` simplified — fixes #50's drop; `do_action` no-op; `CHANGES.md` → **0.2.0**. Compiles on 3.3.10 (67% DRAM), format clean.
- **Client:** `config.DEFAULT_PRINT_MAX=127` + `PRINT_WIRE_MAX=190`; `Gfx.print_max` default + `get_print_max_length()`; `Gfx.print()` slices via `_slice_print` (escape-safe; `str` **and** wire limits); `board._configure` negotiates it and banners it.
- **Host tests:** `test_print_slicing.py` — 9 tests (slicing, escape boundaries, wire cap, default, negotiation + fallback). ruff clean, **33 tests pass**.
- **On-board checks:** integrated into the selftest as `phase1_buffer` — the **last interactive checks** (`buffer:slicing`, `buffer:flow-control`), so they appear in the final PASS/FAIL summary. No separate target (the standalone `buffer_safety.py` and `test-board-buffer` were folded in). `make test-all` = `lint` + `test` + `test-board`.

### 3.2 Hardware verification (done)

- Flashed 0.2.0 (ROM download mode). Board-verified: a 292-char print rendered **in full** (sliced); the rainbow drew **flawlessly** with visible latency spikes at the auto-commit flushes (back-pressure).
- **Oracle proven sensitive:** a temporary tamper dropping ~1 % of `drawPixel` commands produced clearly visible white specks — so a passing (speck-free) run is meaningful.
- `phase1_buffer` finale tuned: a **centered rainbow rect** (~133×75, ~19 countable commits, ~40 s — not the whole screen), no `OK` marker.
- **Full `make test-board` re-run: all passed**, including `buffer:slicing` and `buffer:flow-control`.

### 3.3 Verdict

Accept. (Devlog sections remain `Review: pending` — implemented on verbal go-ahead; the user may attest on `main`.)

## Governance trace

| Source                      | Clause          | Action  | Note                                            |
| --------------------------- | --------------- | ------- | ----------------------------------------------- |
| CLAUDE.md (Framing)         | desired outcome | applied | "no truncation" invariant; FIFO safety reused from #50 |
| CLAUDE.md (Multiple interp) | rank options    | applied | default 127 vs 199 surfaced + ranked            |
| CLAUDE.md (YAGNI)           | drop unneeded   | applied | no depth query — flow control is firmware-side      |
| CLAUDE.md (Fact/inference)  | flag findings   | applied | surfaced #50's `add()` off-by-one drop; fixed here  |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Design | ~22k           | ~35 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 1 (devlog — design only) |
