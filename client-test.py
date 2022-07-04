#!/usr/bin/env python3
"""Demo program communicating with Arduino running oled-server.ino."""

import serial  # pip3 install pyserial
import sys
import config
import time

READY = 'READY'
ASCII = 'ASCII'
OK = 'OK'


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
        print('<<<', s)
        self.ser.write(s.encode(ASCII) + b'\n')

    def read(self):
        message = self.ser.readline().strip().decode(ASCII)
        print(">>>", message)
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


# Here it goes
chan = Channel()
board = Board(chan)
board.wait_configured()
board.monitor()
