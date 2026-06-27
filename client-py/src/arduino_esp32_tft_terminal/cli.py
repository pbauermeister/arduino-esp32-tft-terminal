#!/usr/bin/env python3
"""Program communicating with Arduino running oled-server.ino."""

import time
import traceback
from typing import Any, Type

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.app import App
from arduino_esp32_tft_terminal.app.asteriods import Asteriods
from arduino_esp32_tft_terminal.app.claude_mon import ClaudeMonitor

# from app.bumps import Bumps
from arduino_esp32_tft_terminal.app.collisions import CollisionsElastic
from arduino_esp32_tft_terminal.app.collisions2 import CollisionsGravity
from arduino_esp32_tft_terminal.app.collisions3 import BubblesSoap
from arduino_esp32_tft_terminal.app.collisions4 import BubblesAir
from arduino_esp32_tft_terminal.app.cube import Cube
from arduino_esp32_tft_terminal.app.fill import Fill
from arduino_esp32_tft_terminal.app.monitor_cpus import MonitorCpus
from arduino_esp32_tft_terminal.app.monitor_graph import MonitorGraph
from arduino_esp32_tft_terminal.app.monitor_host import MonitorHost
from arduino_esp32_tft_terminal.app.quix import Quix
from arduino_esp32_tft_terminal.app.starfield import Starfield
from arduino_esp32_tft_terminal.app.thats_all import ThatsAll
from arduino_esp32_tft_terminal.app.tunnel import Tunnel
from arduino_esp32_tft_terminal.lib import ArduinoCommExceptions, RebootedException
from arduino_esp32_tft_terminal.lib.args import get_args
from arduino_esp32_tft_terminal.lib.board import Board
from arduino_esp32_tft_terminal.lib.channel import Channel


def make_board(chan: Channel) -> Board:
    try:
        board = Board(chan)
        # board.wait_configured()
        board.clear_buttons()
        return board
    except ArduinoCommExceptions:
        try:
            chan.close()
        except Exception:
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
    ClaudeMonitor,
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


def start_app(cls: Type[App], only_me: bool, board: Board) -> bool:
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


def main() -> None:
    args, apps = get_args(all_apps)
    _chan, board = make_all()

    # Cycle through apps
    while True:
        try:
            while True:
                for app in apps:
                    start_app(app, len(apps) == 1, board)

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
        except Exception:
            msg = traceback.format_exc()
            board.fatal(msg)

        if args.once:
            break

    if args.once:
        ThatsAll(board).run()


if __name__ == '__main__':
    main()
