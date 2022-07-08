#!/usr/bin/env python3
"""Program communicating with Arduino running oled-server.ino."""

import config
import contextlib
import datetime
import math
import os
import random
import serial  # pip3 install pyserial
import sys
import time
import traceback

from lib import *
from lib.args import get_args
from app import App
from app.asteriods import Asteriods
from app.monitor import Monitor
from app.cube import Cube

@contextlib.contextmanager
def until(timeout=None):
    start = datetime.datetime.now()
    until = timeout and start + datetime.timedelta(seconds=timeout)
    def done():
        if timeout is None:
            return False
        return datetime.datetime.now() >= until
    yield done


class Channel:
    def __init__(self,
                 port=config.SERIAL_PORT,
                 baudrate=config.SERIAL_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.on_message = self.on_fn = None

    def open(self):
        self.ser = serial.Serial(self.port, self.baudrate)
        self.clear()

    def clear(self):
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.flush_in()

    def set_callback(self, message, fn):
        self.on_message = message
        self.on_fn = fn

    def write(self, s):
        if config.DEBUG: print('<<<', s)
        self.ser.write(s.encode(ASCII) + b'\n')

    def read(self):
        try:
            bytes = self.ser.readline()
            message = bytes.decode(ASCII).strip()
        except Exception as e:
            print('>>>', bytes, ' ###', e)
            return f'ERROR {e}'
        if config.DEBUG: print(">>>", message)
        if message == self.on_message:
            self.on_fn(message)
        return message

    def flush_in(self):
        if config.DEBUG:
            print('>flush> ', end='')
        while True:
            if self.ser.inWaiting():
                c = self.ser.read()
                if config.DEBUG:
                    print(c, end='')
            else:
                time.sleep(0.1)
                if not self.ser.inWaiting():
                    if config.DEBUG:
                        print()
                    return

class Board:
    def __init__(self, channel):
        self.chan = channel
        self.configure_callback = None
        self.chan.open()
        self.chan.set_callback('READY', self.on_ready)
        self.configured = False
        self.boots = 0
        self.last_command = None
        self.reading_buttons = False
        self.auto_buttons = set()
        self.auto_buttons_boots = 0
        self.read_buttons_boots = 0

    def command_send(self, cmd):
        assert not self.reading_buttons
        self.chan.write(cmd)
        self.last_command = cmd

    def command_response(self):
        response = self.chan.read()
        if not config.DEBUG:
            if response.startswith(ERROR) or response.startswith(UNKNOWN):
                print('<<<', self.last_command)
                print('>>>', response)
        assert not response.startswith('ERROR')
        if response.startswith('OK '):
            b = response.split(' ', 1)[1].strip()
            if b != NONE:
                self.auto_buttons |= set(b)
        return response

    def command(self, cmd, ignore_error=False):
        self.command_send(cmd)
        try:
            return self.command_response()
        except:
            if ignore_error:
                return ''
            raise

    def on_ready(self, _=None):
        time.sleep(0.2)
        self.boots += 1
        self.configure()

    def set_configure_callback(self, configure_callback):
        self.configure_callback = configure_callback

    def configure(self):
        # normally called by callback
        time.sleep(0.2)
        self.chan.clear()
        self.command(f'setRotation {config.SCREEN_ROTATION}')
        self.command('autoDisplay 0')
        self.command('reset')

        w = int(self.command(f'width'))
        h = int(self.command(f'height'))
        if not config.WIDTH:
            config.WIDTH = w
            config.HEIGHT = h
            config.COLUMNS = int(w / 6.4)
            config.ROWS = int(h / 8)
            print(f'OLED resolution:')
            print(f'  pixels: {w} x {h}')
            print(f'  chars:  {config.COLUMNS} x {config.ROWS}')

        if self.configure_callback:
            self.configure_callback()
        self.configured = True

    def wait_configured(self):
        while True:
            if self.configured:
                return
            self.chan.read()
            time.sleep(0.5)

    def begin_read_buttons(self):
        assert not self.reading_buttons
        if config.DEBUG:
            print('* begin_read_buttons')
        self.command_send('waitButton -1 0')
        self.reading_buttons = True
        self.auto_buttons_boots = self.boots

    def end_read_buttons(self):
        assert self.reading_buttons
        if config.DEBUG:
            print('* end_read_buttons')
        self.reading_buttons = False
        self.command_send('width')
        resp = self.command_response()
        self.chan.flush_in()
        #self.command_response()  # TODO: with a timeout
        #self.chan.clear()
        if resp == NONE:
            val = set()
        else:
            val = set(resp)
        if self.boots > self.auto_buttons_boots:
            val.add('R')
        if config.DEBUG:
            print('* end_read_buttons done:', val)
        return val

    def wait_no_button(self, timeout=None):
        if timeout is None:
            while self.command('readButtons', ignore_error=True) != NONE:
                pass
        else:
            start = datetime.datetime.now()
            until = start + datetime.timedelta(seconds=timeout)
            while datetime.datetime.now() < until:
                if self.command('readButtons', ignore_error=True) != NONE:
                    break

    def begin_auto_read_buttons(self):
        self.command('autoReadButtons 1')
        if config.DEBUG:
            print('* begin_auto_read_buttons')
        self.auto_buttons = set()
        self.auto_buttons_boots = self.boots

    def auto_read_buttons(self):
        if self.boots > self.auto_buttons_boots:
            self.auto_buttons.add('R')
        b = self.auto_buttons
        self.auto_buttons = set()
        return b

    def end_auto_read_buttons(self):
        self.command('autoReadButtons 0')
        self.chan.flush_in()
        if config.DEBUG:
            print('* end_auto_read_buttons')
        if self.boots > self.auto_buttons_boots:
            self.auto_buttons.add('R')
        return self.auto_buttons

    def clear_buttons(self):
        self.chan.flush_in()
        self.read_buttons_boots = self.boots

    def wait_button_up(self, timeout=None):
        return self.wait_button(timeout, wait_released=True)

    def wait_button(self, timeout=None, wait_released=False):
        self.wait_no_button()
        b = set()
        with until(timeout) as done:
            while not done():
                b = self.read_buttons()
                if b: break
        if wait_released:
            while True:
                b2 = self.read_buttons()
                if not b2: break
                b |= b2
        return b

    def read_buttons(self, flush=False):
        if flush:
            self.chan.flush_in()
            self.read_buttons_boots = self.boots

        ans = self.command('readButtons', ignore_error=True)
        b = set()
        if ans != NONE:
            for c in ans:
                if c in 'ABC':
                    b.add(c)
                else:
                    b = set()
                    break
        if self.boots > self.read_buttons_boots:
            b.add('R')
            self.read_buttons_boots = self.boots
        return b

class Bumps(App):
    def __init__(self, board):
        super().__init__(board)
        sprites = [
            #Sprite(self, 4, -1, -1),
            Sprite(self, 7,  1 , 1),
            Sprite(self, 2,  1, -1),
            Sprite(self, 3, -1,  1),
            Sprite(self, 2, -1, -1),
        ]

        escaper = KeyEscaper(self, self.board, steady_message=False)
        while True:
            for s in sprites:
                s.erase()

            escaper.pre_check()

            for s in sprites:
                s.advance()

            if escaper.check(): break
            self.command('display')


class Quix(App):
    def __init__(self, board):
        super().__init__(board)

        a = Bouncer(self, 2, -1, -1)
        b = Bouncer(self, 2,  1 , 1)

        NB_LINES = 6
        REDRAW = False  # True looks cleaner but is slower

        history = [None] * NB_LINES
        i = 0

        escaper = KeyEscaper(self, self.board, steady_message=False)
        while True:
            a.advance()
            b.advance()

            history[i] = (a.x, a.y, b.x, b.y)
            i = (i+1) % NB_LINES
            last = history[i]
            if last:
                ax, ay, bx, by = last
                self.command(f'drawLine {ax} {ay} {bx} {by} 0')

            escaper.pre_check()

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

class Tunnel(App):
    def __init__(self, board):
        super().__init__(board)

        last = None
        escaper = KeyEscaper(self, self.board, steady_message=False)
        K = 0.65
        NB = 12
        NB2 = 6

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
#            self.command(f'drawLine {x0} {y0} {x1} {y1} {c}')
            self.command(f'drawLine {x1} {y1} {x2} {y2} {c}')
#            self.command(f'drawLine {x2} {y2} {x3} {y3} {c}')
            self.command(f'drawLine {x3} {y3} {x0} {y0} {c}')
#            self.command(f'drawRect {0} {0} {config.WIDTH} {config.HEIGHT} 1')

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

            escaper.pre_check()

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

class Starfield(App):
    def __init__(self, board):
        super().__init__(board)

        class Star:
            def __init__(self):
                self.reset(0)

            def reset(self, t):
                self.vx = random.random()-.5
                self.vy = random.random()-.5
                self.t0 = t
                self.k = random.random() + 1.75

            def compute(self, t, check=False):
                dt = t - self.t0
                x = int(self.vx * self.k**dt +.5 + config.WIDTH/2)
                y = int(self.vy * self.k**dt +.5 + config.HEIGHT/2)
                if check:
                    if x > config.WIDTH or x < 0 or y > config.HEIGHT or y < 0:
                        return None, None
                return x, y

        NB_STARS = 6
        stars = [Star() for i in range(NB_STARS)]

        t = 0
        escaper = KeyEscaper(self, self.board, steady_message=False)
        while True:
            # erase
            for star in stars:
                x0, y0 = star.compute(t)
                x1, y1 = star.compute(t+1)
                self.command(f'drawLine {x0} {y0} {x1} {y1} 0')

            escaper.pre_check()

            # draw
            for star in stars:
                x0, y0 = star.compute(t+1, True)
                x1, y1 = star.compute(t+2)
                if x0 is None:
                    star.reset(t)
                else:
                    self.command(f'drawLine {x0} {y0} {x1} {y1} 1')

            if escaper.check(): break
            self.command('display')
            t += 1


class Road(App):
    def __init__(self, board):
        super().__init__(board)

        last = None
        escaper = KeyEscaper(self, self.board, steady_message=False)
        K = 0.65
        NB = 12
        NB2 = 4
        NB3 = 8

        def draw(i, c):
            i = NB - (i%NB)
            w = config.WIDTH  * K**i *2
            h = config.HEIGHT * K**i *2
            x, y =  w/2,  h/2

            x0 = int(config.WIDTH/2 -w/2)
            x1 = int(config.WIDTH/2 +w/2)
            y = int(config.HEIGHT/2 -h/2)

            self.command(f'drawFastVLine {x0} {y} {h} {c}')
            self.command(f'drawFastVLine {x1} {y} {h} {c}')

        i = 0
        while True:
            draw(i, 0)
            draw(i + NB2, 0)
            draw(i + NB3, 0)

            escaper.pre_check()

            draw(i+1, 1)
            draw(i+1 + NB2, 1)
            draw(i+1 + NB3, 1)

            i += 1

            if escaper.check(): break
            self.command('display')


################################################################################
# Helper classes

class RebootedException(Exception):
    pass


class KeyEscaper:
    def __init__(self, app, board, message="Hold a key: next demo",
                 timeout=datetime.timedelta(seconds=60),
                 steady_message=True):
        self.app = app
        self.board = board
        self.message = message
        self.timeout = timeout
        self.steady_message = steady_message
        self.i = -30
        self.n = 0
        self.command = self.board.command
        self.boots = self.board.boots
        self.start = datetime.datetime.now()

    def pre_check(self):
        self.i += 1
        if not self.steady_message and self.i % 80 == 8:
            #self.command('reset')
            self.command(f'fillRect 0 0 {config.WIDTH} 8 0')

    def check(self):
        self.n += 1
        elapsed = datetime.datetime.now() - self.start
        if self.n == 30:
            secs = elapsed.seconds + elapsed.microseconds/1000000
            print(self.app.name, 'FPS:', 30 / secs)
        if self.timeout:
            if elapsed > self.timeout:
                return True
        if self.boots != self.board.boots:
            self.boots = self.board.boots
            raise RebootedException()
        if self.i % 10 == 1:
            if self.command('readButtons', ignore_error=True) != NONE:
                return True
        if self.i % 70 < 8:
            self.command('home')
            self.command(f'print {self.message}')
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


def chunkize(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]

def fatal(msg):
    print(msg)
    board.command('home')
    board.command('setTextSize 1')
    board.command('setTextWrap 1')
    board.command(f'fillRect 0, 0, {config.WIDTH} 8 0')
    board.command('reset')

    msg = ' '.join(msg.split())
    msg = msg[-20*8:]
    for chunk in chunkize(msg.replace('\n', ' '), 20):
        board.command(f'print {chunk}')
    board.command('display')
    sys.exit(1)


# Here it goes
args = get_args()

chan = Channel()
board = Board(chan)
board.wait_configured()
board.clear_buttons()

while True:
    try:
        while True:
            if not config.MONITOR_SKIP:
                Monitor(board)
            if config.MONITOR_ONLY:
                continue
            Asteriods(board)
            Cube(board)
            Road(board)
            Starfield(board)
            Tunnel(board)
            Quix(board)
            Bumps(board)
    except RebootedException:
        # restart loop
        pass
    except KeyboardInterrupt:
        print()
        fatal('Keyboard interrupt')
        raise
    except Exception as e:
        msg = traceback.format_exc()
        fatal(msg)
