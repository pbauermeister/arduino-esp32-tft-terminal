# 0052 — Print/buffer total safety: capability query + slicing + flow control

- GH issue: #52
- Branch: impl/0052-print-buffer-safety
- Opened: 2026-06-28
- Closed: —

### Context

Predecessors: #50 (DRAM trim — shrank `Action.str` to `PRINT_LENGTH=128`, fixed the non-terminating `strncpy` and the `sizeof`-vs-count `add()` overflow). This task hardens the path so it is overflow- and truncation-proof _by construction_, across firmware versions.

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Make the buffered-draw path **totally safe** end-to-end — no silent truncation of printed text, no FIFO overflow — regardless of frame size, text length, or which firmware version the client is talking to.

Three parts:

1. **Capability query (firmware → client):** a command that reports the per-action print-text capacity (and the FIFO depth). If the query errors (a firmware too old to support it), the client assumes a **default safe for every no-query firmware** (see § 2.2).
2. **Client slicing:** the Python library splits a `print` whose text exceeds the capacity into multiple `print` calls, each within the capacity — long text spans calls, never truncated.
3. **Flow control:** when the action FIFO would overflow, apply back-pressure (flush/wait) rather than dropping or corrupting — the firmware's auto-commit-on-full (#50) is the hard net; the client makes flushes predictable.

### 1.1 Acceptance criteria

