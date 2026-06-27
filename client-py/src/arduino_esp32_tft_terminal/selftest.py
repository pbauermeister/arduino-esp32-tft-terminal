"""On-board acceptance self-test (`make test-board`).

Drives a connected gadget over USB to verify the firmware correctly implements
the USB protocol primitives. It does NOT test the panel hardware or the
Adafruit library (trusted SOUP) — only what this project owns.

Two phases, interactive first so the user is needed only briefly at the start:

  Phase 1 — interactive (attended):
    1. a primitive gallery; the user confirms each screen by glance (y/n);
    2. guided button presses, asserted at low level (A/B/C) and high level
       (RESET -> reboot reported as the `R` event).

  Phase 2 — unattended (walk away):
    - every client primitive is sent and checked for a non-error response;
    - queries (width/height/getTextBounds) are sanity-checked;
    - a short soak cycles commands and asserts no comm errors / spurious reboots.

Not in CI — needs the gadget on USB. Run: `make test-board`
(`--unattended-only` skips Phase 1, e.g. for re-runs).
"""

import sys
import time
from typing import Callable

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.lib.board import Board
from arduino_esp32_tft_terminal.lib.channel import Channel
from arduino_esp32_tft_terminal.lib.gfx import Gfx


class Results:
    """Collects pass/fail checks and prints a summary."""

    def __init__(self) -> None:
        self.checks: list[tuple[str, bool, str]] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        # The test ID is already printed as the title (see _title); show result.
        self.checks.append((name, ok, detail))
        mark = "PASS" if ok else "FAIL"
        print(f"  -> {mark}" + (f" ({detail})" if detail else ""))

    @property
    def ok(self) -> bool:
        return all(ok for _, ok, _ in self.checks)

    def summary(self) -> None:
        print("\n=== summary ===")
        for name, ok, detail in self.checks:
            mark = "PASS" if ok else "FAIL"
            line = f"  {mark}  {name}"
            if not ok and detail:
                line += f"  ({detail})"
            print(line)
        passed = sum(1 for _, ok, _ in self.checks if ok)
        verdict = "ALL PASS" if self.ok else "FAILURES"
        print(f"\n  {passed}/{len(self.checks)} passed — {verdict}")


def connect() -> Board:
    """Open the serial port and configure the board (blocks until present)."""
    print("Connecting to the board over USB...")
    board = Board(Channel())
    board.configure()
    assert config.WIDTH and config.HEIGHT
    print(f"Connected: {config.WIDTH}x{config.HEIGHT}.")
    return board


# ----------------------------------------------------------------------------
# Phase 1 — interactive
# ----------------------------------------------------------------------------


def _ask(prompt: str) -> bool:
    return input(f"{prompt} [y/N] ").strip().lower().startswith("y")


