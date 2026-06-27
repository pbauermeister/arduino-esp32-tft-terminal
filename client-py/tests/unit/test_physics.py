"""Tier 1 — Bouncer kinematics and TimeEscaper (seeded / clock-controlled)."""

import datetime
import random

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.app import Bouncer, TimeEscaper


def _set_screen() -> None:
    config.WIDTH = 240
    config.HEIGHT = 135


def test_bouncer_advances_position() -> None:
    _set_screen()
    random.seed(0)
    b = Bouncer(size=5, vx=1, vy=1)
    before = (b.xx, b.yy)
    b.advance()
    assert (b.xx, b.yy) != before


def test_bouncer_reflects_at_right_wall() -> None:
    _set_screen()
    random.seed(0)
    b = Bouncer(size=5, vx=1, vy=1)  # moving right (vx > 0)
    b.xx = config.WIDTH  # park it past the right edge
    b.advance()
    assert b.bumped
    assert b.vx < 0  # velocity reflected inward


class _StubApp:
    def __init__(self, only_me: bool) -> None:
        self.only_me = only_me
        self.name = 'stub'


def test_time_escaper_times_out() -> None:
    esc = TimeEscaper(_StubApp(only_me=False), timeout=1)
    esc.start = datetime.datetime.now() - datetime.timedelta(seconds=100)
    assert esc.check() is True


def test_time_escaper_only_me_never_times_out() -> None:
    esc = TimeEscaper(_StubApp(only_me=True), timeout=1)
    esc.start = datetime.datetime.now() - datetime.timedelta(seconds=100)
    assert esc.check() is False
