# AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
# Regenerate with: make protocol-gen
"""Typed protocol command layer — one method per command.

Generated from protocol.yaml. Each method assembles the wire command and
parses the typed response, then defers to `Command.do_command`. App
conveniences (text scaling, print slicing, HSV, recovery handling) live in
the hand-written Gfx facade, not here.
"""

from __future__ import annotations

from .command import Command


class ProtocolCommands:
    def __init__(self, command: Command) -> None:
        self._command = command

    def reboot(self) -> None:
        """Reboot the board; sends no response, so the client must not wait."""
        self._command.do_command('reboot', ignore_response=True)

    def reset(self) -> None:
        """Reset display state and clear the pending action buffer."""
        self._command.do_command('reset')

    def display(self) -> None:
        """Flush the buffered draw actions to the screen."""
        self._command.do_command('display')

    def auto_display(self, on: bool) -> None:
        """If on=1 draw commands render immediately; if 0 they buffer until `display`."""
        self._command.do_command(f'autoDisplay {int(on)}')

    def auto_read_buttons(self, on: bool) -> None:
        """If on=1, every OK response carries the current button-state suffix."""
        self._command.do_command(f'autoReadButtons {int(on)}')

    def version(self) -> str:
        """Firmware version string."""
        return self._command.do_command('version')

    def width(self) -> int:
        """Display width in pixels."""
        return int(self._command.do_command('width'))

    def height(self) -> int:
        """Display height in pixels."""
        return int(self._command.do_command('height'))

    def get_print_max_length(self) -> int:
        """Maximum unescaped text length storable by one buffered `print`."""
        return int(self._command.do_command('getPrintMaxLength'))

    def get_rotation(self) -> int:
        """Current display rotation (0-3)."""
        return int(self._command.do_command('getRotation'))

    def get_cursor_x(self) -> int:
        """Current text-cursor X coordinate."""
        return int(self._command.do_command('getCursorX'))

    def get_cursor_y(self) -> int:
        """Current text-cursor Y coordinate."""
        return int(self._command.do_command('getCursorY'))

    def get_text_bounds(self, x: int, y: int, text: str) -> tuple[int, int, int, int]:
        """Pixel bounding box (x1,y1,w,h) of `text` rendered at (x,y)."""
        _ans = self._command.do_command(f'getTextBounds {x} {y} {text}')
        _parts = _ans.split()
        return (
            int(_parts[0]),
            int(_parts[1]),
            int(_parts[2]),
            int(_parts[3]),
        )  # x1 y1 w h

    def print(self, text: str) -> None:
        """Print text at the cursor; supports \\n, \\t and \\\\ escapes."""
        self._command.do_command(f'print {text}')

    def clear_display(self) -> None:
        """Clear the screen to the background colour."""
        self._command.do_command('clearDisplay')

    def clear(self) -> None:
        """Clear the screen to the background colour (alias of clearDisplay)."""
        self._command.do_command('clear')

    def home(self) -> None:
        """Move the text cursor to (0,0)."""
        self._command.do_command('home')

    def set_fg_color(self, r: int, g: int, b: int) -> None:
        """Set the foreground (palette index 1) colour from RGB 0-255."""
        self._command.do_command(f'setFgColor {r} {g} {b}')

    def set_bg_color(self, r: int, g: int, b: int) -> None:
        """Set the background (palette index 0) colour from RGB 0-255."""
        self._command.do_command(f'setBgColor {r} {g} {b}')

    def draw_pixel(self, x: int, y: int, color: int) -> None:
        """Plot a pixel at (x,y) in palette `color`."""
        self._command.do_command(f'drawPixel {x} {y} {color}')

    def set_rotation(self, m: int) -> None:
        """Set display rotation (0-3, in 90 degree steps)."""
        self._command.do_command(f'setRotation {m}')

    def invert_display(self, inv: bool = True) -> None:
        """Invert display colours; inv defaults to 1 (on)."""
        self._command.do_command(f'invertDisplay {int(inv)}')

    def draw_fast_v_line(self, x: int, y: int, h: int, color: int) -> None:
        """Vertical line from (x,y), height h, in palette `color`."""
        self._command.do_command(f'drawFastVLine {x} {y} {h} {color}')

    def draw_fast_h_line(self, x: int, y: int, w: int, color: int) -> None:
        """Horizontal line from (x,y), width w, in palette `color`."""
        self._command.do_command(f'drawFastHLine {x} {y} {w} {color}')

    def fill_screen(self, color: int) -> None:
        """Fill the whole screen with palette `color`."""
        self._command.do_command(f'fillScreen {color}')

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        """Line from (x0,y0) to (x1,y1) in palette `color`."""
        self._command.do_command(f'drawLine {x0} {y0} {x1} {y1} {color}')

    def draw_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        """Outline rectangle at (x,y), size w x h, in palette `color`."""
        self._command.do_command(f'drawRect {x} {y} {w} {h} {color}')

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int) -> None:
        """Filled rectangle at (x,y), size w x h, in palette `color`."""
        self._command.do_command(f'fillRect {x} {y} {w} {h} {color}')

    def draw_circle(self, x: int, y: int, r: int, color: int) -> None:
        """Outline circle centred (x,y), radius r, in palette `color`."""
        self._command.do_command(f'drawCircle {x} {y} {r} {color}')

    def fill_circle(self, x: int, y: int, r: int, color: int) -> None:
        """Filled circle centred (x,y), radius r, in palette `color`."""
        self._command.do_command(f'fillCircle {x} {y} {r} {color}')

    def draw_triangle(
        self, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, color: int
    ) -> None:
        """Outline triangle through the three vertices, in palette `color`."""
        self._command.do_command(f'drawTriangle {x0} {y0} {x1} {y1} {x2} {y2} {color}')

    def fill_triangle(
        self, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, color: int
    ) -> None:
        """Filled triangle through the three vertices, in palette `color`."""
        self._command.do_command(f'fillTriangle {x0} {y0} {x1} {y1} {x2} {y2} {color}')

    def draw_round_rect(
        self, x: int, y: int, w: int, h: int, r: int, color: int
    ) -> None:
        """Outline rounded rectangle, corner radius r, in palette `color`."""
        self._command.do_command(f'drawRoundRect {x} {y} {w} {h} {r} {color}')

    def fill_round_rect(
        self, x: int, y: int, w: int, h: int, r: int, color: int
    ) -> None:
        """Filled rounded rectangle, corner radius r, in palette `color`."""
        self._command.do_command(f'fillRoundRect {x} {y} {w} {h} {r} {color}')

    def draw_char(self, x: int, y: int, c: int, fg: bool, bg: bool, size: int) -> None:
        """Draw character code c at (x,y) with fg/bg flags and magnification `size`."""
        self._command.do_command(f'drawChar {x} {y} {c} {int(fg)} {int(bg)} {size}')

    def set_text_size(self, sx: int, sy: int = -1) -> None:
        """Set text magnification; omit sy (default -1) for square."""
        self._command.do_command(f'setTextSize {sx} {sy}')

    def set_cursor(self, x: int, y: int) -> None:
        """Move the text cursor to (x,y)."""
        self._command.do_command(f'setCursor {x} {y}')

    def set_text_color(self, r: int, g: int, b: int) -> None:
        """Set text colour from RGB 0-255."""
        self._command.do_command(f'setTextColor {r} {g} {b}')

    def set_text_wrap(self, w: bool) -> None:
        """Enable (1) or disable (0) automatic text wrapping at the screen edge."""
        self._command.do_command(f'setTextWrap {int(w)}')

    def read_buttons(self) -> str:
        """Currently pressed buttons, e.g. "A", "AB", or "NONE"."""
        return self._command.do_command('readButtons')

    def wait_button(self, during: int, up: int) -> str:
        """Block up to `during` ms for a button event; up=1 waits for release, 0 for press."""
        return self._command.do_command(f'waitButton {during} {up}')

    def monitor_buttons(self, during: int, interval: int = 100) -> None:
        """Stream button states for `during` ms every `interval` ms (default 100), then OK."""
        self._command.do_command(f'monitorButtons {during} {interval}')

    def watch_buttons(self, during: int = 0, interval: int = 100) -> None:
        """Report button changes for `during` ms (0 = until reset) every `interval` ms; no terminating response."""
        self._command.do_command(
            f'watchButtons {during} {interval}', ignore_response=True
        )

    def test(self) -> str:
        """Run the built-in display diagnostic."""
        return self._command.do_command('test')

    def hardcopy(self) -> str:
        """Screen capture (not implemented; returns an error)."""
        return self._command.do_command('hardcopy')
