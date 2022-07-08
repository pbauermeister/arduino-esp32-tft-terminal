from lib import *
import config
from app import App, TimeEscaper

K = 0.65
NB = 12
NB2 = 4
NB3 = 8


class Road(App):
    def __init__(self, board):
        super().__init__(board)
        if self.board.wait_no_button(2): return
        self.board.begin_auto_read_buttons()

    def run(self):
        last = None
        escaper = TimeEscaper(self)

        i = 0
        while True:
            if self.board.auto_read_buttons(): break

            self.draw(i, 0)
            self.draw(i + NB2, 0)
            self.draw(i + NB3, 0)

            self.draw(i+1, 1)
            self.draw(i+1 + NB2, 1)
            self.draw(i+1 + NB3, 1)

            if escaper.check(): break
            self.command('display')
            i += 1

        if 'R' in self.board.end_auto_read_buttons(): return True

    def draw(self, i, c):
        i = NB - (i%NB)
        w = config.WIDTH  * K**i *2
        h = config.HEIGHT * K**i *2
        x, y =  w/2,  h/2

        x0 = int(config.WIDTH/2 -w/2)
        x1 = int(config.WIDTH/2 +w/2)
        y = int(config.HEIGHT/2 -h/2)

        self.command(f'drawFastVLine {x0} {y} {h} {c}')
        self.command(f'drawFastVLine {x1} {y} {h} {c}')