1. A board command returns the print-text capacity; a second value (or command) reports the FIFO depth.
2. With the new client + new firmware: a `print` of arbitrary length renders in full (verified on hardware).
3. With the new client + a **no-query** firmware (old pre-Claude _or_ #50's #51 build): prints render without truncation or overflow (the client falls back to a safe default).
4. A frame with more buffered draws than the FIFO depth completes without crash/corruption (flush-based back-pressure; flicker for such frames is acceptable and documented).
5. Host tests cover the slicing logic and the default fallback; firmware CI still compiles.

### 1.2 Scope note — `str` is print-only

`Action.str` is written **only** by the `print` command; all other buffered commands carry numeric args. `getTextBounds` also takes text but reads it from the **command-line buffer** (`read_last_str`, bounded by `BUFFER_LENGTH=200`), not `Action.str` — so it is unaffected by the `str` capacity and out of slicing scope. (If a caller ever measures text longer than the command line allows, that is a separate, pre-existing command-buffer limit — noted, not addressed here.)

## 2. Execution plan (design)

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 2.1 Firmware

Two new query commands (single-value each, matching the `width`/`height` convention):

- **`printMax`** → the maximum **unescaped** text length one buffered `print` stores. The firmware MUST subtract the `\0` terminator: `printMax = PRINT_LENGTH - 1` (currently `128 - 1 = 127`). It reports usable characters, so the client can slice to exactly this value with no off-by-one — the client never needs to know about the terminator.
- **`bufferDepth`** → the FIFO slot count (`ACTIONS_COUNT`, currently `1000`).

(Alternative: a single `caps` command returning both space-separated — fewer round-trips, extensible — at the cost of departing from the single-value query style. Recommend two single-value queries for consistency; revisit if more caps appear.)

Keep #50's **auto-commit-on-full** in `add()` as the hard overflow net (no corruption regardless of client behaviour).

### 2.2 Default when the query errors (the key safety point)

The default is used when the firmware lacks `printMax` (raises `ERROR unknown cmd`). The firmwares that lack it are:

| Firmware | `str` capacity | usable text | terminator |
| --- | --- | --- | --- |
| pre-Claude (≤ #6) | `BUFFER_LENGTH = 200` | 199 | **buggy** (`strncpy`, no NUL) |
| #51 (DRAM trim) | `PRINT_LENGTH = 128` | 127 | fixed |

The safe default is the **minimum usable text across all no-query firmwares = 127** (driven by #51, _not_ pre-Claude's 199). 127 is also ≤ pre-Claude's 199, so it remains "compatible with all old (pre-Claude) firmware" as required — just more conservative.

**Design decision to confirm:** the mandate says "compatible with all _old_ (pre-Claude) FW", which alone would allow 199. But #51 (a Claude-era build already on the board, no query, `str=128`) is the real floor. Defaulting to **127** covers pre-Claude _and_ an un-reflashed #51 board; defaulting to 199 would silently truncate prints > 127 on a #51 board. Recommend **127**. (Prints are typically ≤ one screen line ~37 chars, so the smaller default costs nothing in practice.)

`bufferDepth` default: `1000` has been stable historically; a wrong value here is still caught by the firmware net, so the default is non-critical — use `1000`.

### 2.3 Client — capability negotiation

On connect (in `board._configure`, where the resolution is already queried): query `printMax` and `bufferDepth`, each wrapped in try/except → defaults `127` / `1000` on error. Store on the board/gfx. Print the values alongside the resolution/version banner.

### 2.4 Client — print slicing

`Gfx.print(s)` splits `s` so each transmitted `print` stores ≤ `printMax` **unescaped** characters:

- Measure by the firmware's stored (unescaped) length, and **never split an escape sequence** (e.g. between `\` and `n`). Approach: slice the logical text into ≤ `printMax` runs, then escape each chunk for the wire — guarantees both invariants.
- Chunks render sequentially (the cursor advances), so the on-screen result is identical to one long print.
- **Prerequisite:** pin the print escaping contract (today `gfx.print` sends `print {s}` raw and the firmware `unescape_inplace`s `\n`/`\\`). The slicer must agree with that contract; clarifying it is part of this task.
- Wire each sliced print as a normal buffered action → counts toward flow control (§ 2.5).

### 2.5 Client — flow control (FIFO)

The FIFO drains only on `display` (a full commit) — there is no partial drain, so "making room" means flushing. Design:

- **Net (firmware):** `add()` auto-commits when full (#50) — guarantees no corruption even if the client miscounts.
- **Predictable (client):** the command layer counts buffered actions since the last `display`; before sending one that would exceed `bufferDepth`, it issues a `display` itself. This turns surprise mid-frame firmware flushes into client-controlled ones, and keeps the count honest across sliced prints.
- **Inherent limit (document):** a single frame with > `bufferDepth` draws cannot be shown atomically; it will flush mid-frame (flicker). `bufferDepth=1000` makes this rare. True incremental drain would require redesigning `commit()` — out of scope.
- _Alternative considered:_ a firmware `FULL` back-pressure response (client flushes + retries). More authoritative but a protocol change that removes the silent net; deferred unless the budgeting proves insufficient.

### 2.6 Coupling / relation to J

`printMax` makes the firmware/client `PRINT_LENGTH` agreement **runtime-negotiated** rather than a duplicated constant — it removes one instance of the client/firmware duplication that the **Protocol single-source (J)** item targets. Note in J that this query is a step in that direction.

### 2.7 Phased implementation (each independently verifiable)

1. **FW:** add `printMax` + `bufferDepth` queries; bump firmware `CHANGES.md`. Verify by compile + a raw query.
2. **Client:** negotiate caps on connect (with defaults); host test the default-fallback path.
3. **Client:** print slicing (escaping-safe); host tests for chunk boundaries + escape sequences.
4. **Client:** FIFO budgeting/flush; host test the count/flush logic.
5. **Hardware:** flash (ROM download mode) + runtime-test long prints and a draw-heavy app; confirm no truncation/crash.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

(Pending implementation.)

## Governance trace

| Source                      | Clause          | Action  | Note                                            |
| --------------------------- | --------------- | ------- | ----------------------------------------------- |
| CLAUDE.md (Framing)         | desired outcome | applied | "totally safe path" framed as invariant, not checks |
| CLAUDE.md (Multiple interp) | rank options    | applied | default 127 vs 199 surfaced + ranked            |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Design | ~18k           | ~25 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 1 (devlog — design only) |
