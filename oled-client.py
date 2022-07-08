#!/usr/bin/env python3
"""Program communicating with Arduino running oled-server.ino."""

import config
import contextlib
import datetime
import math
import os
import random
import serial  # pip3 install pyserial
import sys
import time
import traceback

from lib import *
from lib.args import get_args

from app import App
from app.asteriods import Asteriods
from app.monitor import Monitor
from app.cube import Cube
from app.road import Road
from app.starfield import Starfield
from app.tunnel import Tunnel
from app.quix import Quix

@contextlib.contextmanager
def until(timeout=None):
    start = datetime.datetime.now()
    if timeout is not None:
        until = start + datetime.timedelta(seconds=timeout)
    def done():
        if timeout is None:
            return False
        return datetime.datetime.now() >= until
    yield done


class Channel:
    def __init__(self,
                 port=config.SERIAL_PORT,
                 baudrate=config.SERIAL_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.on_message = self.on_fn = None

    def open(self):
        self.ser = serial.Serial(self.port, self.baudrate)
        self.clear()

    def clear(self):
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.flush_in()

    def set_callback(self, message, fn):
        self.on_message = message
        self.on_fn = fn

    def write(self, s):
        if config.DEBUG: print('<<<', s)
        self.ser.write(s.encode(ASCII) + b'\n')

    def read(self):
        try:
            bytes = self.ser.readline()
            message = bytes.decode(ASCII).strip()
        except Exception as e:
            print('>>>', bytes, ' ###', e)
            return f'ERROR {e}'
        if config.DEBUG: print(">>>", message)
        if message == self.on_message:
            self.on_fn(message)
        return message

    def flush_in(self):
        if config.DEBUG:
            print('>flush> ', end='')
        while True:
            if self.ser.inWaiting():
                c = self.ser.read()
                if config.DEBUG:
                    print(c, end='')
            else:
                time.sleep(0.1)
                if not self.ser.inWaiting():
                    if config.DEBUG:
                        print()
                    return

class Board:
    def __init__(self, channel):
        self.chan = channel
        self.configure_callback = None
        self.chan.open()
        self.chan.set_callback('READY', self.on_ready)
        self.configured = False
        self.boots = 0
        self.last_command = None
        self.reading_buttons = False
        self.auto_buttons = set()
        self.auto_buttons_boots = 0
        self.read_buttons_boots = 0

    def command_send(self, cmd):
        assert not self.reading_buttons
        self.chan.write(cmd)
        self.last_command = cmd

    def command_response(self):
        response = self.chan.read()
        if not config.DEBUG:
            if response.startswith(ERROR) or response.startswith(UNKNOWN):
                print('<<<', self.last_command)
                print('>>>', response)
        assert not response.startswith('ERROR')
        if response.startswith('OK '):
            b = response.split(' ', 1)[1].strip()
            if b != NONE:
                self.auto_buttons |= set(b)
        return response

    def command(self, cmd, ignore_error=False):
        self.command_send(cmd)
        try:
            return self.command_response()
        except:
            if ignore_error:
                return ''
            raise

    def on_ready(self, _=None):
        time.sleep(0.2)
        self.boots += 1
        self.configure()

    def set_configure_callback(self, configure_callback):
        self.configure_callback = configure_callback

    def configure(self):
        # normally called by callback
        try:
            self._configure()
        except:
            self._configure()

    def _configure(self):
        time.sleep(0.1)
        self.chan.clear()
        self.command(f'setRotation {config.SCREEN_ROTATION}')
        self.command('autoDisplay 0')
        self.command('reset')

        w = int(self.command(f'width'))
        h = int(self.command(f'height'))
        if not config.WIDTH:
            config.WIDTH = w
            config.HEIGHT = h
            config.COLUMNS = int(w / 6.4)
            config.ROWS = int(h / 8)
            print(f'OLED resolution:')
            print(f'  pixels: {w} x {h}')
            print(f'  chars:  {config.COLUMNS} x {config.ROWS}')

        if self.configure_callback:
            self.configure_callback()
        self.configured = True

    def wait_configured(self):
        while True:
            if self.configured:
                return
            self.chan.read()
            time.sleep(0.5)

    def begin_read_buttons(self):
        assert not self.reading_buttons
        if config.DEBUG:
            print('* begin_read_buttons')
        self.command_send('waitButton -1 0')
        self.reading_buttons = True
        self.auto_buttons_boots = self.boots

    def end_read_buttons(self):
        assert self.reading_buttons
        if config.DEBUG:
            print('* end_read_buttons')
        self.reading_buttons = False
        self.command_send('width')
        resp = self.command_response()
        self.chan.flush_in()
        if resp == NONE:
            val = set()
        else:
            val = set(resp)
        if self.boots > self.auto_buttons_boots:
            val.add('R')
        if config.DEBUG:
            print('* end_read_buttons done:', val)
        return val

    def wait_no_button(self, timeout=None):
        if timeout is None:
            while self.command('readButtons', ignore_error=True) != NONE:
                pass
        else:
            start = datetime.datetime.now()
            until = start + datetime.timedelta(seconds=timeout)
            while datetime.datetime.now() < until:
                if self.command('readButtons', ignore_error=True) != NONE:
                    break

    def begin_auto_read_buttons(self):
        self.command('autoReadButtons 1')
        if config.DEBUG:
            print('* begin_auto_read_buttons')
        self.auto_buttons = set()
        self.auto_buttons_boots = self.boots

    def auto_read_buttons(self):
        if self.boots > self.auto_buttons_boots:
            self.auto_buttons.add('R')
        b = self.auto_buttons
        self.auto_buttons = set()
        return b

    def end_auto_read_buttons(self):
        self.command('autoReadButtons 0')
        self.chan.flush_in()
        if config.DEBUG:
            print('* end_auto_read_buttons')
        if self.boots > self.auto_buttons_boots:
            self.auto_buttons.add('R')
        return self.auto_buttons

    def clear_buttons(self):
        self.chan.flush_in()
        self.read_buttons_boots = self.boots

    def wait_button_up(self, timeout=None):
        return self.wait_button(timeout, wait_released=True)

    def wait_button(self, timeout=None, wait_released=False):
        self.wait_no_button()
        b = set()
        with until(timeout) as done:
            while not done():
                b = self.read_buttons()
                if b: break
        if wait_released:
            while True:
                b2 = self.read_buttons()
                if not b2: break
                b |= b2
        return b

    def read_buttons(self, flush=False):
        if flush:
            self.chan.flush_in()
            self.read_buttons_boots = self.boots

        ans = self.command('readButtons', ignore_error=True)
        b = set()
        if ans != NONE:
            for c in ans:
                if c in 'ABC':
                    b.add(c)
                else:
                    b = set()
                    break
        if self.boots > self.read_buttons_boots:
            b.add('R')
            self.read_buttons_boots = self.boots
        return b

class Bumps(App):
    def __init__(self, board):
        super().__init__(board)
        sprites = [
            #Sprite(self, 4, -1, -1),
            Sprite(self, 7,  1 , 1),
            Sprite(self, 2,  1, -1),
            Sprite(self, 3, -1,  1),
            Sprite(self, 2, -1, -1),
        ]

        escaper = KeyEscaper(self, self.board, steady_message=False)
        while True:
            for s in sprites:
                s.erase()

            escaper.pre_check()

            for s in sprites:
                s.advance()

            if escaper.check(): break
            self.command('display')



################################################################################
# Helper classes

class RebootedException(Exception):
    pass


class KeyEscaper:
    def __init__(self, app, board, message="Hold a key: next demo",
                 timeout=datetime.timedelta(seconds=60),
                 steady_message=True):
        self.app = app
        self.board = board
        self.message = message
        self.timeout = timeout
        self.steady_message = steady_message
        self.i = -30
        self.n = 0
        self.command = self.board.command
        self.boots = self.board.boots
        self.start = datetime.datetime.now()

    def pre_check(self):
        self.i += 1
        if not self.steady_message and self.i % 80 == 8:
            #self.command('reset')
            self.command(f'fillRect 0 0 {config.WIDTH} 8 0')

    def check(self):
        self.n += 1
        elapsed = datetime.datetime.now() - self.start
        if self.n == 30:
            secs = elapsed.seconds + elapsed.microseconds/1000000
            print(self.app.name, 'FPS:', 30 / secs)
        if self.timeout:
            if elapsed > self.timeout:
                return True
        if self.boots != self.board.boots:
            self.boots = self.board.boots
            raise RebootedException()
        if self.i % 10 == 1:
            if self.command('readButtons', ignore_error=True) != NONE:
                return True
        if self.i % 70 < 8:
            self.command('home')
            self.command(f'print {self.message}')
        return False



def chunkize(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]

def fatal(msg):
    print(msg)
    board.command('home')
    board.command('setTextSize 1')
    board.command('setTextWrap 1')
    board.command(f'fillRect 0, 0, {config.WIDTH} 8 0')
    board.command('reset')

    msg = ' '.join(msg.split())
    msg = msg[-20*8:]
    for chunk in chunkize(msg.replace('\n', ' '), 20):
        board.command(f'print {chunk}')
    board.command('display')
    sys.exit(1)


# Here it goes
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
            Asteriods(board)
            Cube(board)
            Road(board)
            Starfield(board)
            Tunnel(board)
            Quix(board)
            Bumps(board)
    except RebootedException:
        # restart loop
        pass
    except KeyboardInterrupt:
        print()
        fatal('Keyboard interrupt')
        raise
    except Exception as e:
        msg = traceback.format_exc()
        fatal(msg)
