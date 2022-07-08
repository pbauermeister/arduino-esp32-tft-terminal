import config
import serial  # pip3 install pyserial
import time

from lib import *


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
