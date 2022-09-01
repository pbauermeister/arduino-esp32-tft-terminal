import math
import random
import time

from lib import *
import config
from app import App, TimeEscaper, Bouncer


class Fill(App):
    def __init__(self, board):
        super().__init__(board, auto_read=True)

    def _run(self):
        escaper = TimeEscaper(self)
        alt = True
        while True:
            self.board.command(f'home')
            self.board.command(f'fillScreen {int(alt)}')
            self.board.command(f'setTextColor {int(not alt)}')
            for i in range(ord('!'), 255):
                c = chr(i)
                self.command(f'print {c}')
            self.command('display')
            if self.board.auto_read_buttons(): break
            if escaper.check(): break
            time.sleep(.5)
            alt = not alt

        return
