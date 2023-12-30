from app import App
from lib.board import Board


class ThatsAll(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=False, name='That\'s All')

    def _run(self) -> bool:
        return False
