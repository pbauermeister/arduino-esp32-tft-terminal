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
        config.WIDTH = int(self.command(f'width'))
        config.HEIGHT = int(self.command(f'height'))
        if self.configure_callback:
            self.configure_callback()
        self.configured = True

    def wait_configured(self):
        while True:
            if self.configured:
                return
            self.chan.read()
            time.sleep(0.5)


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
        ans = self.command(f'getTextBounds 0 0 {title}')
        vals = [int(v) for v in ans.split()]
        w, h = vals[-2:]
        x = int(config.WIDTH/2 - w/2 +.5)
        y = int(config.HEIGHT/2 - h/2 +.5)
        return x, y

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


class Asteriods(App):
    def custom_configure(self):
        self.board.command('setTextWrap 0')
        return
        self.board.command('autoReadButtons 1')
        print("* custom_configure")

    def __init__(self, board):
        super().__init__(board)
        board.set_configure_callback(self.custom_configure)
        self.custom_configure()
        SHIP_R = 6
        SHIP_V = 2
        SHIP_ROT = .2

        SHOT_V = 5

        SHOT_DELAY = 2
        SHOT_MAX = 8
        ASTEROIDS_MAX = 5

        ASTER_R = 2, 10
        ASTER_SPLIT_A = .4

        SHIELD_DURATION = 12
        PROTECT_DURATION = 16
        SHIELD_RELOAD = 20
        SHIELD_R = SHIP_R + 4

        SCORE_DEC = 20

        GOVER_TITLE = "GAME OVER"
        GOVER_POS = self.get_title_pos(GOVER_TITLE)

        LIVES = 3

        class Game:
            def __init__(self, board):
                self.board = board

                self.player = Player()
                self.shots = []
                self.asteroids = []
                self.player = Player()

            def update_asteroids(self):
                for a in self.asteroids:
                    a.move()
                    if a.hit:
                        a.hit = False
                        a.shrink()
                        if a.r == 0:
                            self.asteroids.remove(a)

            def create_asteroid(self):
                if random.random() > .05: return
                if len(self.asteroids) >= ASTEROIDS_MAX: return
                self.asteroids.append(Asteroid(ship=self.player.ship))

            def autoplay(self, keys):
                p = random.random()
                if p < .1:
                    if len(self.asteroids):
                        keys.add('C')
                elif p < .2:
                    keys.add('A')
                elif p < .4:
                    keys.add('B')
                x, y, r = self.player.ship.x, self.player.ship.y, SHIELD_R
                for a in self.asteroids:
                    if detect_touch(x, y, a.x, a.y, r, a.r):
                        # try shield
                        keys.add('B')
                        keys.add('C')

            def update_ship(self, keys):
                shoot = 'C' in keys
                self.player.ship.move(keys)
                if shoot:
                    self.player.ship.shoot(self.shots)

            def update_shots(self):
                for shot in self.shots:
                    shot.move()
                    if not shot.valid():
                        self.shots.remove(shot)

            def do_detections(self):
                self.player.score += detect_hits(self.shots, self.asteroids)
                detect_collisions(self.asteroids)
                detect_crash(self.player.ship, self.asteroids)

            def add_renders(self, l):
                self.player.ship.add_renders(l)
                for a in self.asteroids:
                    a.add_renders(l)
                for shot in self.shots:
                    shot.add_renders(l)

            def add_renders_overlays(self, l):
                if self.player.lives:
                    x = config.WIDTH - 12
                    l.append(f'setCursor {x} {0}')
                    l.append(f'print L{self.player.lives}')
                else:
                    x, y = GOVER_POS
                    l.append(f'setCursor {x} {y}')
                    l.append(f'print GAME OVER')

                if self.player.ship.aster_crash:
                    return

                if self.player.ship.reloading:
                    r = self.player.ship.reloading
                    l.append(f'home')
                    l.append(f'print Reload {r}')
                else:
                    l.append(f'home')
                    l.append(f'print {self.player.score:04d}')


            def handle_crash(self):
                if not self.player.ship.aster_crash:
                    return False
                self.boom(self.player.ship, self.player.ship.aster_crash)
                self.player.ship.aster_crash = None
                self.player.score = max(self.player.score - SCORE_DEC, 0)
                if self.player.lives:
                    self.player.lives -= 1
                return True

            def boom(self, ship, asteroid):
                command = self.board.command
                command(f'home')
                command(f'print Boom! -{SCORE_DEC}')
                i = 0
                for i in range(4):
                    i += 1
                    renders = []
                    ship.add_renders_boom(i, renders)
                    asteroid.add_renders_boom(i, renders)
                    for r in renders:
                        command(r)
                    command('display')
                ship.protect = PROTECT_DURATION
                ship.shield = SHIELD_DURATION

        class Player:
            def __init__(self):
                self.ship = Ship()
                self.lives = LIVES
                self.score = 0

        class Ship:
            def __init__(self):
                self.x = config.WIDTH / 2
                self.y = config.HEIGHT / 2
                self.a = 0
                self.r = SHIP_R
                self.v = SHIP_V
                self.shield = -SHIELD_RELOAD
                self.i = 0
                self.compute()
                self.shot_reload = 0
                self.protect = 0
                self.aster_crash = None
                self.reloading = 0

            def move(self, keys):
                v = self.v
                # rotate & advance
                if 'A' in keys and 'B' in keys:
                    if self.shield < -SHIELD_RELOAD:
                        self.shield = SHIELD_DURATION
                elif 'B' in keys:
                    self.a -= SHIP_ROT
                    v = self.v/2
                elif 'A' in keys:
                    self.a += SHIP_ROT
                    v = self.v/2
                if 'C' in keys:
                    pass #v = self.v/4

                self.ca, self.sa = math.cos(self.a), math.sin(self.a)
                self.x += self.ca * v
                self.y += self.sa * v
                self.i += 1
                self.shot_reload += 1
                self.shield -= 1
                if self.protect:
                    self.protect -= 1

                # wrap around
                if self.x < -self.r:
                    self.x = config.WIDTH + self.r
                if self.x > config.WIDTH + self.r:
                    self.x = -self.r
                if self.y < -self.r:
                    self.y = config.HEIGHT + self.r
                if self.y > config.HEIGHT + self.r:
                    self.y = -self.r
                self.compute()

                if self.shield <=0 and self.shield > -SHIELD_RELOAD:
                    self.reloading = SHIELD_RELOAD + self.shield
                else:
                    self.reloading = 0

            def compute(self):
                self.ca, self.sa = math.cos(self.a), math.sin(self.a)
                self.x0 = int(self.r*self.ca + self.x +.5)
                self.y0 = int(self.r*self.sa + self.y +.5)

                b = self.a + math.pi * .8
                self.x1 = int(self.r*math.cos(b) + self.x +.5)
                self.y1 = int(self.r*math.sin(b) + self.y +.5)

                b = self.a + math.pi * 1.2
                self.x2 = int(self.r*math.cos(b) + self.x +.5)
                self.y2 = int(self.r*math.sin(b) + self.y +.5)

            def shoot(self, shots):
                if self.shield > 0:
                    return
                if self.shot_reload <= SHOT_DELAY:
                    return
                if len(shots) >= SHOT_MAX:
                    return
                vx, vy = self.ca*SHOT_V, self.sa*SHOT_V
                shot = Shot(self.x0, self.y0, vx, vy)
                shots.append(shot)
                shot = Shot(self.x0+vx, self.y0+vy, vx, vy)
                shots.append(shot)
                self.shot_reload = 0

            def add_renders(self, l):
                if self.protect and self.i & 1:
                    l.append(f'fillTriangle {self.x0} {self.y0} '
                             f'{self.x1} {self.y1} {self.x2} {self.y2} 1')
                else:
                    l.append(f'drawTriangle {self.x0} {self.y0} '
                             f'{self.x1} {self.y1} {self.x2} {self.y2} 1')

                if self.shield > 0:
                    r = SHIELD_R -3 + (self.i%3)*3
                    l.append(f'drawCircle {self.x} {self.y} {r} 1')

            def add_renders_boom(self, i, l):
                c = i % 2
                l.append(f'fillTriangle {self.x0} {self.y0} '
                         f'{self.x1} {self.y1} {self.x2} {self.y2} {c}')
                l.append(f'drawTriangle {self.x0} {self.y0} '
                         f'{self.x1} {self.y1} {self.x2} {self.y2} 1')

        class Shot:
            def __init__(self, x, y, vx, vy):
                self.x, self.y, self.vx, self.vy = x, y, vx, vy

            def move(self):
                self.x += self.vx
                self.y += self.vy

            def valid(self):
                return \
                    self.x >=0 and self.x < config.WIDTH and \
                    self.y >=0 and self.y <config.HEIGHT

            def add_renders(self, l):
                l.append(f'drawPixel {self.x} {self.y} 1')

        class Asteroid:
            def __init__(self, ship=None, other=None):
                if ship is not None:
                    self.init(ship.x, ship.y)
                elif other is not None:
                    self.xx, self.x = other.xx, other.x
                    self.yy, self.y = other.yy, other.y
                    self.r = other.r
                    self.a = other.a
                    self.hit = other.hit
                else:
                    self.init(0, 0)

            def init(self, ship_x, ship_y):
                r = random.randrange(*ASTER_R)
                a = random.random() * math.pi + math.pi/2

                p = random.random()
                if p > .5:
                    x = config.WIDTH + r
                    y = config.HEIGHT * random.random()
                elif p < .25:
                    y = -r
                    x = config.WIDTH * (.75 + random.random() * .25)
                else:
                    y = config.HEIGHT + r
                    x = config.WIDTH * (.75 + random.random() * .25)

                if ship_x > config.WIDTH / 2:
                    x = config.WIDTH - x
                    a += math.pi/2

                self.xx = self.x = int(x+.5)
                self.yy = self.y = int(y+.5)
                self.r = int(r+.5)
                self.a = a
                self.hit = False

            def move(self, dist=None):
                if not dist:
                    v = max((ASTER_R[1] - self.r)**1.5 / 6, .5)
                    dist = v
                vx = math.cos(self.a) * dist
                vy = math.sin(self.a) * dist

                self.xx += vx
                self.yy += vy

                # wrap around
                if self.xx < -self.r:
                    self.xx = config.WIDTH + self.r
                if self.xx > config.WIDTH + self.r:
                    self.xx = -self.r
                if self.yy < -self.r:
                    self.yy = config.HEIGHT + self.r
                if self.yy > config.HEIGHT + self.r:
                    self.yy = -self.r
                self.x = int(self.xx+.5)
                self.y = int(self.yy+.5)

            def shrink(self):
                self.r -= 1
                if self.r < 4:
                    self.r = 0

            def add_renders(self, l):
                if self.hit:
                    l.append(f'fillCircle {self.x} {self.y} {self.r} 1')
                else:
                    l.append(f'drawCircle {self.x} {self.y} {self.r} 1')

            def add_renders_boom(self, i, l):
                c = i%2
                l.append(f'fillCircle {self.x} {self.y} {self.r} {c}')
                l.append(f'drawCircle {self.x} {self.y} {self.r} 1')

        def detect_hits(shots, asteroids):
            score = 0
            if not shots or not asteroids:
                return 0
            for a in asteroids:
                for s in shots:
                    if detect_hit(s.x, s.y, a, .75):
                        shots.remove(s)
                        a.hit = True
                        score += int(a.r)

                        if a.r >= sum(ASTER_R)/2:
                            # split in two
                            a.r -= 1
                            a1 = Asteroid(other=a)
                            a1.a += ASTER_SPLIT_A
                            a1.move(a1.r+1)
                            asteroids.append(a1)

                            a2 = Asteroid(other=a)
                            a2.a -= ASTER_SPLIT_A
                            a2.move(a2.r+1)
                            asteroids.append(a2)

                            if a in asteroids:
                                asteroids.remove(a)
                        continue
            return score

        def detect_crash(ship, asteroids):
            if ship.protect:
                return

            if ship.shield > 0:
                for a in asteroids:
                    if detect_touch(ship.x, ship.y, a.x, a.y, SHIELD_R, a.r):
                        a.hit = True
                return

            for a in asteroids:
                if (detect_hit(ship.x0, ship.y0, a,  .9) or
                    detect_hit(ship.x1, ship.y1, a,  .9) or
                    detect_hit(ship.x2, ship.y2, a,  .9) or
                    detect_hit(ship.x,  ship.y,  a, 1.1) ):
                    a.hit = True
                    ship.aster_crash = a
            return

        def detect_collisions(asteroids):
            pairs = {}
            for a in asteroids:
                for b in asteroids:
                    if a is b: continue
                    if (a, b) in pairs: continue
                    pairs[(a, b)] = True
                    if detect_touch(a.x, a.y, b.x, b.y, a.r, b.r):
                        a.hit=True
                        b.hit=True

        def detect_touch(x0, y0, x1, y1, r0, r1):
            dx = (x0 - x1)**2
            dy = (y0 - y1)**2
            rr = (dx + dy)
            return rr < (r0 + r1)**2

        def detect_hit(x, y, asteroid, factor):
            a = asteroid
            dx = (a.x - x)**2
            dy = (a.y - y)**2
            r2 = (dx + dy) * factor
            return r2 < a.r**2

        def read_keys():
            ans = self.command('readButtons')
            if ans != NONE:
                return set(ans)
            else:
                return set()

        def run(game):
            overs = 0
            while True:
                keys = read_keys()
                if game.player.lives == 0 and keys:
                    break

                # Erase
                self.command(f'reset')

                # Update / create
                game.update_asteroids()
                game.create_asteroid()
                if game.player.lives == 0:
                    game.autoplay(keys)
                game.update_ship(keys)
                game.update_shots()

                # Hits
                game.do_detections()

                # Draw
                renders = []
                game.add_renders(renders)

                # indicators
                game.add_renders_overlays(renders)

                # show
                for render in renders:
                    self.command(render)
                self.command('display')

                # crash
                game.handle_crash()

                if overs == 1:
                    time.sleep(1)
                if game.player.lives == 0:
                    overs += 1

        while True:
            game = Game(self.board)
            run(game)

        board.set_configure_callback(None)

    def k_command(self, keys, cmd):
        answer = self.command(cmd)
        self.extract_keys(answer, keys)

    def extract_keys(self, answer, keys):
        parts = answer.split(' ', 1)
        if len(parts) < 2 or parts[0] != 'OK':
            return
        k = parts[1]
        if 'A' in k: keys.add('A')
        if 'B' in k: keys.add('B')
        if 'C' in k: keys.add('C')

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
