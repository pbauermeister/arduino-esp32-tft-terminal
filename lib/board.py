import config
import serial  # pip3 install pyserial
import time

from lib import *


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

    def command(self, cmd, ignore_error=False):
        # Since the board may be rebooted in the middle of a command,
        # it is okay to retry once
        try:
            return self._command(cmd, ignore_error)
        except:
            self.chan.clear()
            return self._command(cmd, ignore_error)

    def _command(self, cmd, ignore_error=False):
        self._command_send(cmd)
        try:
            return self._command_response()
        except:
            if ignore_error:
                return ''
            raise

    def _command_send(self, cmd):
        assert not self.reading_buttons
        self.chan.write(cmd)
        self.last_command = cmd

    def _command_response(self):
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
        self._command_send('waitButton -1 0')
        self.reading_buttons = True
        self.auto_buttons_boots = self.boots

    def end_read_buttons(self):
        assert self.reading_buttons
        if config.DEBUG:
            print('* end_read_buttons')
        self.reading_buttons = False
        self._command_send('width')
        resp = self._command_response()
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
