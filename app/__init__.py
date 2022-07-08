import datetime
import random
import time

import config
from lib import *

class App:
    def __init__(self, board):
        self.board = board
        self.command = board.command
        self.name = self.__class__.__name__

        self.board.configure()
        assert config.WIDTH and config.HEIGHT
        self.command(f'setTextSize 1 2')
        title = self.name.upper()
        x, y = self.get_title_pos(title)
        self.command('reset')
        self.command(f'setCursor {x} {y}')
        self.command(f'print {title}')
        self.command('display')

        self.command('readButtons')
        time.sleep(0.5)
        if self.command('readButtons') == NONE:
            time.sleep(0.5)

        self.command('reset')
        self.command(f'setTextSize 1')

    def get_title_pos(self, title):
        w, h = self.get_text_size(title)
        x = int(config.WIDTH/2 - w/2 +.5)
        y = int(config.HEIGHT/2 - h/2 +.5)
        return x, y

    def get_text_size(self, text):
        ans = self.command(f'getTextBounds 0 0 {text}')
        vals = [int(v) for v in ans.split()]
        w, h = vals[-2:]
        return w, h

    def show_header(self, title, menu, with_banner=False):
        self.command(f'reset')
        self.command(f'setTextSize 1 1')
        self.command(f'fillRect 0 0 {config.WIDTH} 8 1')
        self.command(f'setTextColor 0')
        self.command(f'setCursor 1 0')
        self.command(f'print {title}')
        w, h = self.get_text_size(menu)
        x = config.WIDTH - w - 3
        self.command(f'setCursor {x} 0')
        self.command(f'print {menu}')
        self.command(f'setTextColor 1')

        if with_banner:
            self.command(f'setTextSize 1 2')
            self.show_title(title)
            self.command(f'display')
            self.command(f'setTextSize 1 1')
        else:
            self.command(f'home')
            self.command(f'print \\n')

    def show_title(self, title):
        x, y = self.get_title_pos(title)
        self.command(f'setCursor {x} {y}')
        self.command(f'print {title}')


class TimeEscaper:
    def __init__(self, app, timeout=60):
        self.app = app
        self.timeout = None if timeout is None \
                       else datetime.timedelta(seconds=timeout)
        self.n = 0
        self.start = datetime.datetime.now()

    def check(self):
        self.n += 1
        elapsed = datetime.datetime.now() - self.start
        if self.n == 30:
            secs = elapsed.seconds + elapsed.microseconds/1000000
            print(self.app.name, 'FPS:', 30 / secs)
        if self.timeout:
            if elapsed > self.timeout:
                return True
        return False


class Bouncer:
    def __init__(self, board, size, vx, vy):
        self.board = board
        self.size = size
        k = .5
        v = (4 + 7**1.25 - size**1.25) * k
        self.xx = size if vx > 0 else config.WIDTH-size
        self.yy = size if vy > 0 else config.HEIGHT-size

        self.x, self.y = int(self.xx +.5), int(self.yy +.5)

        self.vx, self.vy = vx*v, vy*v
        self.vx0, self.vy0 = abs(vx*v), abs(vy*v)

        self.bumped = False

    @staticmethod
    def bump(v, v0):
        nv = (1 + (random.random()-.5)/2)*v0
        return nv if v < 0 else -nv

    def advance(self):
        self.bumped = False
        self.xx += self.vx
        self.yy += self.vy
        if self.xx >= config.WIDTH - self.size:
            self.xx = config.WIDTH - self.size - 1
            self.vx = self.bump(self.vx, self.vx0)
            self.bumped = True
        elif self.xx < self.size:
            self.xx = self.size
            self.vx = self.bump(self.vx, self.vx0)
            self.bumped = True
        if self.yy >= config.HEIGHT - self.size:
            self.yy = config.HEIGHT - self.size - 1
            self.vy = self.bump(self.vy, self.vy0)
            self.bumped = True
        elif self.yy < self.size:
            self.yy = self.size
            self.vy = self.bump(self.vy, self.vy0)
            self.bumped = True
        self.x, self.y = int(self.xx +.5), int(self.yy +.5)


class Sprite(Bouncer):
    def __init__(self, board, size, vx, vy):
        super().__init__(board, size, vx, vy)
        self.was_filled = False

    def erase(self):
        if self.was_filled:
            self.board.command(f'fillCircle {self.x} {self.y} {self.size} 0')
        else:
            self.board.command(f'drawCircle {self.x} {self.y} {self.size} 0')

    def advance(self):
        super().advance()
        if self.bumped:
            self.board.command(f'fillCircle {self.x} {self.y} {self.size} 1')
        else:
            self.board.command(f'drawCircle {self.x} {self.y} {self.size} 1')
        self.was_filled = self.bumped
