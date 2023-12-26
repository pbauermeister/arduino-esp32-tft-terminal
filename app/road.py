import config
from app import App, TimeEscaper
from lib import *
from lib.board import Board

K = 0.65
NB = 12
NB2 = 4
NB3 = 8


class Road(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> None:
        last = None
        escaper = TimeEscaper(self)

        i = 0
        while True:
            if self.board.auto_read_buttons():
                break

            self.draw(i, 0)
            self.draw(i + NB2, 0)
            self.draw(i + NB3, 0)

            self.draw(i+1, 1)
            self.draw(i+1 + NB2, 1)
            self.draw(i+1 + NB3, 1)

            if escaper.check():
                break
            self.command('display')
            i += 1

        return

    def draw(self, i: int, c: int) -> None:
        i = NB - (i % NB)
        w = config.WIDTH * K**i * 2
        h = config.HEIGHT * K**i * 2
        x, y = w/2,  h/2

        x0 = int(config.WIDTH/2 - w/2)
        x1 = int(config.WIDTH/2 + w/2)
        y = int(config.HEIGHT/2 - h/2)

        self.command(f'drawFastVLine {x0} {y} {h} {c}')
        self.command(f'drawFastVLine {x1} {y} {h} {c}')