def _gallery_shapes(gfx: Gfx) -> None:
    # Coordinates derive from the queried resolution so the screen fits any
    # board (the USB protocol is board-agnostic; only W/H and colour differ).
    w, h = config.WIDTH, config.HEIGHT
    r = max(4, h // 8)
    gfx.reset()
    gfx.fill_screen(0)
    gfx.set_fg_color(255, 255, 255)
    gfx.draw_line(0, 0, w // 3, h // 2, 1)
    gfx.draw_rect(w // 3, 2, w // 6, h // 5, 1)
    gfx.fill_rect(w // 2, 2, w // 6, h // 5, 1)
    gfx.set_fg_color(255, 0, 0)
    gfx.draw_circle(w * 3 // 4, h // 4, r, 1)
    gfx.fill_circle(w - r - 2, h // 4, r, 1)
    gfx.set_fg_color(0, 255, 0)
    gfx.draw_triangle(2, h - 2, w // 6, h - 2, w // 12, h * 2 // 3, 1)
    gfx.fill_triangle(w // 5, h - 2, w // 3, h - 2, w * 4 // 15, h * 2 // 3, 1)
    gfx.set_fg_color(64, 128, 255)
    gfx.draw_fast_hline(w // 2, h * 2 // 3, w // 3, 1)
    gfx.draw_fast_vline(w * 3 // 4, h // 2, h // 3, 1)
    gfx.draw_pixel(w // 2, h // 2, 1)
    gfx.display()


def _gallery_text(gfx: Gfx) -> None:
    w, h = config.WIDTH, config.HEIGHT
    gfx.reset()
    gfx.fill_screen(0)
    # top-left, base size
    gfx.set_text_color(255, 255, 255)
    gfx.set_text_size(1, 1)
    gfx.set_cursor(0, 0)
    gfx.print("top-left")
    # middle, double size
    gfx.set_text_size(2, 2)
    gfx.set_text_color(255, 255, 0)
    gfx.set_cursor(0, h // 3)
    gfx.print("SIZE 2")
    # bottom-right, measured with getTextBounds and right/bottom-aligned
    gfx.set_text_size(1, 1)
    gfx.set_text_color(0, 255, 255)
    label = "bottom-right"
    tw, th = gfx.get_text_bounds(0, 0, label)
    gfx.set_cursor(max(0, w - tw), max(0, h - th))
    gfx.print(label)
    gfx.display()


def _gallery_frame(gfx: Gfx) -> None:
    w, h = config.WIDTH, config.HEIGHT
    gfx.reset()
    gfx.fill_screen(0)
    # inset crosshatch (interior only — never touches the border)
    gfx.set_fg_color(64, 64, 64)
    for x in range(20, w - 1, 20):
        gfx.draw_fast_vline(x, 1, h - 2, 1)
    for y in range(20, h - 1, 20):
        gfx.draw_fast_hline(1, y, w - 2, 1)
    # 1px border as four explicit edge lines
    gfx.set_fg_color(255, 255, 255)
    gfx.draw_fast_hline(0, 0, w, 1)
    gfx.draw_fast_hline(0, h - 1, w, 1)
    gfx.draw_fast_vline(0, 0, h, 1)
    gfx.draw_fast_vline(w - 1, 0, h, 1)
    gfx.display()


_SHAPES_REF = """\
  ┌────────────────────┐
  │ ╲      □■    ○●    │
  │  ╲                 │
  │          ·   │     │
  │          ────┼─    │
  │ ◣ ◢          │     │
  └────────────────────┘
"""

_TEXT_REF = """\
  ┌────────────────────┐
  │ top-left           │  small, white
  │                    │
  │ SIZE 2             │  large, yellow
  │                    │
  │        bottom-right│  small, cyan
  └────────────────────┘
"""

GALLERY: list[tuple[str, Callable[[Gfx], None], str, str]] = [
    (
        "shapes",
        _gallery_shapes,
        "do the shapes match the reference (all present, placed alike)?",
        _SHAPES_REF,
    ),
    (
        "text",
        _gallery_text,
        "do the labels match the reference (text, size, colour, position)?",
        _TEXT_REF,
    ),
    (
        "frame",
        _gallery_frame,
        "a 1px border touching all four edges + an even interior crosshatch?",
        "",
    ),
]


def _title(test_id: str) -> None:
    print(f"\n=== {test_id} ===")


def phase1_gallery(board: Board, results: Results) -> None:
    for name, draw, question, reference in GALLERY:
        _title(f"gallery:{name}")
        draw(board.gfx)
        if reference:
            print("  expected layout:")
            print(reference)
        results.check(f"gallery:{name}", _ask(question))


# Seconds to wait for each interactive button press (None = wait forever).
BUTTON_TIMEOUT: float | None = 60


def _await_auto_button(
    board: Board, code: str, timeout: float | None = BUTTON_TIMEOUT
) -> set[str]:
    """In auto-report mode the board appends button codes to every OK response.
    Elicit responses (a cheap `display`) and accumulate codes until `code` is
    seen (or `timeout` elapses; None waits forever). Returns codes seen."""
    seen: set[str] = set()
    deadline = None if timeout is None else time.time() + timeout
    while deadline is None or time.time() < deadline:
        try:
            board.gfx.display()  # its OK response carries the current buttons
            seen |= board.auto_read_buttons()
        except Exception:
            pass
        if code in seen:
            break
        time.sleep(0.05)
    return seen


def phase1_buttons(board: Board, results: Results) -> None:
    # Buttons via auto-report mode (the path the apps use): once enabled, the
    # board appends button codes to every OK response.
    gfx = board.gfx
    board.clear_buttons()  # reset reboot counter so `R` isn't reported spuriously
    board.begin_auto_read_buttons()
    try:
        for code, label in [("A", "A (D0)"), ("B", "B (D1)"), ("C", "C (D2)")]:
            _title(f"button:{code}")
            gfx.reset()
            gfx.fill_screen(0)
            gfx.set_text_color(255, 255, 255)
            gfx.set_text_size(2, 2)
            gfx.set_cursor(0, config.HEIGHT // 3)
            gfx.print(f"PRESS {code}")
            gfx.display()
            print(f"  >>> press button {label}")
            seen = _await_auto_button(board, code)
            results.check(
                f"button:{code}", code in seen, f'saw {sorted(seen) or "nothing"}'
            )
            time.sleep(0.5)  # let the user release before the next prompt
    finally:
        board.end_auto_read_buttons()

    _title("button:reset")
    # Show the RESET prompt on the TFT (replaces the last "PRESS X" screen).
    # "PRESS RESET" doesn't fit on one line at this size, so stack it.
    gfx.reset()
    gfx.fill_screen(0)
    gfx.set_text_color(255, 255, 255)
    gfx.set_text_size(2, 2)
    gfx.set_cursor(0, config.HEIGHT // 4)
    gfx.print("PRESS")
    gfx.set_cursor(0, config.HEIGHT // 2)
    gfx.print("RESET")
    gfx.display()
    print("  >>> press the RESET button (the board reboots)")
    board.clear_buttons()
    deadline = None if BUTTON_TIMEOUT is None else time.time() + BUTTON_TIMEOUT
    detected = False
    while deadline is None or time.time() < deadline:
        try:
            if "R" in board.read_buttons():
                detected = True
                break
        except Exception:
            pass  # serial may drop across the reset; recovery re-opens
        time.sleep(0.2)
    results.check("button:reset", detected, "reset -> reboot reported as R")


# ----------------------------------------------------------------------------
# Phase 2 — unattended
# ----------------------------------------------------------------------------

PRIMITIVES: list[tuple[str, Callable[[Gfx], None]]] = [
    ("reset", lambda g: g.reset()),
    ("fillScreen", lambda g: g.fill_screen(0)),
    ("setFgColor", lambda g: g.set_fg_color(255, 0, 0)),
    ("setBgColor", lambda g: g.set_bg_color(0, 0, 32)),
    ("drawPixel", lambda g: g.draw_pixel(5, 5, 1)),
    ("drawLine", lambda g: g.draw_line(0, 0, 50, 30, 1)),
    ("drawRect", lambda g: g.draw_rect(2, 2, 40, 20, 1)),
    ("fillRect", lambda g: g.fill_rect(2, 2, 40, 20, 1)),
    ("drawCircle", lambda g: g.draw_circle(30, 30, 15, 1)),
    ("fillCircle", lambda g: g.fill_circle(30, 30, 15, 1)),
    ("drawTriangle", lambda g: g.draw_triangle(0, 0, 20, 0, 10, 20, 1)),
    ("fillTriangle", lambda g: g.fill_triangle(0, 0, 20, 0, 10, 20, 1)),
    ("drawFastHLine", lambda g: g.draw_fast_hline(0, 10, 50, 1)),
    ("drawFastVLine", lambda g: g.draw_fast_vline(10, 0, 40, 1)),
    ("setTextSize", lambda g: g.set_text_size(1, 1)),
    ("setTextColor", lambda g: g.set_text_color(255, 255, 255)),
    ("setCursor", lambda g: g.set_cursor(0, 0)),
    ("setTextWrapOn", lambda g: g.set_text_wrap_on()),
    ("setTextWrapOff", lambda g: g.set_text_wrap_off()),
    ("home", lambda g: g.home()),
    ("print", lambda g: g.print("selftest")),
    ("clear", lambda g: g.clear()),
    ("setRotation", lambda g: g.set_rotation(config.SCREEN_ROTATION)),
    ("display", lambda g: g.display()),
]


def phase2_unattended(board: Board, results: Results) -> None:
    gfx = board.gfx

    # Every client primitive must dispatch without an ERROR response.
    for name, call in PRIMITIVES:
        _title(f"cmd:{name}")
        try:
            call(gfx)
            results.check(f"cmd:{name}", True)
        except Exception as e:
            results.check(f"cmd:{name}", False, str(e))

    # Queries return sane values.
    _title("query:width")
    results.check("query:width", gfx.get_width() > 0)
    _title("query:height")
    results.check("query:height", gfx.get_height() > 0)
    _title("query:getTextBounds")
    w, h = gfx.get_text_bounds(0, 0, "Hi")
    results.check("query:getTextBounds", w > 0 and h > 0, f"{w}x{h}")

    # Short soak: cycle drawing, assert no comm errors / spurious reboots.
    _title("soak")
    print("  drawing for 5s...")
    boots_before = board.boots
    errors = 0
    end = time.time() + 5
    i = 0
    while time.time() < end:
        try:
            gfx.fill_screen(0)
            gfx.draw_circle(i % config.WIDTH, i % config.HEIGHT, 10, 1)
            gfx.display()
            i += 1
        except Exception:
            errors += 1
    results.check("soak:no-comm-errors", errors == 0, f"{errors} errors")
    results.check("soak:no-spurious-reboot", board.boots == boots_before)


def _show_done(board: Board, ok: bool) -> None:
    """Leave a clear end screen on the gadget (not the leftover soak frame)."""
    gfx = board.gfx
    gfx.reset()
    gfx.fill_screen(0)
    gfx.set_text_size(1, 1)
    gfx.set_text_color(255, 255, 255)
    gfx.set_cursor(0, config.HEIGHT // 4)
    gfx.print("All tests done")
    gfx.set_text_size(2, 2)
    if ok:
        gfx.set_text_color(0, 255, 0)
    else:
        gfx.set_text_color(255, 0, 0)
    gfx.set_cursor(0, config.HEIGHT // 2)
    gfx.print("PASS" if ok else "FAIL")
    gfx.display()


def main() -> None:
    unattended_only = "--unattended-only" in sys.argv
    board = connect()
    results = Results()
    if not unattended_only:
        phase1_gallery(board, results)
        phase1_buttons(board, results)
    phase2_unattended(board, results)
    results.summary()
    _show_done(board, results.ok)
    sys.exit(0 if results.ok else 1)


if __name__ == "__main__":
    main()
