from typing import Callable

import config
from .command import Command


class Gfx:
    def __init__(self, command: Command):
        self.command = command

    def _command(self, cmd: str, ignore_error: bool = False) -> str:
        return self.command.do_command(cmd, ignore_error)

    def reset(self) -> None:
        self._command('reset')

    def clear(self) -> None:
        self._command('clear')

    def set_text_size(self, w: float, h: float) -> None:
        w = int(config.TEXT_SCALING*w + .5)
        h = int(config.TEXT_SCALING*h + .5)
        self._command(f'setTextSize {w} {h}')

    def set_cursor(self, x: int, y: int) -> None:
        self._command(f'setCursor {x} {y}')

    def print(self, s: str) -> None:
        self._command(f'print {s}')

    def display(self) -> None:
        self._command('display')

    def get_text_bounds(self, x: int, y: int, text: str) -> tuple[int, int]:
        ans = self._command(f'getTextBounds 0 0 {text}')
        vals = [int(v) for v in ans.split()]
        w, h = vals[-2:]
        return w, h

    def fill_rect(self, x: int, y: int, w: int, h: int, fg: int) -> None:
        self._command(f'fillRect {x} {y} {w} {h} {fg}')

    def set_text_color(self, fg: int) -> None:
        self._command(f'setTextColor {fg}')

    def home(self) -> None:
        self._command('home')

    def draw_pixel(self,  x: int, y: int, fg: int) -> None:
        self._command(f'drawPixel {x} {y} {fg}')

    def draw_circle(self, x: int, y: int, r: int, fg: int) -> None:
        self._command(f'drawCircle {x} {y} {r} {fg}')

    def fill_circle(self, x: int, y: int, r: int, fg: int) -> None:
        self._command(f'fillCircle {x} {y} {r} {fg}')

    def draw_triangle(self, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, fg: int) -> None:
        self._command(f'drawTriangle {x0} {y0} {x1} {y1} {x2} {y2} {fg}')

    def fill_triangle(self, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, fg: int) -> None:
        self._command(f'fillTriangle {x0} {y0} {x1} {y1} {x2} {y2} {fg}')

    def set_text_wrap_on(self) -> None:
        self._command('setTextWrap 1')

    def set_text_wrap_off(self) -> None:
        self._command('setTextWrap 0')

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, fg: int) -> None:
        self._command(f'drawLine {x0} {y0} {x1} {y1} {fg}')

    def fill_screen(self, fg: int) -> None:
        self._command(f'fillScreen {fg}')

    def draw_fast_vline(self, x: int, y: int, h: int, fg: int) -> None:
        self._command(f'drawFastVLine {x} {y} {h} {fg}')

    def draw_fast_hline(self, x: int, y: int, w: int, fg: int) -> None:
        self._command(f'drawFastHLine {x} {y} {w} {fg}')

    def set_rotation(self, r: int) -> None:
        self._command(f'setRotation {r}')

    def set_auto_display_on(self) -> None:
        self._command('autoDisplay 1')

    def set_auto_display_off(self) -> None:
        self._command('autoDisplay 0')

    def get_width(self) -> int:
        return int(self._command(f'width'))

    def get_height(self) -> int:
        return int(self._command(f'height'))

    def read_buttons(self) -> str:
        return self._command('readButtons', ignore_error=True)

    def set_auto_read_buttons_on(self) -> None:
        self._command('autoReadButtons 1')

    def set_auto_read_buttons_off(self) -> None:
        self._command('autoReadButtons 0')

    def set_fg_color(self, r: int, g: int, b: int) -> None:
        self._command(f'setFgColor {r} {g} {b}')

    def set_bg_color(self, r: int, g: int, b: int) -> None:
        self._command(f'setBgColor {r} {g} {b}')
