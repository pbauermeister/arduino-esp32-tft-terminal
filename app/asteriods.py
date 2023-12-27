import datetime
import math
import random
import time
from dataclasses import dataclass

import config
from app import App
from lib import *
from lib.board import Board

# Parameters
SHIP_RADIUS = 6
SHIP_SPEED = 2
SHIP_ROT_STEP = .2

SHOT_SPEED = 5
SHOT_DELAY = 2
SHOT_MAX = 8

ASTEROID_NB_MAX = 5
ASTEROID_RADIUS = 2, 10
ASTEROID_SPLIT_A = .4  # angle

SHIELD_DURATION = 12
SHIELD_TIMEOUT = 20
SHIELD_RADIUS = SHIP_RADIUS + 6

PROTECT_DURATION = 16

GAME_OVER_TITLE = "GAME OVER"
GAME_OVER_POS = 0, 0  # to be computed

LIVES = 3

MENU_TIMEOUT = 30

# Enums
MENU_PLAY = 1
MENU_NEXT = 2
MENU_AUTO = 3
MENU_QUIT = 4

GOTO_MENU = 1
GOTO_NEXT = 2
GOTO_QUIT = 3


class Shot:
    def __init__(self, x: float, y: float, vx: float, vy: float):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy

    def move(self) -> None:
        self.x += self.vx
        self.y += self.vy

    def valid(self) -> bool:
        return \
            self.x >= 0 and self.x < config.WIDTH and \
            self.y >= 0 and self.y < config.HEIGHT

    def add_renders(self, l: list[str]) -> None:
        l.append(f'drawPixel {self.x} {self.y} 1')


class Ship:
    def __init__(self) -> None:
        self.x: float = config.WIDTH / 2
        self.y: float = config.HEIGHT / 2
        self.a: float = 0
        self.r: int = SHIP_RADIUS
        self.v: float = SHIP_SPEED
        self.shield: int = -SHIELD_TIMEOUT
        self.i: int = 0
        self.compute()
        self.shot_reload = 0
        self.protect = 0
        self.aster_crash: Asteroid = None
        self.reloading = 0

    def move(self, keys: set[str]) -> None:
        v = self.v
        # rotate & advance
        if 'A' in keys and 'B' in keys:
            if self.shield < -SHIELD_TIMEOUT:
                self.shield = SHIELD_DURATION
        elif 'B' in keys:
            self.a -= SHIP_ROT_STEP
            v = self.v/2
        elif 'A' in keys:
            self.a += SHIP_ROT_STEP
            v = self.v/2
        if 'C' in keys:
            pass  # v = self.v/4

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

        if self.shield <= 0 and self.shield > -SHIELD_TIMEOUT:
            self.reloading = SHIELD_TIMEOUT + self.shield
        else:
            self.reloading = 0

    def compute(self) -> None:
        self.ca, self.sa = math.cos(self.a), math.sin(self.a)
        self.x0 = int(self.r*self.ca + self.x + .5)
        self.y0 = int(self.r*self.sa + self.y + .5)

        b = self.a + math.pi * .8
        self.x1 = int(self.r*math.cos(b) + self.x + .5)
        self.y1 = int(self.r*math.sin(b) + self.y + .5)

        b = self.a + math.pi * 1.2
        self.x2 = int(self.r*math.cos(b) + self.x + .5)
        self.y2 = int(self.r*math.sin(b) + self.y + .5)

    def shoot(self, shots: list[Shot]) -> None:
        if self.shield > 0:
            return
        if self.shot_reload <= SHOT_DELAY:
            return
        if len(shots) >= SHOT_MAX:
            return
        vx, vy = self.ca*SHOT_SPEED, self.sa*SHOT_SPEED
        shot = Shot(self.x0, self.y0, vx, vy)
        shots.append(shot)
        shot = Shot(self.x0+vx, self.y0+vy, vx, vy)
        shots.append(shot)
        self.shot_reload = 0

    def add_renders(self, l: list[str]) -> None:
        x0 = self.x0
        y0 = self.y0
        x1 = self.x1
        y1 = self.y1
        x2 = self.x2
        y2 = self.y2
        if self.shield > 0 and not self.protect:
            l.append(f'fillTriangle {x0} {y0} '
                     f'{x1} {y1} {x2} {y2} 1')
        else:
            l.append(f'drawTriangle {x0} {y0} '
                     f'{x1} {y1} {x2} {y2} 1')

        if self.shield > 0:
            x = int(self.x + .5)
            y = int(self.y + .5)
            if self.protect:
                r = SHIELD_RADIUS
            else:
                r = SHIELD_RADIUS - 3 + (self.i % 3)*3
            l.append(f'drawCircle {x} {y} {r} 1')

    def add_renders_boom(self, i: int, l: list[str]) -> None:
        c = i % 2
        l.append(f'fillTriangle {self.x0} {self.y0} '
                 f'{self.x1} {self.y1} {self.x2} {self.y2} {c}')
        l.append(f'drawTriangle {self.x0} {self.y0} '
                 f'{self.x1} {self.y1} {self.x2} {self.y2} 1')


