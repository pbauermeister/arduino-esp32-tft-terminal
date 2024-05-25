import time
from typing import Any, Callable

import serial  # pip3 install pyserial

import config
from lib import *
from lib import ArduinoCommExceptions
import sys


class Channel:
    def __init__(
        self,
        port_base: str = config.SERIAL_PORT_BASE,
        baudrate: int = config.SERIAL_BAUDRATE,
    ) -> None:
        self.port_base = port_base
        self.baudrate = baudrate
        self.ser: serial.Serial | None = None
        self.on_message: str | None = None
        self.on_fn: Callable[[Any], None] | None = None

    def open(self) -> None:
        port_nr = 0
        while True:
            try:
                port = f'{self.port_base}{port_nr}'
                print('>open', port)
                self.ser = serial.Serial(port, self.baudrate)
            # except ArduinoCommExceptions as e:
            except ArduinoCommExceptions as e:
                print('>open>error:', e)
                port_nr = (port_nr + 1) % 25
                time.sleep(
                    config.SERIAL_ERROR_RETRY_DELAY
                    if port_nr
                    else config.SERIAL_ERROR_RETRY_DELAY_2
                )
                continue

            self.ser.timeout = config.SERIAL_TIMEOUT
            self.ser.write_timeout = config.SERIAL_TIMEOUT
            self.clear()
            return

    def close(self) -> None:
        assert self.ser
        self.ser.close()

    def clear(self) -> None:
        assert self.ser
        self.ser.flush()
        # self.ser.flushInput()
        # self.ser.flushOutput()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.flush_in()

    def set_callback(self, message: str, fn: Callable[[Any], None] | None) -> None:
        self.on_message = message
        self.on_fn = fn

    def write(self, s: str) -> None:
        if config.DEBUG:
            print('<<<', s)
        # self.ser.write(s.encode(ASCII) + b'\n')
        assert self.ser
        self.ser.write(str.encode(s) + b'\n')

    def read(self) -> str:
        assert self.ser
        bytes = None
        message: str
        try:
            bytes = self.ser.readline()
            message = bytes.decode(ASCII).strip()
        except ArduinoCommExceptions:
            raise
        except Exception as e:
            print('>>>', bytes, ' ###', e)
            return f'ERROR {e}'
        if config.DEBUG:
            print(">>>", message)
        if message == self.on_message:
            if self.on_fn:
                self.on_fn(message)
        return message

    def flush_in(self) -> None:
        assert self.ser
        if config.DEBUG:
            print('>flush> ', end='')
        while True:
            if self.ser.in_waiting:
                try:
                    c = self.ser.read()
                except ArduinoCommExceptions:
                    c = b''
                try:
                    c = c.decode('ascii')
                except:
                    pass
                if config.DEBUG:
                    print(c, end='')
            else:
                time.sleep(0.1)
                if not self.ser.in_waiting:
                    if config.DEBUG:
                        print()
                    return

    def monitor(self) -> None:
        while True:
            print('*', self.port_base, self.baudrate)
            self.open()
            self.write('test')
            print('* opened')
            while True:
                try:
                    message = self.read()
                    print('* msg:', message)
                except Exception as e:
                    print('* exc:', e)
                    break
