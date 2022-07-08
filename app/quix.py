import math
import random

from lib import *
import config
from app import App, TimeEscaper, Bouncer

NB_LINES = 8
REDRAW = False  # True looks cleaner but is slower


class Quix(App):
    def __init__(self, board):
        super().__init__(board)

        a = Bouncer(self, 2, -1, -1)
        b = Bouncer(self, 2,  1 , 1)

        history = [None] * NB_LINES
        i = 0

        escaper = TimeEscaper(self)
        while True:
            a.advance()
            b.advance()

            history[i] = (a.x, a.y, b.x, b.y)
            i = (i+1) % NB_LINES
            last = history[i]
            if last:
                ax, ay, bx, by = last
                self.command(f'drawLine {ax} {ay} {bx} {by} 0')

            if REDRAW:
                for j in range(NB_LINES-1):
                    last = history[(i-1-j) % NB_LINES]
                    if last:
                        ax, ay, bx, by = last
                        self.command(f'drawLine {ax} {ay} {bx} {by} 1')
            else:
                self.command(f'drawLine {a.x} {a.y} {b.x} {b.y} 1')

            if escaper.check(): break
            self.command('display')
