#!/usr/bin/env python3
"""Program communicating with Arduino running oled-server.ino."""

import time
import traceback
from typing import Any, Type

import config
from app import App
from app.asteriods import Asteriods
from app.bumps import Bumps
from app.collisions import Collisions
from app.collisions_2 import Collisions_2
from app.cube import Cube
from app.fill import Fill
from app.monitor import Monitor
from app.quix import Quix
from app.road import Road
from app.starfield import Starfield
from app.thats_all import ThatsAll
from app.tunnel import Tunnel
from lib import ArduinoCommExceptions, RebootedException
from lib.args import get_args
from lib.board import Board
from lib.channel import Channel


def make_board(chan: Channel) -> Board:
    try:
        board = Board(chan)
        # board.wait_configured()
        board.clear_buttons()
        return board
    except ArduinoCommExceptions as e:
        try:
            chan.close()
        except:
            pass
        raise


def make_all() -> tuple[Channel, Board]:
    while True:
        try:
            chan = Channel()
            board = make_board(chan)
            return chan, board
        except ArduinoCommExceptions as e:
            print('Serial error:', e)
            print('-- make_all will retry in', config.SERIAL_ERROR_RETRY_DELAY)
            time.sleep(config.SERIAL_ERROR_RETRY_DELAY)

### Here we go ###


# Init
args, only_apps = get_args([
    Asteriods,
    Monitor,
    Cube,
    Road,
    Starfield,
    Tunnel,
    Quix,
    # Bumps,
    Collisions,
    Collisions_2,
    Fill,
])

# Channel().monitor()
chan, board = make_all()


def start_app_maybe(cls: Type[App]) -> bool:
    if only_apps and cls not in only_apps:
        return False
    return cls(board).run()


def suppress_ctrl_c() -> None:
    import signal
    def handler(signum: int, frame: Any) -> None: pass
    signal.signal(signal.SIGINT, handler)


# Cycle through apps
while True:
    try:
        while True:
            if not config.MONITOR_SKIP:
                if Monitor(board).run():
                    break
            if config.MONITOR_ONLY:
                continue
            if not config.APP_ASTERIODS_SKIP:
                if start_app_maybe(Asteriods):
                    break

            if start_app_maybe(Cube):
                break
            if start_app_maybe(Road):
                break
            if start_app_maybe(Starfield):
                break
            if start_app_maybe(Tunnel):
                break
            if start_app_maybe(Quix):
                break
            if start_app_maybe(Bumps):
                break
            if start_app_maybe(Collisions):
                break
            if start_app_maybe(Collisions_2):
                break
            if start_app_maybe(Fill):
                break

            if args.demo_once:
                break

    except RebootedException:
        # restart loop
        pass
    except KeyboardInterrupt:
        print()
        board.fatal('Keyboard interrupt')
        suppress_ctrl_c()
        raise
    except Exception as e:
        msg = traceback.format_exc()
        board.fatal(msg)

    if args.demo_once:
        break

if args.demo:
    ThatsAll(board).run()
