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

args = get_args()
chan = Channel()
board = Board(chan)
board.wait_configured()
board.clear_buttons()

while True:
    try:
        while True:
            if not config.MONITOR_SKIP:
                Monitor(board)
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
