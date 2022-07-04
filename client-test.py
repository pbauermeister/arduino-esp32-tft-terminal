#!/usr/bin/env python3
"""Demo program communicating with Arduino running oled-server.ino."""

import serial  # pip3 install pyserial
import sys
import config
import time
import random
import math
import datetime

READY = 'READY'
ASCII = 'ASCII'
OK = 'OK'
NONE = 'NONE'
ERROR = 'ERROR'
UNKNOWN = 'UNKNOWN'

class Channel:
    def __init__(self, port=config.SERIALPORT, baudrate=config.BAUDRATE):
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

    def set_callback(self, message, fn):
        self.on_message = message
        self.on_fn = fn

    def write(self, s):
        if config.DEBUG: print('<<<', s)
        self.ser.write(s.encode(ASCII) + b'\n')

    def read(self):
        message = self.ser.readline().strip().decode(ASCII)
        if config.DEBUG: print(">>>", message)
        if message == self.on_message:
            self.on_fn(message)
        return message


class Board:
    def __init__(self, channel):
        self.chan = channel
        self.chan.open()
        self.chan.set_callback('READY', self.configure)
        self.configured = False
        self.boots = 0

    def command(self, cmd):
        self.chan.write(cmd)
        response = self.chan.read()
        if not config.DEBUG:
            if response.startswith(ERROR) or response.startswith(UNKNOWN):
                print('<<<', cmd)
                print('>>>', response)
        return response

    def configure(self, _):
        # normally called by callback
        time.sleep(0.2)
        self.chan.clear()
        self.command(f'setRotation {config.ROTATION}')
        self.command('autoDisplay 0')
        self.command('reset')
        config.WIDTH = int(self.command(f'width'))
        config.HEIGHT = int(self.command(f'height'))
        self.configured = True
        self.boots += 1

    def wait_configured(self):
        while True:
            if self.configured:
                return
            self.chan.read()
            time.sleep(0.5)

    def title(self, txt):
        assert config.WIDTH and config.HEIGHT
        self.command(f'setTextSize 1 2')
        ans = self.command(f'getTextBounds 0 0 {txt}')
        vals = [int(v) for v in ans.split()]
        w, h = vals[-2:]
        x = int(config.WIDTH/2 - w/2 +.5)
        y = int(config.HEIGHT/2 - h/2 +.5)
        self.command('reset')
        self.command(f'setCursor {x} {y}')
        self.command(f'print {txt}')
        self.command('display')

        self.command('readButtons')
        time.sleep(0.5)
        if self.command('readButtons') == NONE:
            time.sleep(0.5)

        self.command('reset')
        self.command(f'setTextSize 1')

    def bumps(self):
        self.title('BUMPS')
        sprites = [
            #Sprite(self, 4, -1, -1),
            Sprite(self, 7,  1 , 1),
            Sprite(self, 2,  1, -1),
            Sprite(self, 3, -1,  1),
            Sprite(self, 2, -1, -1),
        ]

        escaper = KeyEscaper(self, steady_message=False)
        while True:
            for s in sprites:
                s.erase()

            escaper.pre_check()

            for s in sprites:
                s.advance()

            if escaper.check():
                break

            self.command('display')
            #time.sleep(0.06)

    def quix(self):
        self.title('QUIX')
        a = Bouncer(self, 2, -1, -1)
        b = Bouncer(self, 2,  1 , 1)

        NB_LINES = 6
        REDRAW = False  # True looks cleaner but is slower

        history = [None] * NB_LINES
        i = 0

        escaper = KeyEscaper(self, steady_message=False)
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

            if escaper.check():
                break

            self.command('display')

    def tunnel(self):
        self.title('TUNNEL')
        last = None
        escaper = KeyEscaper(self, steady_message=False)
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
            self.command(f'drawLine {x0} {y0} {x1} {y1} {c}')
#            self.command(f'drawLine {x1} {y1} {x2} {y2} {c}')
            self.command(f'drawLine {x2} {y2} {x3} {y3} {c}')
#            self.command(f'drawLine {x3} {y3} {x0} {y0} {c}')
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

            if escaper.check():
                break

            self.command('display')

    def starfield(self):
        self.title('STAR FIELD')

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
        escaper = KeyEscaper(self, steady_message=False)
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

            if escaper.check():
                break

            self.command('display')
            t += 1

    def road(self):
        self.title('ROAD')
        last = None
        escaper = KeyEscaper(self, steady_message=False)
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

            if escaper.check():
                break

            self.command('display')


class KeyEscaper:
    def __init__(self, board, message="Hold a key to move on",
                 timeout=datetime.timedelta(seconds=60),
                 steady_message=True):
        self.board = board
        self.message = message
        self.timeout = timeout
        self.steady_message = steady_message
        self.i = -20
        self.command = self.board.command
        self.boots = self.board.boots
        self.start = datetime.datetime.now()

    def pre_check(self):
        self.i += 1
        if not self.steady_message and self.i % 80 == 8:
            #self.command('reset')
            self.command(f'fillRect 0 0 {config.WIDTH} 8 0')

    def check(self):
        if self.timeout:
            elapsed = datetime.datetime.now() - self.start
            if elapsed > self.timeout:
                return True
        if self.boots != self.board.boots:
            return True
        if self.i % 10 == 1:
            if self.command('readButtons') != NONE:
                return True
        if self.i % 80 < 8:
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


# Here it goes
chan = Channel()
board = Board(chan)
board.wait_configured()
#board.monitor()
while True:
    board.road()
    board.tunnel()
    board.starfield()
    board.quix()
    board.bumps()
