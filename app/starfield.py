import random

import config
from app import App, TimeEscaper
from lib import *
from lib.board import Board


class Star:
    def __init__(self) -> None:
        self.reset(0)

    def reset(self, t: int) -> None:
        self.vx = random.random()-.5
        self.vy = random.random()-.5
        self.t0 = t
        self.k = random.random() + 1.75

    def compute(self, t: int, check: bool = False) -> tuple[int, int]:
        dt = t - self.t0
        x = int(self.vx * self.k**dt + .5 + config.WIDTH/2)
        y = int(self.vy * self.k**dt + .5 + config.HEIGHT/2)
        if check:
            if x > config.WIDTH or x < 0 or y > config.HEIGHT or y < 0:
                return None, None
        return x, y


class Starfield(App):
    NB_STARS = 6

    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> None:
        stars = [Star() for i in range(self.NB_STARS)]
        t = 0
        escaper = TimeEscaper(self)
        while True:
            if self.board.auto_read_buttons():
                break

            # erase
            for star in stars:
                x0, y0 = star.compute(t)
                x1, y1 = star.compute(t+1)
                self.command(f'drawLine {x0} {y0} {x1} {y1} 0')

            # draw
            for star in stars:
                x0, y0 = star.compute(t+1, True)
                x1, y1 = star.compute(t+2)
                if x0 is None:
                    star.reset(t)
                else:
                    self.command(f'drawLine {x0} {y0} {x1} {y1} 1')

            if escaper.check():
                break
            self.command('display')
            t += 1

        return
