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
        super().__init__(board)

        last = None
        escaper = TimeEscaper(self)

        def make(i):
            i = NB - 1 - (i%NB)
            w = config.WIDTH  * K**i *2
            h = config.HEIGHT * K**i *2

            return w, h

        def compute(w, h, t):
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

        def draw(x0, y0, x1, y1, x2, y2, x3, y3, c):
            #self.command(f'drawLine {x0} {y0} {x1} {y1} {c}')
            self.command(f'drawLine {x1} {y1} {x2} {y2} {c}')
            #self.command(f'drawLine {x2} {y2} {x3} {y3} {c}')
            self.command(f'drawLine {x3} {y3} {x0} {y0} {c}')
            #self.command(f'drawRect {0} {0} {config.WIDTH} {config.HEIGHT} 1')

        i = 0
        while True:
            j = i
            w, h = make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = compute(w, h, j)
            draw(x0, y0, x1, y1, x2, y2, x3, y3, 0);

            j = i + NB2
            w, h = make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = compute(w, h, j)
            draw(x0, y0, x1, y1, x2, y2, x3, y3, 0);

            j = i+1
            w, h = make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = compute(w, h, j)
            draw(x0, y0, x1, y1, x2, y2, x3, y3, 1);

            j = i+1 + NB2
            w, h = make(j)
            x0, y0, x1, y1, x2, y2, x3, y3 = compute(w, h, j)
            draw(x0, y0, x1, y1, x2, y2, x3, y3, 1);

            i += 1

            if escaper.check(): break
            self.command('display')
