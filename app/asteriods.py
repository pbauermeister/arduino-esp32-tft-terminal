import datetime
import math
import random
import time
from dataclasses import dataclass

import config
from app import App
from lib.board import Board
from lib.gfx import Gfx

# Parameters
SHIP_RADIUS = 8 * config.GFX_SCALING
SHIP_SPEED = 2
SHIP_ROT_STEP = .2

SHOT_SPEED = 5
SHOT_DELAY = 2*2
SHOT_MAX = 10

ASTEROID_NB_MAX = 8*2
ASTEROID_RADIUS = 2*config.GFX_SCALING, 18*config.GFX_SCALING
ASTEROID_RADIUS_MEAN = sum(ASTEROID_RADIUS)/2
ASTEROID_SPLIT_A = .4*2  # angle
ASTEROID_SHRINK_FACTOR = .8

SHIELD_DURATION = 12
SHIELD_TIMEOUT = 20
SHIELD_RADIUS = SHIP_RADIUS + 6*config.GFX_SCALING

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

KEY_CW = 'C'
KEY_CCW = 'A'
KEY_FIRE = 'B'
KEY_SHIELD1 = 'A'
KEY_SHIELD2 = 'B'


class Shot:
    def __init__(self, gfx: Gfx, x: float, y: float, vx: float, vy: float):
        self.gfx = gfx
        self.x, self.y, self.vx, self.vy = x, y, vx, vy

    def move(self) -> None:
        self.x += self.vx
        self.y += self.vy

    def valid(self) -> bool:
        return \
            self.x >= 0 and self.x < config.WIDTH and \
            self.y >= 0 and self.y < config.HEIGHT

    def add_renders(self) -> None:
        self.gfx.set_fg_color(255, 64, 0)
        self.gfx.draw_pixel(int(self.x + .5), int(self.y + .5), 1)
        self.gfx.set_fg_color(255, 255, 255)


class Ship:
    def __init__(self, gfx: Gfx) -> None:
        self.gfx = gfx
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
        self.aster_crash: Asteroid | None = None
        self.reloading = 0

    def move(self, keys: set[str]) -> None:
        v = self.v
        # rotate & advance
        if KEY_SHIELD1 in keys and KEY_SHIELD2 in keys:
            if self.shield < -SHIELD_TIMEOUT:
                self.shield = SHIELD_DURATION
        elif KEY_CCW in keys:
            self.a -= SHIP_ROT_STEP
            v = self.v/2
        elif KEY_CW in keys:
            self.a += SHIP_ROT_STEP
            v = self.v/2
        if KEY_FIRE in keys:
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
        self.x0 = self.r*self.ca + self.x
        self.y0 = self.r*self.sa + self.y

        b = self.a + math.pi * .8
        self.x1 = self.r*math.cos(b) + self.x
        self.y1 = self.r*math.sin(b) + self.y

        b = self.a + math.pi * 1.2
        self.x2 = self.r*math.cos(b) + self.x
        self.y2 = self.r*math.sin(b) + self.y

    def shoot(self, shots: list[Shot]) -> None:
        if self.shield > 0:
            return
        if self.shot_reload <= SHOT_DELAY:
            return
        if len(shots) >= SHOT_MAX:
            return
        vx, vy = self.ca*SHOT_SPEED, self.sa*SHOT_SPEED
        shot = Shot(self.gfx, self.x0, self.y0, vx, vy)
        shots.append(shot)
        shot = Shot(self.gfx, self.x0+vx*3, self.y0+vy*3, vx, vy)
        shots.append(shot)
        self.shot_reload = 0

    def add_renders(self) -> None:
        x0 = int(self.x0 + .5)
        y0 = int(self.y0 + .5)
        x1 = int(self.x1 + .5)
        y1 = int(self.y1 + .5)
        x2 = int(self.x2 + .5)
        y2 = int(self.y2 + .5)
        self.gfx.draw_triangle(x0, y0, x1, y1, x2, y2, 1)

        if self.shield > 0:
            if self.protect:
                r = SHIELD_RADIUS
            else:
                r = SHIELD_RADIUS - 3 + (self.i % 3)*3
            x = int(self.x + .5)
            y = int(self.y + .5)
            self.gfx.set_fg_color(64, 64, 255)
            self.gfx.draw_circle(x, y, r, 1)
            self.gfx.set_fg_color(255, 255, 255)

    def add_renders_boom(self, i: int) -> None:
        x0 = int(self.x0 + .5)
        y0 = int(self.y0 + .5)
        x1 = int(self.x1 + .5)
        y1 = int(self.y1 + .5)
        x2 = int(self.x2 + .5)
        y2 = int(self.y2 + .5)

        c = i % 2
        self.gfx.set_fg_color(255, 64, 64)
        self.gfx.fill_triangle(x0, y0, x1, y1, x2, y2, c)
        self.gfx.draw_triangle(x0, y0, x1, y1, x2, y2, c)
        self.gfx.set_fg_color(255, 255, 255)


