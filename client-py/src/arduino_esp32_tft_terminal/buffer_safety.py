"""On-board demo for the print/buffer total-safety task (devlog 0052).

Two demonstrations, run on the gadget (`make test-board-buffer`):

A. **Slicing** — print a string far longer than the board's per-action `str`
   capacity; the client slices it into multiple `print` calls so it renders in
   full instead of being truncated.
B. **Flow control (gradient)** — paint a full-screen rainbow pixel by pixel
   (`setFgColor` + `drawPixel` per pixel, on a white background), far more
   buffered actions than the FIFO holds (`ACTIONS_COUNT=1000`). The firmware
   auto-commits when full, so the image fills in bands. The correctness oracle
   is the **picture**: a smooth rainbow with no white specks or hue jumps means
   no action was lost. Response times are reported only to *confirm* that flow
   control happens (latency spikes at the flushes) — never to count commits, as
   a board may be fast, cache, or commit differently.

Connect cleanly first: reset the board (boot logo), then run this.
"""

import colorsys
import time

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.lib import READY
from arduino_esp32_tft_terminal.lib.board import Board
from arduino_esp32_tft_terminal.lib.channel import Channel


def _connect() -> Board:
    """Hardened connect: no READY->configure->reboot, retry until responsive."""
    board = Board(Channel())
    board.chan.set_callback(READY, None)
    g = board.gfx
    for _ in range(40):
        try:
            int(g._command('width'))
            break
        except Exception:
            time.sleep(0.4)
    g.set_rotation(config.SCREEN_ROTATION)
    g.set_auto_display_off()  # buffer draws until display()
    g.reset()
    config.WIDTH = g.get_width()
    config.HEIGHT = g.get_height()
    try:
        g.print_max = g.get_print_max_length()
    except Exception:
        pass  # older firmware: keep the default
    return board


def demo_slicing(board: Board) -> None:
    g = board.gfx
    text = ('The quick brown fox jumps over the lazy dog. ' * 12)[:400]
    n_chunks = -(-len(text) // g.print_max)  # ceil
    print(f'\n=== A. gigantic print (print_max={g.print_max}) ===')
    print(f'  printing {len(text)} chars -> client slices into ~{n_chunks} calls')
    g.reset()
    g.fill_screen(0)
    g.set_text_color(255, 255, 255)
    g.set_text_size(1, 1)
    g.set_text_wrap_on()
    g.home()
    g.print(text)
    g.display()
    print('  -> TFT should show the FULL text (wrapped), not truncated.')


def demo_gradient(board: Board, step: int = 1) -> None:
    g = board.gfx
    w, h = config.WIDTH, config.HEIGHT
    nx, ny = len(range(0, w, step)), len(range(0, h, step))
    total = nx * ny
    print(f'\n=== B. rainbow gradient, pixel by pixel ({total} px, step={step}) ===')
    print('  ~2 buffered actions/pixel; fills in bands as the FIFO auto-commits.')
    g.reset()
    g.set_fg_color(255, 255, 255)
    g.fill_screen(1)  # white: a lost pixel shows as a white speck on the rainbow
    latencies: list[tuple[int, float]] = []
    idx = 0
    for yy in range(0, h, step):
        for xx in range(0, w, step):
            r, gn, b = colorsys.hsv_to_rgb(idx / total, 1.0, 1.0)
            t0 = time.time()
            g.set_fg_color(int(r * 255), int(gn * 255), int(b * 255))
            if step == 1:
                g.draw_pixel(xx, yy, 1)
            else:
                g.fill_rect(xx, yy, step, step, 1)
            latencies.append((idx, time.time() - t0))
            idx += 1
    g.display()
    # Final centered black "OK" marker -> the demo completed.
    g.set_text_size(3, 3)
    tw, th = g.get_text_bounds(0, 0, 'OK')
    g.set_text_color(0, 0, 0)
    g.set_cursor((w - tw) // 2, (h - th) // 2)
    g.print('OK')
    g.display()
    latencies.sort(key=lambda p: -p[1])
    print('  slowest pixels (auto-commit flushes = back-pressure):')
    for i, dt in latencies[:6]:
        print(f'    pixel #{i}: {dt * 1000:.0f} ms')
    print('  -> CORRECTNESS = the picture: a smooth rainbow with NO white specks')
    print('     or hue jumps means every action survived (none dropped).')
    print('  -> timing only CONFIRMS flow control happens; it is not a commit')
    print('     counter (a board may be fast / cache / commit differently).')


def main() -> None:
    board = _connect()
    demo_slicing(board)
    time.sleep(3)
    demo_gradient(board)
    board.chan.close()
    print('\nbuffer-safety demo complete.')


if __name__ == '__main__':
    main()
