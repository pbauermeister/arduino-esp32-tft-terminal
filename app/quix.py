
import random
from dataclasses import dataclass

from app import App, Bouncer, TimeEscaper
from lib.board import Board

NB_LINES = 9
REDRAW = not False  # True looks cleaner but is slower


@dataclass
class Segment:
    ax: int
    ay: int
    bx: int
    by: int
    cx: int
    cy: int


@dataclass
class ColorComponent:
    value:     int
    speed:     int
    max_speed: int
    min:       int
    max:       int

    def advance(self) -> None:
        self.value += self.speed
        if self.value > self.max:
            self.value = self.max
            self.speed = -int(random.random()*(self.max_speed-1)+1)
        elif self.value < self.min:
            self.value = self.min
            self.speed = int(random.random()*(self.max_speed-1)+1)


@dataclass
class Color:
    r: ColorComponent
    g: ColorComponent
    b: ColorComponent

    def advance(self) -> tuple[int, int, int]:
        self.r.advance()
        self.g.advance()
        self.b.advance()
        return self.r.value, self. g.value, self. b.value


class Quix(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> bool:
        p1 = Bouncer(2, -1, -1)
        p2 = Bouncer(2, +1, +1)
        p3 = Bouncer(3, +1, -1)

        rgb = Color(
            ColorComponent(128, +15, 25, 64, 255),
            ColorComponent(128, -15, 25, 64, 255),
            ColorComponent(128, +25, 25, 64, 255),
        )

        history: list[Segment | None] = [None] * NB_LINES
        i = 0

        escaper = TimeEscaper(self)
        while True:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            p1.advance()
            p2.advance()
            p3.advance()
            history[i] = Segment(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)

            # erase
            i = (i+1) % NB_LINES
            last = history[i]
            if last is not None:
                self.gfx.draw_triangle(
                    last.ax, last.ay, last.bx, last.by, last.cx, last.cy, 0)

            # color
            r, g, b = rgb.advance()
            self.gfx.set_fg_color(r, g, b)

            # draw
            if REDRAW:
                for j in range(NB_LINES-1):
                    last = history[(i-1-j) % NB_LINES]
                    if last:
                        self.gfx.draw_triangle(
                            last.ax, last.ay, last.bx, last.by, last.cx, last.cy, 1)
            else:
                self.gfx.draw_triangle(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y, 1)

            self.gfx.display()
        return
