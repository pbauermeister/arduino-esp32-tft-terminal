# 0024 — Firmware host-test feasibility (study)

- GH issue: #24
- Branch: study/0024-firmware-test-study
- Opened: 2026-06-27

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Research only (no implementation). Answers three questions about testing the gadget's firmware / USB protocol off-board.

## Mandate

1. How much can be tested **without** firmware (FW) changes?
2. What new commands / FW changes would tests need (e.g. simulating button presses)?
3. Has the board/display been **updated to allow pixel readback**, or was it ever possible in some form?

## 1. How much is host-testable without firmware changes

The firmware is well-layered for this. The protocol interpreter is essentially a pure function over text, and hardware is touched only at the edges.

| Layer | File | Hardware coupling | Host-testable without FW change? |
| --- | --- | --- | --- |
| Command parse + dispatch | `command.cpp::interpret()` (`switch(hash(...))`) | only `Serial.printf` (error log) + button reads | **Yes** |
| Compile-time command hash | `command.h::hash()` | none | **Yes** |
| Transaction buffering/commit | `transaction.cpp` (`add`/`commit`/`do_action`) | indirect (calls display layer) | **Yes** |
| Command → draw-call mapping | `esp32s3-display.h/.cpp` (thin `tft.*` wrappers) | `Adafruit_ST7789` | **Yes**, against a recording mock |
| Button **read** → response | `read_buttons`, `wait_buttons` | `Button` class (GPIO) | **Yes**, against a mock `Button` |

What this buys: feeding a command line and asserting (a) the answer (`OK` / `ERROR …` / queried value), and (b) the resulting sequence of GFX calls (`drawCircle(10,20,5,…)`). **That sequence is the automatable proxy for "reading back the screen"** — the mock display _is_ a readable record of what would be drawn. Button readback (`readButtons` → `"AB"`) is testable by scripting the mock `Button`.

**Stubs required** (host build, no FW change): `Arduino.h` essentials (`pinMode`/`digitalWrite`/`millis`/`delay`/`yield`), a `Stream`/`Serial` stub, a `Button` stub, and a recording `Adafruit_ST7789`/`Adafruit_GFX` mock. `neopixel.*` (uses `Adafruit_TestBed`) is off the interpreter path — stub or exclude.

**Verdict:** the protocol interpreter + transaction logic + draw-call mapping + button readback — i.e. the gadget's real logic — is host-testable with **no firmware change**. The cost is a C++ host harness (stub headers + a test framework), which is real scaffolding, not a quick add.

## 2. New commands / FW changes tests would need

- **Button simulation.** There is no way to inject a press today. Two options:
  - _Host-only (no FW change):_ mock the `Button` class and script `pressed()`/`released()`/`read()`. Sufficient for host unit/integration tests of the interpreter and button reporting.
  - _On-target (small FW change):_ add a command, e.g. `simulateButton <idx> <0|1>`, that drives the button state used by `read_buttons`/`wait_buttons`. Needed only if you want to exercise the **real board's** button→protocol path over USB (an end-to-end test). The protocol already separates **edges** (`waitButton`, auto-read events) from **state** (`readButtons`), so a sim command should set press (down edge), release (up edge), and held (level).
- **Pixel readback command** — see §3; optional, FW change.

## 3. Pixel / screen readback — not available, never reliably was

Three independent layers, all negative:

- **Firmware**: no readback path. No `tft.readPixel`/`readRect`, no `GFXcanvas`/shadow framebuffer; the only retained state is `fg_color`/`bg_color`. The display is write-only from the firmware's view.
- **Library**: `Adafruit_ST7789` is **write-only** — its class reference exposes no `readPixel`/`readRect`/`readcommand`. (Adafruit's ST77xx SPI driver does not provide working pixel reads.)
- **Hardware**: the ST7789 controller has internal GRAM and a RAM-read (`RAMRD`) command _in principle_, but reads over SPI on these Adafruit breakouts are unsupported/unreliable, and the panel's data-out line isn't a confirmed route. The board's "MISO / GPIO37" cited online is the Feather's shared SPI bus (SD card, etc.), **not** a verified TFT read path.

**Has it been "updated" to allow readback?** No — no board, firmware, or library change enables it, and it was never reliably possible in this stack. Your assumption holds: you cannot read the panel back.

**But readback can be _synthesised in firmware_** — and this is the key option. Mirror every draw into an in-memory `GFXcanvas16` (240×135×2 ≈ **63.4 KB**, comfortable on the ESP32-S3's RAM/PSRAM), and add a `readPixel x y` / `readRect …` command that returns from the canvas. That gives **true on-board screen-state assertions** over USB, independent of whether the panel supports hardware read. The host-test mock does the same thing host-side (record draws into a buffer and assert).

## Recommendation

1. **Primary, no FW change — host tests of the interpreter.** A small C++ host build of `command.cpp` + `transaction.cpp` + a stub display layer with a **recording** `Adafruit_ST7789` mock + a stub `Button`, driven by a test framework. Assert: command line → expected answer; draw command → expected GFX-call sequence; scripted button state → `readButtons` response. This verifies the gadget's actual logic off-board. Right-size it: start with parse/dispatch + a handful of draw commands + button reads, not full coverage.
2. **Optional FW changes, only if you want on-target end-to-end tests:**
   - `simulateButton <idx> <0|1>` — drive the button path over real USB.
   - A shadow `GFXcanvas16` + `readPixel`/`readRect` — assert actual screen **state** on the board (the closest thing to "read back the screen" the hardware will ever give).
3. **Not automatable:** the real TFT panel's pixels (no hardware readback) → stays a manual visual smoke (Tier 3).

Effort note: the host harness (stub Arduino headers + a C++ test runner — Unity / Catch2 / GoogleTest) is the bulk of the work; the tests themselves are then cheap. This is a larger task than the Python side.

### Open decisions (for review)

1. C++ test framework — Unity (Arduino-friendly), Catch2, or GoogleTest/gmock (best mocking)?
2. Accept the host-harness scaffolding cost for §1, and scope the first slice?
3. The optional FW changes (§2: `simulateButton`; shadow canvas + `readPixel`) — do them now, or defer until the host tests exist?

## Sources

- [Adafruit_ST7789 class reference (write-only API)](https://adafruit.github.io/Adafruit-ST7735-Library/html/class_adafruit___s_t7789.html)
- [Adafruit ESP32-S3 Reverse TFT Feather — Built-In TFT](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/built-in-tft)
- [Adafruit ESP32-S3 Reverse TFT Feather — Pinouts](https://learn.adafruit.com/esp32-s3-reverse-tft-feather/pinouts)
- [Adafruit-ST7735-Library (ST7789 driver source)](https://github.com/adafruit/Adafruit-ST7735-Library)

## Governance trace

| Source                      | Clause                  | Action  | Note                                       |
| --------------------------- | ----------------------- | ------- | ------------------------------------------ |
| CLAUDE.md (Task nature)     | exploratory             | applied | research task; extrapolation marked        |
| CLAUDE.md (References)      | sources for external claims | applied | library/hardware claims cited              |
| CLAUDE.md (Proportionality) | proportionality         | applied | flagged host-harness cost; phased recommendation |

## Resource consumption

| Phase    | Tokens (approx) | Wall time |
| -------- | --------------- | --------- |
| Research | ~60k (subagent + web) | ~30 min |

| Counter              | Value |
| -------------------- | ----- |
| Subagent invocations | 1     |
| Web searches         | 2 + 1 fetch |