class Player:
    def __init__(self, autoplay_enabled: bool):
        self.ship = Ship()
        self.lives = LIVES
        self.autoplay_enabled = autoplay_enabled
        self.score = 0


@dataclass
class AsteriodData:
    xx: float
    x: float
    yy: float
    y: float
    r: float
    a: float
    hit: bool


class Asteroid(AsteriodData):
    def __init__(self, ship: Ship = None, other: AsteriodData = None):
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

    def init(self, ship_x: float, ship_y: float) -> None:
        r = random.randrange(*ASTEROID_RADIUS)
        a = random.random() * math.pi + math.pi/2

        p = random.random()
        x: float
        y: float
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

    def move(self, dist: float = None) -> None:
        if dist is None:
            v = max((ASTEROID_RADIUS[1] - self.r)**1.5 / 6, .5)
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

    def shrink(self) -> None:
        self.r -= 1
        if self.r < 4:
            self.r = 0

    def add_renders(self, l: list[str]) -> None:
        x = int(self.x + .5)
        y = int(self.y + .5)
        r = int(self.r + .5)
        if self.hit:
            l.append(f'fillCircle {x} {y} {r} 1')
        else:
            l.append(f'drawCircle {x} {y} {r} 1')

    def add_renders_boom(self, i: int, l: list[str]) -> None:
        x = int(self.x + .5)
        y = int(self.y + .5)
        r = int(self.r + .5)
        c = i % 2
        l.append(f'fillCircle {x} {y} {r} {c}')
        l.append(f'drawCircle {x} {y} {r} 1')


