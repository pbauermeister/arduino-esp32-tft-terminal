#!/usr/bin/env python3
"""Program communicating with Arduino running oled-server.ino."""

import time
import traceback
from typing import Any, Type

import config
from app import App
from app.asteriods import Asteriods

# from app.bumps import Bumps
from app.collisions import CollisionsElastic
from app.collisions2 import CollisionsGravity
from app.collisions3 import BubblesSoap
from app.collisions4 import BubblesAir
from app.cube import Cube
from app.fill import Fill
from app.monitor_cpus import MonitorCpus
from app.monitor_graph import MonitorGraph
from app.monitor_host import MonitorHost
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

all_apps = [
    MonitorHost,
    MonitorCpus,
    MonitorGraph,
    Asteriods,
    Cube,
    # Road,
    Starfield,
    Tunnel,
    Quix,
    # Bumps,
    CollisionsElastic,
    CollisionsGravity,
    BubblesSoap,
    BubblesAir,
    Fill,
]

# Init
args, apps = get_args(all_apps)

# Channel().monitor()
chan, board = make_all()


def start_app(cls: Type[App], only_me: bool) -> bool:
    instance = cls(board)
    instance.only_me = only_me

    while True:
        try:
            return instance.run()
        except ArduinoCommExceptions as e:
            print('Serial error:', e)
            time.sleep(1)
            print('Please reset the board.')


def suppress_ctrl_c() -> None:
    import signal

    def handler(signum: int, frame: Any) -> None:
        pass

    signal.signal(signal.SIGINT, handler)


# Cycle through apps
while True:
    try:
        while True:
            for app in apps:
                start_app(app, len(apps) == 1)

            if args.once:
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

    if args.once:
        break

if args.once:
    ThatsAll(board).run()
