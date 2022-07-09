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
args = get_args()
chan, board = make_all()

# Cycle through apps
while True:
    try:
        while True:
            if not config.MONITOR_SKIP:
                Monitor(board).run()
            if config.MONITOR_ONLY:
                continue

            if not config.APP_ASTERIODS_SKIP:
                if Asteriods(board).run(): break

            if Cube(board).run(): break
            if Road(board).run(): break
            if Starfield(board).run(): break
            if Tunnel(board).run(): break
            if Quix(board).run(): break
            if Bumps(board).run(): break
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
