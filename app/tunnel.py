import math
import random

from lib import *
import config
from app import App, TimeEscaper

K = 0.65
NB = 12
NB2 = 6


class Tunnel(App):
    def __init__(self, board):
        super().__init__(board, auto_read=True)

    def _run(self):
        escaper = TimeEscaper(self)

        i = 0
        while True:
            if self.board.auto_read_buttons(): break
            j = i
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 0);

            j = i + NB2
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 0);

            j = i+1
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 1);

            j = i+1 + NB2
            w, h = self.make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = self.compute(w, h, j)
            self.draw(x0, y0, x1, y1, x2, y2, x3, y3, 1);

            if escaper.check(): break
            self.command('display')
            i += 1

        return

    def make(self, i):
        i = NB - 1 - (i%NB)
        w = config.WIDTH  * K**i *2
        h = config.HEIGHT * K**i *2

        return w, h

    def compute(self, w, h, t):
        a = math.sin(t/100)
        a = a*a
        cos, sin = math.cos(a), math.sin(a)

        x, y =  w/2,  h/2
        x, y = cos*x - sin*y, sin*x + cos*y
        x0 = int(config.WIDTH/2 + x)
        y0 = int(config.HEIGHT/2 + y)

        x, y =  w/2, -h/2
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

    def draw(self, x0, y0, x1, y1, x2, y2, x3, y3, c):
        #self.command(f'drawLine {x0} {y0} {x1} {y1} {c}')
        self.command(f'drawLine {x1} {y1} {x2} {y2} {c}')
        #self.command(f'drawLine {x2} {y2} {x3} {y3} {c}')
        self.command(f'drawLine {x3} {y3} {x0} {y0} {c}')
        #self.command(f'drawRect {0} {0} {config.WIDTH} {config.HEIGHT} 1')
