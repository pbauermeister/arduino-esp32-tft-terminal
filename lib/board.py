import datetime
import sys
import time
from typing import Any, Callable

import config
from lib import *
from lib.gfx import Gfx

from .channel import Channel


class Board:
    def __init__(self, channel: Channel) -> None:
        self.gfx = Gfx(self.do_command)
        self.chan = channel
        self.configure_callback: Callable[[], None] | None = None
        self.comm_error_handler: Callable[[], None] | None = None
        self.configured = False
        self.boots = 0
        self.last_command: str | None = None
        self.reading_buttons = False
        self.auto_buttons: set[str] = set()
        self.auto_buttons_boots = 0
        self.read_buttons_boots = 0

        self.chan.open()
        self.chan.set_callback('READY', self.on_ready)

    def set_configure_callback(self, configure_callback: Callable[[], None] | None) -> None:
        self.configure_callback = configure_callback

    def set_comm_error_handler(self, handler: Callable[[], None]) -> None:
        self.comm_error_handler = handler

    def close(self) -> None:
        self.chan.close()

    def reopen(self) -> None:
        self.chan.open()

    def send_command(self, cmd: str, ignore_error: bool = False) -> str:
        delay = config.SERIAL_ERROR_RETRY_DELAY
        while True:
            try:
                return self._command(cmd, ignore_error)
            except ArduinoCommExceptions as e:
                print('Serial error:', e)
                self.close()
                while True:
                    print('-- Board.command will retry in', delay)
                    time.sleep(delay)
                    try:
                        self.reopen()
                        if not self.comm_error_handler:
                            print('Re-open OK.')
                        else:
                            self.comm_error_handler()
                            print('Re-init OK.')
                        break
                    except ArduinoCommExceptions as e:
                        print('Error:', e)

    def _command(self, cmd: str, ignore_error: bool = False) -> str:
        self._command_send(cmd)
        try:
            return self._command_response()
        except:
            if ignore_error:
                return ''
            raise

    def _command_send(self, cmd: str) -> None:
        assert not self.reading_buttons
        self.chan.write(cmd)
        self.last_command = cmd

    def _command_response(self) -> str:
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

    def on_ready(self, _: Any = None) -> None:
        time.sleep(0.2)
        self.boots += 1
        self.configure()

    def configure(self) -> None:
        # normally called by callback
        try:
            self._configure()
        except:
            self._configure()

    def _configure(self) -> None:
        time.sleep(0.1)
        self.chan.clear()
        self.gfx.set_rotation(config.SCREEN_ROTATION)
        self.gfx.set_auto_display_off()
        self.gfx.reset()

        w = self.gfx.get_width()
        h = self.gfx.get_height()
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

    def wait_configured(self) -> None:
        while True:
            if self.configured:
                return
            self.chan.read()
            time.sleep(0.5)

    def begin_read_buttons(self) -> None:
        assert not self.reading_buttons
        if config.DEBUG:
            print('* begin_read_buttons')
        self._command_send('waitButton -1 0')
        self.reading_buttons = True
        self.auto_buttons_boots = self.boots

    def end_read_buttons(self) -> set[str]:
        assert self.reading_buttons
        if config.DEBUG:
            print('* end_read_buttons')
        self.reading_buttons = False
        self._command_send('width')
        resp = self._command_response()
        self.chan.flush_in()
        val: set[str]
        if resp == NONE:
            val = set()
        else:
            val = set(resp)
        if self.boots > self.auto_buttons_boots:
            val.add('R')
        if config.DEBUG:
            print('* end_read_buttons done:', val)
        return val

    def wait_no_button(self, timeout: int | None = None) -> bool:
        self.chan.flush_in()
        if timeout is None:
            while self.gfx.read_buttons() != NONE:
                pass
        else:
            start = datetime.datetime.now()
            until = start + datetime.timedelta(seconds=timeout)
            while datetime.datetime.now() < until:
                if self.gfx.read_buttons() != NONE:
                    break
        return False

    def begin_auto_read_buttons(self) -> None:
        self.gfx.set_auto_read_buttons_on()
        if config.DEBUG:
            print('* begin_auto_read_buttons')
        self.auto_buttons = set()
        self.auto_buttons_boots = self.boots

    def auto_read_buttons(self) -> set[str]:
        if self.boots > self.auto_buttons_boots:
            self.auto_buttons.add('R')
        b = self.auto_buttons
        self.auto_buttons = set()
        return b

    def end_auto_read_buttons(self) -> set[str]:
        self.gfx.set_auto_read_buttons_off()
        self.chan.flush_in()
        if config.DEBUG:
            print('* end_auto_read_buttons')
        if self.boots > self.auto_buttons_boots:
            self.auto_buttons.add('R')
        return self.auto_buttons

    def clear_buttons(self) -> None:
        self.chan.flush_in()
        self.read_buttons_boots = self.boots

    def wait_button_up(self, timeout: int | None = None) -> set[str]:
        return self.wait_button(timeout, wait_released=True)

    def wait_button(self, timeout: int | None = None, wait_released: bool = False) -> set[str]:
        self.wait_no_button()
        b: set[str] = set()
        with until(timeout) as done:
            while not done():
                b = self.read_buttons()
                if b:
                    break
        if wait_released:
            while True:
                b2 = self.read_buttons()
                if not b2:
                    break
                b |= b2
        return b

    def read_buttons(self, flush: bool = False) -> set[str]:
        if flush:
            self.chan.flush_in()
            self.read_buttons_boots = self.boots

        ans = self.gfx.read_buttons()
        b: set[str] = set()
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

    def do_command(self, cmd: str, ignore_error: bool = False) -> str:
        # Since the board may be rebooted in the middle of a command,
        # it is okay to retry once
        try:
            return self.send_command(cmd, ignore_error)
        except:
            self.chan.clear()
            return self.send_command(cmd, ignore_error)

    def fatal(self, msg: str) -> None:
        print(msg)
        self.gfx.reset()
        w, h = 1, config.TEXT_SCALING
        self.gfx.set_text_size(0.5, 1)
        self.gfx.set_text_wrap_on()

        msg = ' '.join(msg.split())
        msg = msg[-20*8:]
        for chunk in chunkize(msg.replace('\n', ' '), 20):
            self.gfx.print(chunk)
        self.gfx.display()
        sys.exit(1)