class Player:
    def __init__(self, gfx: Gfx, autoplay_enabled: bool):
        self.ship = Ship(gfx)
        self.lives = LIVES
        self.autoplay_enabled = autoplay_enabled
        self.score = 0


@dataclass
class AsteriodData:
    x: float
    y: float
    r: float
    a: float
    hit: bool


class Asteroid(AsteriodData):
    def __init__(self, gfx: Gfx, ship: Ship | None = None, other: AsteriodData | None = None):
        self.gfx = gfx
        if ship is not None:
            self.init(ship.x, ship.y)
        elif other is not None:
            self.x = other.x
            self.y = other.y
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

        self.x = x
        self.y = y
        self.r = int(r+.5)
        self.a = a
        self.hit = False

    def move(self, dist: float | None = None) -> None:
        if dist is None:
            v = max((ASTEROID_RADIUS[1] - self.r)**1.4 / 6, .5)
            dist = v
        vx = math.cos(self.a) * (dist or 0)
        vy = math.sin(self.a) * (dist or 0)

        self.x += vx
        self.y += vy

        # wrap around
        if self.x < -self.r:
            self.x = config.WIDTH + self.r
        if self.x > config.WIDTH + self.r:
            self.x = -self.r
        if self.y < -self.r:
            self.y = config.HEIGHT + self.r
        if self.y > config.HEIGHT + self.r:
            self.y = -self.r

    def shrink(self) -> None:
        self.r = int(self.r*ASTEROID_SHRINK_FACTOR + .5)
        if self.r < 4:
            self.r = 0

    def add_renders(self) -> None:
        x = int(self.x + .5)
        y = int(self.y + .5)
        r = int(self.r + .5)
        if self.hit:
            self.gfx.set_fg_color(255, 64, 64)
            self.gfx.fill_circle(x, y, r, 1)
            self.gfx.set_fg_color(255, 255, 255)
        else:
            self.gfx.draw_circle(x, y, r, 1)

    def add_renders_boom(self, i: int) -> None:
        x = int(self.x + .5)
        y = int(self.y + .5)
        r = int(self.r + .5)

        c = i % 2
        self.gfx.set_fg_color(255, 64, 64)
        self.gfx.fill_circle(x, y, r, c)
        self.gfx.set_fg_color(255, 255, 255)
        # self.gfx.draw_circle(x, y, r, c)


@dataclass
class Bonus:
    x: int
    y: int
    value: int

    def render(self, gfx: Gfx) -> None:
        gfx.set_cursor(self.x + config.TEXT_SCALING*2,
                       self.y - config.TEXT_SCALING*4)
        # gfx.set_fg_color(96, 96, 192)
        gfx.set_fg_color(255, 64, 0)
        gfx.set_text_color(1)
        gfx.print(str(self.value))
        gfx.set_fg_color(255, 255, 255)


class Game:
    def __init__(self, app: App, autoplay_enabled: bool):
        self.app = app
        self.gfx = app.gfx
        self.player = Player(self.gfx, autoplay_enabled)
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
        if len(self.asteroids) >= ASTEROID_NB_MAX:
            return
        if random.random() > .05:
            return
        self.asteroids.append(Asteroid(self.gfx, ship=self.player.ship))

    def autoplay(self, keys: set[str]) -> None:
        p = random.random()
        if p < .1:
            if len(self.asteroids):
                keys.add(KEY_FIRE)
        elif p < .2:
            keys.add(KEY_CW)
        elif p < .4:
            keys.add(KEY_CCW)

        x, y, r = self.player.ship.x, self.player.ship.y, SHIELD_RADIUS
        for a in self.asteroids:
            if Detect.touch(x, y, a.x, a.y, r, a.r):
                # try shield
                keys.add(KEY_SHIELD1)
                keys.add(KEY_SHIELD2)

    def update_ship(self, keys: set[str]) -> None:
        shoot = KEY_FIRE in keys
        self.player.ship.move(keys)
        if shoot:
            self.player.ship.shoot(self.shots)

    def update_shots(self) -> None:
        for shot in self.shots:
            shot.move()
            if not shot.valid():
                self.shots.remove(shot)

    def do_detections(self) -> list[Bonus]:
        bonuses = Detect.hits(self.gfx, self.shots, self.asteroids)
        Detect.collisions(self.asteroids)
        Detect.crash(self.player.ship, self.asteroids)
        return bonuses

    def add_renders(self) -> None:
        self.player.ship.add_renders()
        for a in self.asteroids:
            a.add_renders()
        for shot in self.shots:
            shot.add_renders()

    def add_renders_overlays(self) -> None:
        self.gfx.set_text_size(1, 1)
        if self.player.autoplay_enabled:
            self.gfx.set_fg_color(64, 64, 64)
            self.gfx.set_text_color(1)
            x, y = GAME_OVER_POS
            self.gfx.set_cursor(x, y)
            self.gfx.print(GAME_OVER_TITLE)

        x = config.WIDTH - 12*config.TEXT_SCALING
        self.gfx.set_cursor(x, 0)
        self.gfx.set_fg_color(96, 96, 192)
        self.gfx.set_text_color(1)
        self.gfx.print(str(self.player.lives))

        self.gfx.set_fg_color(255, 255, 255)
        if self.player.ship.aster_crash:
            return

        if self.player.ship.reloading:
            r = self.player.ship.reloading
            self.gfx.home()
            self.gfx.print(f'Shield in {r}')
        elif self.player.ship.shield > 0 and not self.player.ship.protect:
            self.gfx.home()
            self.gfx.print('Shield')
        else:
            self.gfx.home()
            self.gfx.print(f'{self.player.score:04d}')

    def handle_crash(self) -> bool:
        if not self.player.ship.aster_crash:
            return False
        self.gfx.set_fg_color(255, 64, 64)
        self.gfx.set_text_color(1)
        self.boom(self.player.ship, self.player.ship.aster_crash)
        self.player.ship.aster_crash = None
        if self.player.lives:
            self.player.lives -= 1
        self.gfx.set_fg_color(255, 255, 255)
        self.gfx.set_text_color(1)
        return True

    def boom(self, ship: Ship, asteroid: Asteroid) -> None:
        self.gfx.home()
        self.gfx.print('Boom!')
        for i in range(9):
            asteroid.add_renders_boom(i)
            ship.add_renders_boom(i)
            self.gfx.display()
            time.sleep(0.05)
        ship.protect = PROTECT_DURATION
        ship.shield = SHIELD_DURATION


