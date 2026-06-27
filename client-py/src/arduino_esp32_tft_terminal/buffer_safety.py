"""On-board demo for the print/buffer total-safety task (devlog 0052).

Two demonstrations, run on the gadget (`make test-board-buffer`):

A. **Slicing** — print a string far longer than the board's per-action `str`
   capacity; the client slices it into multiple `print` calls so it renders in
   full instead of being truncated.
B. **Flow control** — queue far more buffered draws than the action FIFO holds
   (`ACTIONS_COUNT=1000`) without a `display`. The firmware auto-commits when
   full and keeps going; the command that triggers the flush returns only after
   the draw completes, so the client is back-pressured (visible as a latency
   spike near each multiple of 1000). Every shape is drawn — none dropped.

Connect cleanly first: reset the board (boot logo), then run this.
"""

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


def demo_flow_control(board: Board, n: int = 1500) -> None:
    g = board.gfx
    w, h = config.WIDTH, config.HEIGHT
    print(f'\n=== B. {n} buffered draws, no display (FIFO=1000) ===')
    g.reset()
    g.fill_screen(0)
    g.set_fg_color(0, 255, 0)
    latencies: list[tuple[int, float]] = []
    for i in range(n):
        x, y = (i * 7) % (w - 8), (i * 11) % (h - 6)
        t0 = time.time()
        g.draw_rect(x, y, 8, 6, 1)  # buffered (auto-display off)
        latencies.append((i, time.time() - t0))
    g.display()  # flush the remainder
    latencies.sort(key=lambda p: -p[1])
    print('  slowest commands (auto-commit flushes = back-pressure):')
    for i, dt in latencies[:5]:
        print(f'    draw #{i}: {dt * 1000:.0f} ms')
    print('  -> spikes near multiples of 1000 are the firmware auto-committing;')
    print('     the client waited for the response. All shapes drew, none dropped.')


def main() -> None:
    board = _connect()
    demo_slicing(board)
    time.sleep(3)
    demo_flow_control(board)
    board.chan.close()
    print('\nbuffer-safety demo complete.')


if __name__ == '__main__':
    main()