class Game:
    def __init__(self, app: App, autoplay_enabled: bool):
        self.app = app
        self.player = Player(autoplay_enabled)
        self.shots: list[Shot] = []
        self.asteroids: list[Asteroid] = []

    def update_asteroids(self) -> None:
        for a in self.asteroids:
            a.move()
            if a.hit:
                a.hit = False
                a.shrink()
                if a.r == 0:
                    self.asteroids.remove(a)

    def create_asteroid(self) -> None:
        if random.random() > .05:
            return
        if len(self.asteroids) >= ASTEROID_NB_MAX:
            return
        self.asteroids.append(Asteroid(ship=self.player.ship))

    def autoplay(self, keys: set[str]) -> None:
        p = random.random()
        if p < .1:
            if len(self.asteroids):
                keys.add('C')
        elif p < .2:
            keys.add('A')
        elif p < .4:
            keys.add('B')

        x, y, r = self.player.ship.x, self.player.ship.y, SHIELD_RADIUS
        for a in self.asteroids:
            if Detect.touch(x, y, a.x, a.y, r, a.r):
                # try shield
                keys.add('B')
                keys.add('C')

    def update_ship(self, keys: set[str]) -> None:
        shoot = 'C' in keys
        self.player.ship.move(keys)
        if shoot:
            self.player.ship.shoot(self.shots)

    def update_shots(self) -> None:
        for shot in self.shots:
            shot.move()
            if not shot.valid():
                self.shots.remove(shot)

    def do_detections(self) -> None:
        self.player.score += Detect.hits(self.shots, self.asteroids)
        Detect.collisions(self.asteroids)
        Detect.crash(self.player.ship, self.asteroids)

    def add_renders(self, l: list[str]) -> None:
        self.player.ship.add_renders(l)
        for a in self.asteroids:
            a.add_renders(l)
        for shot in self.shots:
            shot.add_renders(l)

    def add_renders_overlays(self, l: list[str]) -> None:
        x = config.WIDTH - 12
        l.append(f'setCursor {x} {0}')
        l.append(f'print L{self.player.lives}')
        if self.player.autoplay_enabled:
            x, y = GAME_OVER_POS
            l.append(f'setCursor {x} {y}')
            l.append(f'print {GAME_OVER_TITLE}')

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

    def handle_crash(self) -> bool:
        if not self.player.ship.aster_crash:
            return False
        self.boom(self.player.ship, self.player.ship.aster_crash)
        self.player.ship.aster_crash = None
        if self.player.lives:
            self.player.lives -= 1
        return True

    def boom(self, ship: Ship, asteroid: Asteroid) -> None:
        command = self.app.command
        command(f'home')
        command(f'print Boom!')
        i = 0
        for i in range(4):
            i += 1
            renders: list[str] = []
            ship.add_renders_boom(i, renders)
            asteroid.add_renders_boom(i, renders)
            for r in renders:
                command(r)
            command('display')
        ship.protect = PROTECT_DURATION
        ship.shield = SHIELD_DURATION


class Detect:
    @staticmethod
    def hits(shots: list[Shot], asteroids: list[Asteroid]) -> int:
        score = 0
        if not shots or not asteroids:
            return 0
        for a in asteroids:
            for s in shots:
                if Detect.hit(s.x, s.y, a, .75):
                    shots.remove(s)
                    a.hit = True
                    score += int(a.r)

                    if a.r >= sum(ASTEROID_RADIUS)/2:
                        # split in two
                        a.r -= 1
                        a1 = Asteroid(other=a)
                        a1.a += ASTEROID_SPLIT_A
                        a1.move(a1.r+1)
                        asteroids.append(a1)

                        a2 = Asteroid(other=a)
                        a2.a -= ASTEROID_SPLIT_A
                        a2.move(a2.r+1)
                        asteroids.append(a2)

                        if a in asteroids:
                            asteroids.remove(a)
                    continue
        return score

    @staticmethod
    def crash(ship: Ship, asteroids: list[Asteroid]) -> None:
        if ship.protect:
            return

        if ship.shield > 0:
            for a in asteroids:
                if Detect.touch(ship.x, ship.y, a.x, a.y, SHIELD_RADIUS, a.r):
                    a.hit = True
            return

        for a in asteroids:
            if (Detect.hit(ship.x0, ship.y0, a,  .9) or
                Detect.hit(ship.x1, ship.y1, a,  .9) or
                Detect.hit(ship.x2, ship.y2, a,  .9) or
                    Detect.hit(ship.x,  ship.y,  a, 1.1)):
                a.hit = True
                ship.aster_crash = a
        return

    @staticmethod
    def collisions(asteroids: list[Asteroid]) -> None:
        pairs = {}
        for a in asteroids:
            for b in asteroids:
                if a is b:
                    continue
                ah = a and a.__hash__
                bh = b and b.__hash__
                if (ah, bh) in pairs:
                    continue
                pairs[(ah, bh)] = True
                if Detect.touch(a.x, a.y, b.x, b.y, a.r, b.r):
                    a.hit = True
                    b.hit = True

    @staticmethod
    def touch(x0: float, y0: float, x1: float, y1: float, r0: float, r1: float) -> bool:
        dx = (x0 - x1)**2
        dy = (y0 - y1)**2
        rr = (dx + dy)
        return rr < (r0 + r1)**2

    @staticmethod
    def hit(x: float, y: float, asteroid: Asteroid, factor: float) -> bool:
        a = asteroid
        dx = (a.x - x)**2
        dy = (a.y - y)**2
        r2 = (dx + dy) * factor
        return r2 < a.r**2


