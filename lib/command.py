import time
from abc import abstractmethod
from typing import Callable

import config
from lib import *

from .channel import Channel

import sys


class Command:
    def __init__(self, channel: Channel):
        self.chan = channel
        self.comm_error_handler: Callable[[], None] | None = None
        self.auto_btn_handler:  Callable[[set[str]], None] | None = None
        self.recoveries = 0

    def had_recoveries(self) -> bool:
        had = self.recoveries > 0
        self.recoveries = 0
        return had

    def set_comm_error_handler(self, handler: Callable[[], None]) -> None:
        self.comm_error_handler = handler

    def set_auto_btn_handler(self, handler: Callable[[set[str]], None]) -> None:
        self.auto_btn_handler = handler

    def do_command(self, cmd: str, ignore_error: bool = False) -> str:
        # Since the board may be rebooted in the middle of a command,
        # it is okay to retry once
        try:
            return self._send_command(cmd, ignore_error)
        except:
            self.chan.clear()
            return self._send_command(cmd, ignore_error)

    def _send_command(self, cmd: str, ignore_error: bool = False) -> str:
        delay = config.SERIAL_ERROR_RETRY_DELAY
        while True:
            try:
                self.command_send(cmd)
                return self.command_response()
            except ArduinoCommExceptions as e:
                print('Serial error:', e)
                self.recover()
                if ignore_error:
                    return ''

    def recover(self) -> None:
        delay = config.SERIAL_ERROR_RETRY_DELAY
        try:
            self.chan.close()
        except:
            pass

        self.chan.open()

        if not self.comm_error_handler:
            print('Re-open OK.')
        else:
            self.comm_error_handler()
            print('Re-init OK.')
            self.recoveries += 1

    def command_send(self, cmd: str) -> None:
        # assert not self.reading_buttons
        self.chan.write(cmd)
        self.last_command = cmd

    def command_response(self) -> str:
        response = ''
        while True:
            response = self.chan.read()
            if response.startswith('#'):
                # if config.DEBUG:
                print('>>>', response)
            else:
                break

        if not config.DEBUG:
            if response.startswith(ERROR) or response.startswith(UNKNOWN):
                print('<<<', self.last_command)
                print('>>>', response)
        assert not response.startswith('ERROR')
        if response.startswith('OK '):
            b = response.split(' ', 1)[1].strip()
            if b != NONE and self.auto_btn_handler is not None:
                self.auto_btn_handler(set(b))
        return response
