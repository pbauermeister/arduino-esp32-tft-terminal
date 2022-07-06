#!/usr/bin/env python3
"""Demo program communicating with Arduino running oled-server.ino."""

import config
import datetime
import math
import os
import random
import serial  # pip3 install pyserial
import sys
import time
import traceback

from lib import *
from lib.app import App
from lib.asteriods import Asteriods
from lib.monitor import Monitor

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
        try:
            bytes = self.ser.readline()
            message = bytes.decode(ASCII).strip()
        except Exception as e:
            print(">>>", bytes, ' ###', e)
            return f'ERROR {e}'
        if config.DEBUG: print(">>>", message)
        if message == self.on_message:
            self.on_fn(message)
        return message


class Board:
    def __init__(self, channel):
        self.chan = channel
        self.configure_callback = None
        self.chan.open()
        self.chan.set_callback('READY', self.on_ready)
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

    def on_ready(self, _=None):
        time.sleep(0.2)
        self.boots += 1
        self.configure()

    def set_configure_callback(self, configure_callback):
        self.configure_callback = configure_callback

    def configure(self):
        # normally called by callback
        self.chan.clear()
        self.command(f'setRotation {config.ROTATION}')
        self.command('autoDisplay 0')
        self.command('reset')

        w = int(self.command(f'width'))
        h = int(self.command(f'height'))
        if not config.WIDTH:
            config.WIDTH = w
            config.HEIGHT = h
            print(f'OLED resolution: {w} x {h}')

        if self.configure_callback:
            self.configure_callback()
        self.configured = True

    def wait_configured(self):
        while True:
            if self.configured:
                return
            self.chan.read()
            time.sleep(0.5)



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

