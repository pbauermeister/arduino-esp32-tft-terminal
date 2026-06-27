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

    def check(self, name: str, ok: bool, detail: str = '') -> None:
        self.checks.append((name, ok, detail))
        mark = 'PASS' if ok else 'FAIL'
        print(f'  [{mark}] {name}' + (f' — {detail}' if detail else ''))

    @property
    def ok(self) -> bool:
        return all(ok for _, ok, _ in self.checks)

    def summary(self) -> None:
        passed = sum(1 for _, ok, _ in self.checks if ok)
        total = len(self.checks)
        print(f'\nself-test: {passed}/{total} checks passed.')
        if not self.ok:
            print('Failed:')
            for name, ok, detail in self.checks:
                if not ok:
                    print(f'  - {name}' + (f' ({detail})' if detail else ''))


def connect() -> Board:
    """Open the serial port and configure the board (blocks until present)."""
    print('Connecting to the board over USB...')
    board = Board(Channel())
    board.configure()
    assert config.WIDTH and config.HEIGHT
    print(f'Connected: {config.WIDTH}x{config.HEIGHT}.')
    return board


# ----------------------------------------------------------------------------
# Phase 1 — interactive
# ----------------------------------------------------------------------------


def _ask(prompt: str) -> bool:
    return input(f'{prompt} [y/N] ').strip().lower().startswith('y')


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
    gfx.set_text_color(255, 255, 255)
    gfx.set_text_size(1, 1)
    gfx.set_cursor(0, 0)
    gfx.print('size 1x1 top-left')
    gfx.set_text_size(2, 2)
    gfx.set_text_color(255, 255, 0)
    gfx.set_cursor(0, h // 3)
    gfx.print('SIZE 2')
    gfx.set_text_size(1, 1)
    gfx.set_text_color(0, 255, 255)
    gfx.set_cursor(w // 2, h - 10)
    gfx.print('bottom-right')
    gfx.display()


def _gallery_frame(gfx: Gfx) -> None:
    gfx.reset()
    gfx.fill_screen(0)
    gfx.set_fg_color(255, 255, 255)
    # 1px border exactly at the screen edge
    gfx.draw_rect(0, 0, config.WIDTH, config.HEIGHT, 1)
    # crosshatch on round coordinates
    gfx.set_fg_color(64, 64, 64)
    for x in range(0, config.WIDTH, 20):
        gfx.draw_fast_vline(x, 0, config.HEIGHT, 1)
    for y in range(0, config.HEIGHT, 20):
        gfx.draw_fast_hline(0, y, config.WIDTH, 1)
    gfx.display()


GALLERY: list[tuple[str, Callable[[Gfx], None], str]] = [
    (
        'shapes',
        _gallery_shapes,
        'lines, rects, circles, triangles, hline/vline, pixel — all present and correctly placed?',
    ),
    (
        'text',
        _gallery_text,
        'three text labels, right size/colour/position, no wrap artefacts?',
    ),
    (
        'frame',
        _gallery_frame,
        'a 1px border touching all four edges + an even crosshatch grid?',
    ),
]


def phase1_gallery(board: Board, results: Results) -> None:
    print('\n== Phase 1a: primitive gallery (glance check) ==')
    for name, draw, question in GALLERY:
        draw(board.gfx)
        results.check(f'gallery:{name}', _ask(question))


def _poll_for_button(board: Board, code: str, timeout: int = 15) -> set[str]:
    """Poll `readButtons` until `code` is pressed (or timeout). Returns all
    codes seen (for diagnostics when nothing matches)."""
    seen: set[str] = set()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            b = board.read_buttons()
        except Exception:
            b = set()
        seen |= b
        if code in b:
            break
        time.sleep(0.05)
    return seen


def phase1_buttons(board: Board, results: Results) -> None:
    # Read the gadget's buttons by polling — no terminal input here.
    print('\n== Phase 1b: buttons — press the button ON THE GADGET ==')
    board.clear_buttons()  # reset reboot counter so `R` isn't reported spuriously
    for code, label in [('A', 'A (D0)'), ('B', 'B (D1)'), ('C', 'C (D2)')]:
        print(f'  >>> press and hold button {label} for ~1s (up to 15s)...')
        seen = _poll_for_button(board, code)
        results.check(
            f'button:{code}', code in seen, f'saw {sorted(seen) or "nothing"}'
        )
        time.sleep(1)  # give the user time to release before the next prompt

    print('  >>> now press the RESET button (the board reboots)...')
    board.clear_buttons()
    deadline = time.time() + 20
    detected = False
    while time.time() < deadline:
        try:
            if 'R' in board.read_buttons():
                detected = True
                break
        except Exception:
            pass  # serial may drop across the reset; recovery re-opens
        time.sleep(0.2)
    results.check('button:R (reset->reboot)', detected)


# ----------------------------------------------------------------------------
# Phase 2 — unattended
# ----------------------------------------------------------------------------

PRIMITIVES: list[tuple[str, Callable[[Gfx], None]]] = [
    ('reset', lambda g: g.reset()),
    ('fillScreen', lambda g: g.fill_screen(0)),
    ('setFgColor', lambda g: g.set_fg_color(255, 0, 0)),
    ('setBgColor', lambda g: g.set_bg_color(0, 0, 32)),
    ('drawPixel', lambda g: g.draw_pixel(5, 5, 1)),
    ('drawLine', lambda g: g.draw_line(0, 0, 50, 30, 1)),
    ('drawRect', lambda g: g.draw_rect(2, 2, 40, 20, 1)),
    ('fillRect', lambda g: g.fill_rect(2, 2, 40, 20, 1)),
    ('drawCircle', lambda g: g.draw_circle(30, 30, 15, 1)),
    ('fillCircle', lambda g: g.fill_circle(30, 30, 15, 1)),
    ('drawTriangle', lambda g: g.draw_triangle(0, 0, 20, 0, 10, 20, 1)),
    ('fillTriangle', lambda g: g.fill_triangle(0, 0, 20, 0, 10, 20, 1)),
    ('drawFastHLine', lambda g: g.draw_fast_hline(0, 10, 50, 1)),
    ('drawFastVLine', lambda g: g.draw_fast_vline(10, 0, 40, 1)),
    ('setTextSize', lambda g: g.set_text_size(1, 1)),
    ('setTextColor', lambda g: g.set_text_color(255, 255, 255)),
    ('setCursor', lambda g: g.set_cursor(0, 0)),
    ('setTextWrapOn', lambda g: g.set_text_wrap_on()),
    ('setTextWrapOff', lambda g: g.set_text_wrap_off()),
    ('home', lambda g: g.home()),
    ('print', lambda g: g.print('selftest')),
    ('clear', lambda g: g.clear()),
    ('setRotation', lambda g: g.set_rotation(config.SCREEN_ROTATION)),
    ('display', lambda g: g.display()),
]


def phase2_unattended(board: Board, results: Results) -> None:
    print('\n== Phase 2: unattended protocol conformance ==')
    gfx = board.gfx

    # Every client primitive must dispatch without an ERROR response.
    for name, call in PRIMITIVES:
        try:
            call(gfx)
            results.check(f'cmd:{name}', True)
        except Exception as e:
            results.check(f'cmd:{name}', False, str(e))

    # Queries return sane values.
    results.check('query:width', gfx.get_width() > 0)
    results.check('query:height', gfx.get_height() > 0)
    w, h = gfx.get_text_bounds(0, 0, 'Hi')
    results.check('query:getTextBounds', w > 0 and h > 0, f'{w}x{h}')

    # Short soak: cycle drawing, assert no comm errors / spurious reboots.
    print('  soak: drawing for 5s...')
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
    results.check('soak:no-comm-errors', errors == 0, f'{errors} errors')
    results.check('soak:no-spurious-reboot', board.boots == boots_before)


def main() -> None:
    unattended_only = '--unattended-only' in sys.argv
    board = connect()
    results = Results()
    if not unattended_only:
        phase1_gallery(board, results)
        phase1_buttons(board, results)
    phase2_unattended(board, results)
    results.summary()
    sys.exit(0 if results.ok else 1)


if __name__ == '__main__':
    main()
