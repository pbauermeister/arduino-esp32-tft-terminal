import config
from app import App, Sprite, TimeEscaper
from lib import *
from lib.board import Board


class Bumps(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> None:
        sprites = [
            Sprite(self, 7,  1, 1),
            Sprite(self, 2,  1, -1),
            Sprite(self, 3, -1,  1),
            Sprite(self, 2, -1, -1),
        ]

        escaper = TimeEscaper(self)
        while True:
            if self.board.auto_read_buttons():
                break

            for s in sprites:
                s.erase()

            for s in sprites:
                s.advance()

            if escaper.check():
                break
            self.command('display')

        return