class Autoplay:
    def __init__(self, game: Game, enabled: bool):
        self.game = game
        self.enabled = enabled
        self.start: datetime.datetime = None
        self.until: datetime.datetime = None
        if enabled:
            self.enable()

    def enable(self) -> None:
        self.enabled = True
        self.start = datetime.datetime.now()
        ap_timeout = config.APP_ASTERIODS_AUTOPLAY_TIMEOUT
        if ap_timeout:
            self.until = self.start + \
                datetime.timedelta(seconds=ap_timeout)
        else:
            self.until = None
        self.game.player.autoplay_enabled = True
        self.game.player.score = 0
        self.game.player.lives = LIVES


class Asteriods(App):
    def extra_configurator(self) -> None:
        self.command('setTextWrap 0')

    def __init__(self, board: Board):
        super().__init__(board, auto_read=False,
                         extra_configurator=self.extra_configurator)
        global GAME_OVER_POS
        GAME_OVER_POS = self.get_title_pos(GAME_OVER_TITLE)

    def _run(self) -> bool:
        first = True
        while True:
            if config.APP_ASTERIODS_AUTOPLAY and first:
                auto = True
            else:
                menu = self.menu()
                auto = False
                if menu == MENU_NEXT:
                    return False
                elif menu == MENU_QUIT:
                    return True
                elif menu == MENU_PLAY:
                    pass
                elif menu == MENU_AUTO:
                    auto = True
                else:
                    return False
            first = False

            go = self.run_once(auto)
            if go == GOTO_MENU:
                pass
            elif go == GOTO_NEXT:
                return False
            elif go == GOTO_QUIT:
                if auto:
                    return True
                else:
                    continue  # reset during playing returns to menu

    def menu(self) -> int:
        self.show_header('', 'C:next B:start A:auto')
        self.command(f'print \\n')
        self.command(f'print {self.name.upper()} keys:\\n')
        self.command(f'print   C   fire\\n')
        self.command(f'print   B   cntr-clockwise\\n')
        self.command(f'print   A   clockwise\\n')
        self.command(f'print   A+B shield\\n')
        self.command(f'print   R   back to menu\\n\\n')
        # self.command(f'print R:exit  any:start')
        self.command(f'display')

        k = self.board.wait_button_up(MENU_TIMEOUT)
        if 'R' in k:
            return MENU_QUIT
        elif 'C' in k:
            return MENU_NEXT
        elif 'A' in k:
            return MENU_AUTO
        elif k:
            return MENU_PLAY
        return MENU_AUTO

    def run_once(self, autoplay_enabled: bool) -> int:
        game = Game(self, autoplay_enabled)
        autoplay = Autoplay(game, autoplay_enabled)
        overs = 0
        while True:
            keys = self.board.read_buttons()
            if 'R' in keys:
                return GOTO_QUIT
            if autoplay.enabled and keys:
                return GOTO_MENU

            # Erase
            self.command(f'reset')

            # Update / create
            game.update_asteroids()
            game.create_asteroid()
            if autoplay.enabled:
                game.autoplay(keys)
            game.update_ship(keys)
            game.update_shots()

            # Hits
            game.do_detections()

            # Draw
            renders: list[str] = []
            game.add_renders(renders)

            # indicators
            game.add_renders_overlays(renders)

            # show
            for render in renders:
                self.command(render)
            self.command('display')

            now = datetime.datetime.now()
            if autoplay.enabled and autoplay.until and now > autoplay.until:
                return GOTO_NEXT  # exit autoplay

            # crash
            crashed = game.handle_crash()
            if crashed and game.player.lives == 0:
                time.sleep(1)
                if autoplay.enabled:
                    # autoplay crashed
                    return GOTO_NEXT
                else:
                    # player crashed
                    autoplay.enable()
                    self.board.wait_no_button()
