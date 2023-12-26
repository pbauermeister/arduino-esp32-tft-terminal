import math
import random
import time

import config
from app import App, Bouncer, TimeEscaper
from lib import *
from lib.board import Board


class Fill(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> None:
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
            if self.board.auto_read_buttons():
                break
            if escaper.check():
                break
            time.sleep(.5)
            alt = not alt

        return
