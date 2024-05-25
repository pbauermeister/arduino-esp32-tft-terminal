import time

from app import App, TimeEscaper
from lib.board import Board


class Fill(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)

    def _run(self) -> bool:
        escaper = TimeEscaper(self)
        alt = True
        self.gfx.set_auto_display_on()
        sx = 0.5
        sy = 0.5

        def run_once(alt: bool, sx: float, sy: float) -> bool | None:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            self.gfx.set_text_size(sx, sy)
            self.gfx.home()
            self.gfx.fill_screen(int(alt))
            if alt:
                self.gfx.set_text_color(0, 0, 0)
            else:
                self.gfx.set_text_color(255, 255, 255)
            for i in range(ord('!'), 255):
                c = chr(i)
                self.gfx.print(c)
            self.gfx.display()
            time.sleep(0.5)
            return None

        while True:
            for sx, sy in ((0.5, 0.5), (0.5, 1), (1, 1)):
                for alt in True, False:
                    res = run_once(alt, sx, sy)
                    if res is None:
                        continue
                    return res
