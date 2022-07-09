import contextlib
import datetime
import random
import time

import config
from lib import *

class App:
    def __init__(self, board, auto_read, extra_configurator=None,
                 name=None):
        self.board = board
        self.name = name or self.__class__.__name__
        print(f'== {self.name} ==')
        self.board.set_comm_error_handler(self.init)
        self.auto_read = auto_read
        self.extra_configurator = extra_configurator
        board.set_configure_callback(extra_configurator)
        self.init()

    def run(self):
        if self.board.read_buttons(flush=True):
            return False

        start = datetime.datetime.now()
        reset = False
        if not self.board.wait_no_button(2):
            reset = self._run()
            if self.auto_read:
                reset = reset or 'R' in self.board.end_auto_read_buttons()
        self.board.set_comm_error_handler(self.init)
        self.board.set_configure_callback(None)
        duration = datetime.datetime.now() - start
        print('Duration:', duration)
        return reset

    def init(self):
        self.board.set_comm_error_handler(self.init)
        self.board.configure()
        assert config.WIDTH and config.HEIGHT
        self.command(f'setTextSize 1 2')
        title = self.name.upper()
        x, y = self.get_title_pos(title)

        # title
        self.command('reset')
        self.command(f'setCursor {x} {y}')
        self.command(f'print {title}')
        self.command('display')

        # ready for run()
        self.command('reset')
        self.command(f'setTextSize 1')
        self.board.clear_buttons()
        if self.auto_read:
            self.board.begin_auto_read_buttons()

    def command(self, cmd, **kw):
        delay = config.SERIAL_ERROR_RETRY_DELAY
        while True:
            try:
                return self.board.command(cmd, **kw)
            except ArduinoCommExceptions as e:
                print('Serial error:', e)
                self.board.close()
                while True:
                    print('-- will retry in', delay)
                    time.sleep(delay)
                    try:
                        self.board.reopen()
                        self.init()
                        print('Re-init OK.')
                        break
                    except Exception as e:
                        print('Error:', e)

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
    def __init__(self, app, timeout=-1):
        self.app = app
        if timeout == -1:
            timeout = config.APPS_TIMEOUT  # config is patched, so not in ctor
        if timeout is not None:
            timeout = datetime.timedelta(seconds=timeout)
        self.timeout = timeout
        self.frames = 0
        self.start = datetime.datetime.now()

    def check(self):
        self.frames += 1
        elapsed = datetime.datetime.now() - self.start
        nf = 30
        if self.frames == nf:
            secs = elapsed.seconds + elapsed.microseconds/1000000
            print(self.app.name, 'FPS:', nf / secs)
        if self.timeout:
            if elapsed > self.timeout:
                return True
        return False


class Bouncer:
    def __init__(self, size, vx, vy):
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
    def __init__(self, app, size, vx, vy):
        super().__init__(size, vx, vy)
        self.app = app
        self.was_filled = False

    def erase(self):
        if self.was_filled:
            self.app.command(f'fillCircle {self.x} {self.y} {self.size} 0')
        else:
            self.app.command(f'drawCircle {self.x} {self.y} {self.size} 0')

    def advance(self):
        super().advance()
        if self.bumped:
            self.app.command(f'fillCircle {self.x} {self.y} {self.size} 1')
        else:
            self.app.command(f'drawCircle {self.x} {self.y} {self.size} 1')
        self.was_filled = self.bumped
