from lib import *
import config
from app import App

class ThatsAll(App):
    def __init__(self, board):
        super().__init__(board, auto_read=False, name='That\'s All')

    def _run(self):
        pass
