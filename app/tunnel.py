import math

import config
from app import App, TimeEscaper
from lib.board import Board

K = 0.65
NB = 12
NB2 = 6


class Tunnel(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> bool:
        escaper = TimeEscaper(self)

        i = 0
        while True:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            j = i
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 0)

            j = i + NB2
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 0)

            j = i+1
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 1)

            j = i+1 + NB2
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 1)

            self.gfx.display()
            i += 1

    def make(self, i: int) -> tuple[int, int]:
        i = NB - 1 - (i % NB)
        w = int(config.WIDTH * K**i * 2)
        h = int(config.HEIGHT * K**i * 2)
        return w, h

    def compute(self, w: int, h: int, t: int) -> tuple[int, int, int, int, int, int, int, int]:
        a = math.sin(t/100)
        a = a*a
        cos, sin = math.cos(a), math.sin(a)

        x, y = w/2,  h/2
        x, y = cos*x - sin*y, sin*x + cos*y
        x0 = int(config.WIDTH/2 + x)
        y0 = int(config.HEIGHT/2 + y)

        x, y = w/2, -h/2
        x, y = cos*x - sin*y, sin*x + cos*y
        x1 = int(config.WIDTH/2 + x)
        y1 = int(config.HEIGHT/2 + y)

        x, y = -w/2, -h/2
        x, y = cos*x - sin*y, sin*x + cos*y
        x2 = int(config.WIDTH/2 + x)
        y2 = int(config.HEIGHT/2 + y)

        x, y = -w/2,  h/2
        x, y = cos*x - sin*y, sin*x + cos*y
        x3 = int(config.WIDTH/2 + x)
        y3 = int(config.HEIGHT/2 + y)

        return x0, y0, x1, y1, x2, y2, x3, y3

    def draw(self, x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, c: int) -> None:
        self.gfx.draw_line(x1, y1, x2, y2, c)
        self.gfx.draw_line(x3, y3, x0, y0, c)

        # self.command(f'drawRect {0} {0} {config.WIDTH} {config.HEIGHT} 1')
