import math
import random
from dataclasses import dataclass

import config
from app import App, Bouncer, TimeEscaper
from lib import *
from lib.board import Board

NB_LINES = 8
REDRAW = False  # True looks cleaner but is slower


@dataclass
class Segment:
    ax: int
    ay: int
    bx: int
    by: int


class Quix(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> None:
        a = Bouncer(2, -1, -1)
        b = Bouncer(2,  1, 1)

        history: list[Segment | None] = [None] * NB_LINES
        i = 0

        escaper = TimeEscaper(self)
        while True:
            if self.board.auto_read_buttons():
                break

            a.advance()
            b.advance()

            history[i] = Segment(a.x, a.y, b.x, b.y)
            i = (i+1) % NB_LINES
            last = history[i]
            if last is not None:
                self.gfx.draw_line(last.ax, last.ay, last.bx, last.by, 0)

            if REDRAW:
                for j in range(NB_LINES-1):
                    last = history[(i-1-j) % NB_LINES]
                    if last:
                        self.gfx.draw_line(
                            last.ax, last.ay, last.bx, last.by, 1)
            else:
                self.gfx.draw_line(a.x, a.y, b.x, b.y, 1)

            if escaper.check():
                break
            self.gfx.display()

        return
