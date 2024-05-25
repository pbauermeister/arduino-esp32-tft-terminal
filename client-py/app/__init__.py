import re
import datetime
import random
import time
from abc import abstractmethod
from typing import Callable

import config
from lib.board import Board

CAMEL_RX = re.compile('([a-z][A-Z0-9])')


class App:
    def __init__(
        self,
        board: Board,
        auto_read: bool = False,
        extra_configurator: Callable[[], None] | None = None,
        name: str | None = None,
    ) -> None:
        self.board = board
        self.gfx = board.gfx
        self.name = name or self.__class__.__name__
        self.title = camel_to_title(self.name)
        print(f'== {self.title} ==')
        self.board.set_comm_error_handler(self.init)
        self.auto_read = auto_read
        self.extra_configurator = extra_configurator
        board.set_configure_callback(extra_configurator)
        self.text_bound_cache: dict[str, tuple[int, int]] = {}
        self.board.clear_buttons()
        self.board.command.had_recoveries()
        self.only_me = False
        self.init()
        self.show_main_title()

    @abstractmethod
    def _run(self) -> bool:
        return False

    def run(self) -> bool:
        if self.board.read_buttons(flush=True):
            return False
        start = datetime.datetime.now()
        reset = False
        if not self.board.wait_no_button(config.APPS_TITLE_DURATION):
            self.gfx.reset()
            reset = self._run()
            if self.auto_read:
                reset = reset or 'R' in self.board.end_auto_read_buttons()
        self.board.set_comm_error_handler(self.init)
        self.board.set_configure_callback(None)
        duration = datetime.datetime.now() - start
        print('Duration:', duration)
        while self.board.read_buttons(flush=True):
            time.sleep(0.1)
            pass
        return reset

    def init(self) -> None:
        self.board.set_comm_error_handler(self.init)
        self.board.configure()
        assert config.WIDTH and config.HEIGHT

        # ready for run()
        self.gfx.set_text_size(1, 1)
        if self.auto_read:
            self.board.begin_auto_read_buttons()

    def show_main_title(self) -> None:
        self.gfx.reset()
        self.gfx.set_text_size(1, 2)
        title = self.title.upper()
        x, y = self.get_title_pos(title)

        # title
        self.gfx.set_cursor(x, y)
        self.gfx.print(title)
        self.gfx.display()

    def get_title_pos(self, title: str) -> tuple[int, int]:
        w, h = self.get_text_size(title)
        x = int(config.WIDTH / 2 - w / 2 + 0.5)
        y = int(config.HEIGHT / 2 - h / 2 + 0.5)
        return x, y

    def get_text_size(self, text: str) -> tuple[int, int]:
        res = self.text_bound_cache.get(text)
        if res is None:
            res = self.gfx.get_text_bounds(0, 0, text)
            self.text_bound_cache[text] = res
        return res

    def show_header(self, title: str, menu: str, with_banner: bool = False) -> None:
        self.gfx.clear()
        self.gfx.set_text_size(1, 1)
        self.gfx.fill_rect(0, 0, config.WIDTH, config.TEXT_SCALING * 8, 1)
        self.gfx.set_text_color(0, 0, 0)
        self.gfx.set_cursor(1, 0)
        self.gfx.print(title)

        w, h = self.get_text_size(menu)
        x = max(config.WIDTH - w - 3, 0)
        self.gfx.set_cursor(x, 1)
        self.gfx.print(menu)
        self.gfx.set_text_color(255, 255, 255)

        if with_banner:
            self.gfx.set_text_size(1, 2)
            self.show_title(title)
            self.gfx.display()
            self.gfx.set_text_size(1, 2)
        else:
            self.gfx.home()
            self.gfx.print('\\n')

    def show_title(self, title: str) -> None:
        x, y = self.get_title_pos(title)
        self.gfx.set_cursor(x, y)
        self.gfx.print(title)


class TimeEscaper:
    def __init__(self, app: App, timeout: int | None = None) -> None:
        self.app = app
        if timeout is None:
            timeout = config.APPS_TIMEOUT  # config is patched, so not in ctor
        self.timeout = datetime.timedelta(seconds=timeout)
        self.frames = 0
        self.start = datetime.datetime.now()

    def retrigger(self) -> None:
        self.start = datetime.datetime.now()

    def check(self) -> bool:
        self.frames += 1
        elapsed = datetime.datetime.now() - self.start
        nf = 30
        if self.frames == nf:
            secs = elapsed.seconds + elapsed.microseconds / 1000000
            print(self.app.name, 'FPS:', nf / secs)
        if self.app.only_me:
            return False
        if self.timeout:
            if elapsed > self.timeout:
                return True
        return False


class Bouncer:
    def __init__(self, size: int, vx: float, vy: float) -> None:
        self.size = size
        k = 0.5
        v: float = (4 + 7**1.25 - size**1.25) * k
        self.xx: float = size if vx > 0 else config.WIDTH - size
        self.yy: float = size if vy > 0 else config.HEIGHT - size

        self.x, self.y = int(self.xx + 0.5), int(self.yy + 0.5)

        self.vx, self.vy = vx * v, vy * v
        self.vx0, self.vy0 = abs(vx * v), abs(vy * v)

        self.bumped = False

    @staticmethod
    def bump(v: float, v0: float) -> float:
        nv = (1 + (random.random() - 0.5) / 2) * v0
        return nv if v < 0 else -nv

    def advance(self) -> None:
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
        self.x, self.y = int(self.xx + 0.5), int(self.yy + 0.5)


class Sprite(Bouncer):
    def __init__(self, app: App, size: int, vx: float, vy: float) -> None:
        super().__init__(size, vx, vy)
        self.app = app
        self.was_filled = False

    def erase(self) -> None:
        if self.was_filled:
            self.app.gfx.fill_circle(self.x, self.y, self.size, 0)
        else:
            self.app.gfx.draw_circle(self.x, self.y, self.size, 0)

    def advance(self) -> None:
        super().advance()
        if self.bumped:
            self.app.gfx.fill_circle(self.x, self.y, self.size, 1)
        else:
            self.app.gfx.draw_circle(self.x, self.y, self.size, 1)
        self.was_filled = self.bumped


def camel_to_snake(s: str) -> str:
    def replacer(m: re.Match[str]) -> str:
        s = m[1]
        return f'{s[0]}_{s[1]}'

    return CAMEL_RX.sub(replacer, s).lower()


def camel_to_kebab(s: str) -> str:
    def replacer(m: re.Match[str]) -> str:
        s = m[1]
        return f'{s[0]}-{s[1]}'

    return CAMEL_RX.sub(replacer, s).lower()


def camel_to_title(s: str) -> str:
    def replacer(m: re.Match[str]) -> str:
        s = m[1]
        return f'{s[0]} {s[1]}'

    return CAMEL_RX.sub(replacer, s)
