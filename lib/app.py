from lib import *
import config
import time

class App:
    def __init__(self, board):
        self.board = board
        self.command = board.command
        self.name = self.__class__.__name__

        self.board.configure()
        assert config.WIDTH and config.HEIGHT
        self.command(f'setTextSize 1 2')
        title = self.name.upper()
        x, y = self.get_title_pos(title)
        self.command('reset')
        self.command(f'setCursor {x} {y}')
        self.command(f'print {title}')
        self.command('display')

        self.command('readButtons')
        time.sleep(0.5)
        if self.command('readButtons') == NONE:
            time.sleep(0.5)

        self.command('reset')
        self.command(f'setTextSize 1')

    def get_title_pos(self, title):
        ans = self.command(f'getTextBounds 0 0 {title}')
        vals = [int(v) for v in ans.split()]
        w, h = vals[-2:]
        x = int(config.WIDTH/2 - w/2 +.5)
        y = int(config.HEIGHT/2 - h/2 +.5)
        return x, y
