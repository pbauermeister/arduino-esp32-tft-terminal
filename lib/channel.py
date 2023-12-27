import time
from typing import Any, Callable

import serial  # pip3 install pyserial

import config
from lib import *
from lib import ArduinoCommExceptions


class Channel:
    def __init__(self,
                 port_base: str = config.SERIAL_PORT_BASE,
                 baudrate: int = config.SERIAL_BAUDRATE) -> None:
        self.port_base = port_base
        self.baudrate = baudrate
        self.ser: serial.Serial = None
        self.on_message: str = None
        self.on_fn: Callable[[Any], None] = None

    def open(self) -> None:
        port_nr = 0
        while True:
            try:
                port = f'{self.port_base}{port_nr}'
                print('>open', port)
                self.ser = serial.Serial(port, self.baudrate)
            # except ArduinoCommExceptions as e:
            except Exception as e:
                print('>open>error:', e)
                port_nr = (port_nr + 1) % 10
                time.sleep(0.1)
                continue
            self.clear()
            return

    def close(self) -> None:
        self.ser.close()

    def clear(self) -> None:
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.flush_in()

    def set_callback(self, message: str, fn: Callable[[Any], None]) -> None:
        self.on_message = message
        self.on_fn = fn

    def write(self, s: str) -> None:
        if config.DEBUG:
            print('<<<', s)
        # self.ser.write(s.encode(ASCII) + b'\n')
        self.ser.write(str.encode(s) + b'\n')

    def read(self) -> str:
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
            self.on_fn(message)
        return message

    def flush_in(self) -> None:
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
