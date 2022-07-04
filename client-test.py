#!/usr/bin/env python3
"""Demo program communicating with Arduino running oled-server.ino."""

import serial  # pip3 install pyserial
import sys
import config
import time
import random

READY = 'READY'
ASCII = 'ASCII'
OK = 'OK'
NONE = 'NONE'

class Channel:
    def __init__(self, port=config.SERIALPORT, baudrate=config.BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.on_message = self.on_fn = None

    def open(self):
        self.ser = serial.Serial(self.port, self.baudrate)
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def set_callback(self, message, fn):
        self.on_message = message
        self.on_fn = fn

    def write(self, s):
        if config.DEBUG: print('<<<', s)
        self.ser.write(s.encode(ASCII) + b'\n')

    def read(self):
        message = self.ser.readline().strip().decode(ASCII)
        if config.DEBUG: print(">>>", message)
        if message == self.on_message:
            self.on_fn(message)
        return message


class Board:
    def __init__(self, channel):
        self.chan = channel
        self.chan.open()
        self.chan.set_callback('READY', self.configure)
        self.configured = False

    def command(self, cmd):
        self.chan.write(cmd)
        response = self.chan.read()
        return response

    def configure(self, _):
        # normally called by callback
        self.command(f'setRotation {config.ROTATION}')
        config.WIDTH = int(self.command(f'width'))
        config.HEIGHT = int(self.command(f'height'))
        self.configured = True

    def wait_configured(self):
        while True:
            if self.configured:
                return
            self.chan.read()
            time.sleep(0.5)

    def monitor(self):
        print('Starting Up Serial Monitor')
        while True:
            for rot in range(4):
                self.command(f'setRotation {rot}')
                self.command('reset')
                self.command('print HELLO\\nWORLD')
            #response = self.chan.read()

    def bumps(self):
        assert config.WIDTH and config.HEIGHT
        sprites = [
            #Sprite(self, 4, -1, -1),
            Sprite(self, 7,  1 , 1),
            Sprite(self, 2,  1, -1),
            Sprite(self, 3, -1,  1),
            Sprite(self, 2, -1, -1),
        ]

        self.command('autoDisplay 0')
        i = 0
        while True:
            for s in sprites:
                s.erase()
            for s in sprites:
                s.advance()

            i += 1
            if i % 10 == 0:
                self.command('home')
                self.command('print Press any key')

            self.command('display')
            #time.sleep(0.06)
            if self.command('readButtons') != NONE:
                break


class Sprite:
    def __init__(self, board, size, vx, vy):
        self.board = board
        self.size = size
        k = .5
        v = (4 + 7**1.25 - size**1.25) * k
        self.x = size if vx > 0 else config.WIDTH-size
        self.y = size if vy > 0 else config.HEIGHT-size

        self.vx, self.vy = vx*v, vy*v
        self.vx0, self.vy0 = abs(vx*v), abs(vy*v)
        self.was_filled = False

    @staticmethod
    def bump(v, v0):
        nv = (1 + (random.random()-.5)/2)*v0
        return nv if v < 0 else -nv

    def erase(self):
        x, y = int(self.x), int(self.y)
        if self.was_filled:
            self.board.command(f'fillCircle {x} {y} {self.size} 0')
        else:
            self.board.command(f'drawCircle {x} {y} {self.size} 0')

    def advance(self):
        filled = False
        self.x += self.vx
        self.y += self.vy
        if self.x >= config.WIDTH - self.size:
            self.x = config.WIDTH - self.size - 1
            self.vx = self.bump(self.vx, self.vx0)
            filled = True
        elif self.x < self.size:
            self.x = self.size
            self.vx = self.bump(self.vx, self.vx0)
            filled = True
        if self.y >= config.HEIGHT - self.size:
            self.y = config.HEIGHT - self.size - 1
            self.vy = self.bump(self.vy, self.vy0)
            filled = True
        elif self.y < self.size:
            self.y = self.size
            self.vy = self.bump(self.vy, self.vy0)
            filled = True

        x, y = int(self.x), int(self.y)
        if filled:
            self.board.command(f'fillCircle {x} {y} {self.size} 1')
        else:
            self.board.command(f'drawCircle {x} {y} {self.size} 1')
        self.was_filled = filled

# Here it goes
chan = Channel()
board = Board(chan)
board.wait_configured()
#board.monitor()
board.bumps()
