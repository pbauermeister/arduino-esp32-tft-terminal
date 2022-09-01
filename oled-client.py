#!/usr/bin/env python3
"""Program communicating with Arduino running oled-server.ino."""

import config
import datetime
import math
import os
import random
import sys
import time
import traceback

from lib import *
from lib.args import get_args
from lib.channel import Channel
from lib.board import Board

from app import App
from app.asteriods import Asteriods
from app.monitor import Monitor
from app.cube import Cube
from app.road import Road
from app.starfield import Starfield
from app.tunnel import Tunnel
from app.quix import Quix
from app.bumps import Bumps
from app.fill import Fill
from app.thats_all import ThatsAll


def make_board(chan):
    try:
        board = Board(chan)
        board.wait_configured()
        board.clear_buttons()
        return board
    except ArduinoCommExceptions as e:
        try: board.close()
        except: pass
        raise

def make_all():
    while True:
        try:
            chan = Channel()
            board = make_board(chan)
            return chan, board
        except ArduinoCommExceptions as e:
            print('Serial error:', e)
            print('-- will retry in', config.SERIAL_ERROR_RETRY_DELAY)
            time.sleep(config.SERIAL_ERROR_RETRY_DELAY)

### Here we go ###

# Init
args, only_apps = get_args(
    Asteriods,
    Monitor,
    Cube,
    Road,
    Starfield,
    Tunnel,
    Quix,
    Bumps,
    Fill,
    )
chan, board = make_all()


def start_app_maybe(cls):
    if only_apps and cls not in only_apps: return False
    return cls(board).run()


# Cycle through apps
while True:
    try:
        while True:
            if not config.MONITOR_SKIP:
                Monitor(board).run()
            if config.MONITOR_ONLY:
                continue
            if not config.APP_ASTERIODS_SKIP:
                if start_app_maybe(Asteriods): break

            if start_app_maybe(Cube): break
            if start_app_maybe(Road): break
            if start_app_maybe(Starfield): break
            if start_app_maybe(Tunnel): break
            if start_app_maybe(Quix): break
            if start_app_maybe(Bumps): break
            if start_app_maybe(Fill): break

            if args.demo_once: break

    except RebootedException:
        # restart loop
        pass
    except KeyboardInterrupt:
        print()
        fatal(board, 'Keyboard interrupt')
        raise
    except Exception as e:
        msg = traceback.format_exc()
        fatal(board, msg)

    if args.demo_once: break

if args.demo:
    ThatsAll(board).run()
