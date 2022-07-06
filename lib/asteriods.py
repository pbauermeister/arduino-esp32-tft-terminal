from lib import *
from lib.app import App
import time
import random
import math
import datetime
import config

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

GOVER_TITLE = "GAME OVER"
GOVER_POS = 0

LIVES = 3

MENU_TIMEOUT = datetime.timedelta(seconds=30)
MENU_PLAY = 1
MENU_QUIT = 2
MENU_AUTO = 3

GOTO_MENU = 1
GOTO_REPLAY = 2
GOTO_QUIT = 3


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
        global GOVER_POS
        GOVER_POS = self.get_title_pos(GOVER_TITLE)

        self.run()
        board.set_configure_callback(None)

    def run(self):
        while True:
            menu = self.menu()
            auto = False
            if menu == MENU_QUIT:
                return
            elif menu == MENU_PLAY:
                pass
            elif menu == MENU_AUTO:
                auto = True
            else:
                return

            while True:
                self.boots = self.board.boots
                go = self.run_once(auto)
                if go == GOTO_MENU:
                    break
                elif go == GOTO_REPLAY:
                    auto = False
                    continue
                elif go == GOTO_QUIT:
                    return

    def menu(self):
        self.command('reset')
        self.command('setTextSize 1')
        self.command(f'print Play {self.name.upper()}:\\n')
        self.command(f'print   C   fire\\n')
        self.command(f'print   B   cntr-clockwise\\n')
        self.command(f'print   A   clockwise\\n')
        self.command(f'print   A+B shield\\n')
        self.command(f'print   R   back to menu\\n\\n')
        self.command(f'print R:exit  any:start')
        self.command(f'display')
        while self.read_keys():
            pass

        boots = self.board.boots
        start = datetime.datetime.now()
        while True:
            if self.read_keys():
                while self.read_keys():
                    pass
                return MENU_PLAY
            if self.board.boots > boots:
                return MENU_QUIT
            delta = datetime.datetime.now() - start
            if delta > MENU_TIMEOUT:
                return MENU_AUTO

    def read_keys(self):
        ans = self.command('readButtons')
        if ans.startswith(ERROR):
            return set()
        if ans == NONE:
            return set()
        for c in ans:
            if c not in 'ABC':
                return set()  # garbage
        return set(ans)

    def run_once(self, autoplay):
        game = Game(self.board, autoplay)
        overs = 0
        autoplay_start = None
        while True:
            if self.boots != self.board.boots:
                return GOTO_MENU

            keys = self.read_keys()
            if autoplay and keys:
                return GOTO_MENU

            # Erase
            self.command(f'reset')

            # Update / create
            game.update_asteroids()
            game.create_asteroid()
            if autoplay:
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
                time.sleep(3)
                if autoplay:
                    return GOTO_QUIT
                autoplay = True
                autoplay_start = datetime.datetime.now()
                game.player.autoplay =True
                game.player.lives = LIVES
                overs = 0
            if game.player.lives == 0:
                overs += 1

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


class Game:
    def __init__(self, board, autoplay):
        self.board = board
        self.player = Player(autoplay)
        self.shots = []
        self.asteroids = []

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
        x = config.WIDTH - 12
        l.append(f'setCursor {x} {0}')
        l.append(f'print L{self.player.lives}')
        if self.player.autoplay:
            x, y = GOVER_POS
            l.append(f'setCursor {x} {y}')
            l.append(f'print {GOVER_TITLE}')

        if self.player.ship.aster_crash:
            return

        if self.player.ship.reloading:
            r = self.player.ship.reloading
            l.append(f'home')
            l.append(f'print Reload {r}')
        elif self.player.ship.shield > 0 and not self.player.ship.protect:
            l.append(f'home')
            l.append(f'print Shield')
        else:
            l.append(f'home')
            l.append(f'print {self.player.score:04d}')


    def handle_crash(self):
        if not self.player.ship.aster_crash:
            return False
        self.boom(self.player.ship, self.player.ship.aster_crash)
        self.player.ship.aster_crash = None
        if self.player.lives:
            self.player.lives -= 1
        return True

    def boom(self, ship, asteroid):
        command = self.board.command
        command(f'home')
        command(f'print Boom!')
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
    def __init__(self, autoplay):
        self.ship = Ship()
        self.lives = LIVES
        self.autoplay = autoplay
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
        if self.shield > 0 and not self.protect:
            l.append(f'fillTriangle {self.x0} {self.y0} '
                     f'{self.x1} {self.y1} {self.x2} {self.y2} 1')
        else:
            l.append(f'drawTriangle {self.x0} {self.y0} '
                     f'{self.x1} {self.y1} {self.x2} {self.y2} 1')

        if self.shield > 0:
            if self.protect:
                r = SHIELD_R
            else:
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