class Cube(App):
    def __init__(self, board):
        super().__init__(board)

        """Rotating Cube, by Al Sweigart al@inventwithpython.com A rotating
        cube animation. Press Ctrl-C to stop.  This code is available
        at https://nostarch.com/big-book-small-python-programming
        Tags: large, artistic, math

        https://inventwithpython.com/bigbookpython/project62.html"""

        # Set up the constants:
        SIZE = min(config.WIDTH, config.HEIGHT)
        OFFSET_X = (config.WIDTH-SIZE) // 2
        OFFSET_Y = (config.HEIGHT-SIZE) // 2
        SCALEX = SCALEY = SIZE // 4

        TRANSLATEX = (config.WIDTH - 4) // 2
        TRANSLATEY = (config.HEIGHT - 4) // 2 + 4

        # (!) Try changing this to '#' or '*' or some other character:
        LINE_CHAR = chr(9608)  # Character 9608 is a solid block.

        # (!) Try setting two of these values to zero to rotate the cube only
        # along a single axis:
        X_ROTATE_SPEED = 0.03
        Y_ROTATE_SPEED = 0.08
        Z_ROTATE_SPEED = 0.13

        # This program stores XYZ coordinates in lists, with the X coordinate
        # at index 0, Y at 1, and Z at 2. These constants make our code more
        # readable when accessing the coordinates in these lists.
        X = 0
        Y = 1
        Z = 2

        i = 0

        def line(x1, y1, x2, y2, c):
            self.command(f'drawLine {x1+.5} {y1+.5} {x2+.5} {y2+.5} {c}')

        def rotatePoint(x, y, z, ax, ay, az):
            """Returns an (x, y, z) tuple of the x, y, z arguments rotated.

            The rotation happens around the 0, 0, 0 origin by angles
            ax, ay, az (in radians).
                Directions of each axis:
                 -y
                  |
                  +-- +x
                 /
                +z
            """

            # Rotate around x axis:
            rotatedX = x
            rotatedY = (y * math.cos(ax)) - (z * math.sin(ax))
            rotatedZ = (y * math.sin(ax)) + (z * math.cos(ax))
            x, y, z = rotatedX, rotatedY, rotatedZ

            # Rotate around y axis:
            rotatedX = (z * math.sin(ay)) + (x * math.cos(ay))
            rotatedY = y
            rotatedZ = (z * math.cos(ay)) - (x * math.sin(ay))
            x, y, z = rotatedX, rotatedY, rotatedZ

            # Rotate around z axis:
            rotatedX = (x * math.cos(az)) - (y * math.sin(az))
            rotatedY = (x * math.sin(az)) + (y * math.cos(az))
            rotatedZ = z

            # False perspective
            k = 1 if alt else 1.5**z *.6 + .25

            return (rotatedX*k, rotatedY*k, rotatedZ)


        def adjustPoint(point):
            """Adjusts the 3D XYZ point to a 2D XY point fit for displaying on
            the screen. This resizes this 2D point by a scale of SCALEX and
            SCALEY, then moves the point by TRANSLATEX and TRANSLATEY."""
            return (int(point[X] * SCALEX + TRANSLATEX),
                    int(point[Y] * SCALEY + TRANSLATEY))

        def cube(rotatedCorners, xRotation, yRotation, zRotation, c):
            for i in range(len(CUBE_CORNERS)):
                x = CUBE_CORNERS[i][X]
                y = CUBE_CORNERS[i][Y]
                z = CUBE_CORNERS[i][Z]
                rotatedCorners[i] = rotatePoint(x, y, z, xRotation,
                    yRotation, zRotation)

            # Find farthest point to omit hidden edges
            minZ = 0
            for fromCornerIndex, toCornerIndex in CUBE_EDGES:
                fromPoint = rotatedCorners[fromCornerIndex]
                toPoint = rotatedCorners[toCornerIndex]
                minZ = min(minZ, fromPoint[Z])
                minZ = min(minZ, toPoint[Z])

            # Get the points of the cube lines:
            for fromCornerIndex, toCornerIndex in CUBE_EDGES:
                fromPoint = rotatedCorners[fromCornerIndex]
                toPoint = rotatedCorners[toCornerIndex]
                fromX, fromY = adjustPoint(fromPoint)
                toX, toY = adjustPoint(toPoint)
                if alt:
                    if fromPoint[Z] == minZ or toPoint[Z] == minZ:
                        continue  # bound to farthest point: hidden edge
                line(fromX, fromY, toX, toY, c)

        """CUBE_CORNERS stores the XYZ coordinates of the corners of a cube.
        The indexes for each corner in CUBE_CORNERS are marked in this diagram:
              0------1
             /|     /|
            2------3 |
            | 4----|-5
            |/     |/
            6------7
        """
        CUBE_CORNERS = [[-1, -1, -1], # Point 0
                        [ 1, -1, -1], # Point 1
                        [-1, -1,  1], # Point 2
                        [ 1, -1,  1], # Point 3
                        [-1,  1, -1], # Point 4
                        [ 1,  1, -1], # Point 5
                        [-1,  1,  1], # Point 6
                        [ 1,  1,  1]] # Point 7
        CUBE_EDGES = (
            (0, 1), (1, 3), (3, 2), (2, 0),
            (0, 4), (1, 5), (2, 6), (3, 7),
            (4, 5), (5, 7), (7, 6), (6, 4),
        )

        # rotatedCorners stores the XYZ coordinates from CUBE_CORNERS after
        # they've been rotated by rx, ry, and rz amounts:
        rotatedCorners = [None, None, None, None, None, None, None, None]
        # Rotation amounts for each axis:
        xRotation = 0.0
        yRotation = 0.0
        zRotation = 0.0

        previous = None
        undraw = False
        escaper = KeyEscaper(self, self.board, steady_message=False)
        start = datetime.datetime.now()
        while True:  # Main program loop.
            alt = (i%50) > 25
            if not undraw:
                self.command('clearDisplay')

            if previous and undraw:
                xRotation, yRotation, zRotation = previous
                cube(rotatedCorners, xRotation, yRotation, zRotation, 0)

            escaper.pre_check()

            # Rotate the cube along different axes by different amounts:
            xRotation += X_ROTATE_SPEED
            yRotation += Y_ROTATE_SPEED
            zRotation += Z_ROTATE_SPEED
            cube(rotatedCorners, xRotation, yRotation, zRotation, 1)

            if undraw:
                previous = xRotation, yRotation, zRotation

            if escaper.check():
                break
            self.command('display')
            i += 1



################################################################################
# Helper classes

class RebootedException(Exception):
    pass


class KeyEscaper:
    def __init__(self, app, board, message="Hold a key to move on",
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
            if self.command('readButtons') != NONE:
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
chan = Channel()
board = Board(chan)
board.wait_configured()
#board.monitor()
while True:
    try:
        while True:
            Monitor(board)
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
    except Exception as e:
        msg = traceback.format_exc()
        fatal(msg)