class Detect:
    @staticmethod
    def hits(gfx: Gfx, shots: list[Shot], asteroids: list[Asteroid]) -> list[Bonus]:
        bonuses: list[Bonus] = []
        if not shots or not asteroids:
            return []
        for a in asteroids:
            for s in shots:
                if Detect.hit(s.x, s.y, a, .75):
                    shots.remove(s)
                    a.hit = True
                    points = int(ASTEROID_RADIUS[1]-a.r) + 1
                    bonuses.append(Bonus(int(a.x + a.r), int(a.y), points))

                    if a.r >= ASTEROID_RADIUS_MEAN:
                        # a.r = int(a.r * .67 + .5)

                        # split in two
                        a1 = Asteroid(gfx, other=a)
                        a1.a += ASTEROID_SPLIT_A
                        a1.move(a1.r/2)
                        asteroids.append(a1)

                        a2 = Asteroid(gfx, other=a)
                        a2.a -= ASTEROID_SPLIT_A
                        a2.move(a2.r/2)
                        asteroids.append(a2)

                        if a in asteroids:
                            asteroids.remove(a)
                    continue
        return bonuses

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
        for a in asteroids:
            for b in asteroids:
                if a is b:
                    continue
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
        self.start: datetime.datetime | None = None
        self.until: datetime.datetime | None = None
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
        self.gfx.set_text_wrap_off()

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
                    return True  # first app
                else:
                    continue  # reset during playing returns to menu

    def menu(self) -> int:
        self.show_header('', 'C:next B:play A:demo')
        self.gfx.print(f'\\n')
        self.gfx.print(f'{self.name.upper()} keys:\\n')
        self.gfx.print(f' {KEY_FIRE}   fire\\n')
        self.gfx.print(f' {KEY_CCW}   cntr-clockwise\\n')
        self.gfx.print(f' {KEY_CW}   clockwise\\n')
        self.gfx.print(f' {KEY_SHIELD1}+{KEY_SHIELD2} shield\\n')
        self.gfx.display()

        k = self.board.wait_button_up(MENU_TIMEOUT)
        if 'R' in k:
            return MENU_QUIT
        elif 'C' in k:
            return MENU_NEXT
        elif 'A' in k:
            return MENU_AUTO
        elif 'B' in k:
            return MENU_PLAY
        return MENU_AUTO

    def run_once(self, autoplay_enabled: bool) -> int:
        game = Game(self, autoplay_enabled)
        autoplay = Autoplay(game, autoplay_enabled)
        self.gfx.reset()
        while True:
            keys = self.board.read_buttons()
            if 'R' in keys:
                return GOTO_QUIT
            if autoplay.enabled and keys:
                return GOTO_MENU

            # Erase
            self.gfx.clear()

            # Update / create
            game.update_asteroids()
            game.create_asteroid()
            if autoplay.enabled:
                game.autoplay(keys)
            game.update_ship(keys)
            game.update_shots()

            # Hits
            bonuses = game.do_detections()

            # Draw

            # - indicators
            game.add_renders_overlays()

            # - objects
            game.add_renders()

            for bonus in bonuses:
                game.player.score += bonus.value
                bonus.render(self.gfx)

            # - show
            self.gfx.display()

            now = datetime.datetime.now()
            if autoplay.enabled and autoplay.until and now > autoplay.until:
                return GOTO_NEXT  # exit autoplay

            # Crash
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
            # time.sleep(1*10000)
