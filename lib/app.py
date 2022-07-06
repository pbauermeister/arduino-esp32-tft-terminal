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
        w, h = self.get_text_size(title)
        x = int(config.WIDTH/2 - w/2 +.5)
        y = int(config.HEIGHT/2 - h/2 +.5)
        return x, y

    def get_text_size(self, text):
        ans = self.command(f'getTextBounds 0 0 {text}')
        vals = [int(v) for v in ans.split()]
        w, h = vals[-2:]
        return w, h

    def show_header(self, title, menu):
        self.command(f'reset')
        self.command(f'fillRect 0 0 {config.WIDTH} 8 1')
        self.command(f'setTextColor 0')
        self.command(f'setCursor 1 0')
        self.command(f'print {title}')
        w, h = self.get_text_size(menu)
        x = config.WIDTH - w - 3
        self.command(f'setCursor {x} 0')
        self.command(f'print {menu}')

        self.command(f'setTextColor 1')
        self.command(f'home')
        self.command(f'print \\n')