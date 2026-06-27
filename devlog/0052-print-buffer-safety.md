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

Make the buffered `print` path **totally safe** — no silent truncation of printed text — regardless of text length or which firmware version the client talks to. FIFO overflow safety is already provided firmware-side (§ 1.3).

Two parts:

1. **Capability query (firmware → client):** `getPrintMaxLength` reports the per-`print` text capacity, already accounting for the `\0` terminator. If the query errors (firmware too old to support it), the client assumes a **default safe for every no-query firmware** (§ 2.2).
2. **Client slicing:** the Python library splits a `print` whose text exceeds that capacity into multiple `print` calls, each within it — long text spans calls, never truncated.

### 1.1 Acceptance criteria

1. `getPrintMaxLength` returns the usable text length = `PRINT_LENGTH - 1` (the `\0` is subtracted firmware-side).
2. New client + new firmware: a `print` of arbitrary length renders in full (hardware-verified).
3. New client + a **no-query** firmware (old pre-Claude _or_ #51's build): prints render without truncation (client default fallback).
4. Host tests cover the slicing logic (incl. escape-sequence boundaries) and the default fallback; firmware CI still compiles.

### 1.2 Scope — `str` is print-only

`Action.str` is written **only** by `print`; all other buffered commands carry numeric args. `getTextBounds` also takes text but reads it from the **command-line buffer** (`read_last_str`, bounded by `BUFFER_LENGTH=200`), not `Action.str` — unaffected by this capacity and out of slicing scope.

### 1.3 Flow control is already done (no depth query)

The action FIFO cannot overflow: #50's `add()` **auto-commits when full** (firmware-side). The client therefore needs **no** buffer-depth query and does no depth budgeting — flow control is entirely the firmware's responsibility. (Proven: the draw-heavy `bubbles-air` ran with no crash.) A single frame exceeding the FIFO depth flushes mid-frame (rare flicker; `ACTIONS_COUNT=1000`) — inherent and accepted; true incremental drain would need a `commit()` redesign, out of scope.

## 2. Execution plan (design)

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 2.1 Firmware — the query

One new query command, `get…`-style (like `getRotation` / `getTextBounds`):

- **`getPrintMaxLength`** → maximum **unescaped** text length one buffered `print` stores. The firmware subtracts the terminator: `PRINT_LENGTH - 1` (currently `128 - 1 = 127`). Reporting usable characters means the client slices to exactly this value, with no off-by-one and no knowledge of the terminator.

Bump the firmware `CHANGES.md` (new command = new firmware version).

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

1. **FW:** add `getPrintMaxLength`; bump firmware `CHANGES.md`. Verify by compile + raw query (expect `127`).
2. **Client:** negotiate the cap on connect (default `127`); host-test the default-fallback path.
3. **Client:** print slicing (escaping-safe); host-test chunk boundaries + escape sequences.
4. **Hardware:** flash (ROM download mode) + runtime-test a > 127-char print renders in full.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

(Pending implementation.)

## Governance trace

| Source                      | Clause          | Action  | Note                                            |
| --------------------------- | --------------- | ------- | ----------------------------------------------- |
| CLAUDE.md (Framing)         | desired outcome | applied | "no truncation" invariant; FIFO safety reused from #50 |
| CLAUDE.md (Multiple interp) | rank options    | applied | default 127 vs 199 surfaced + ranked            |
| CLAUDE.md (YAGNI)           | drop unneeded   | applied | no depth query — flow control already firmware-side |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Design | ~22k           | ~35 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 1 (devlog — design only) |
