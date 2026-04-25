from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from app import App, TimeEscaper
from claude_busy_monitor import (
    ClaudeState,
    get_sessions,
    get_state_counts,
)
from lib.board import Board
from lib.gfx import Gfx

STATUS_TEXT_SIZE_X = 1.5
STATUS_TEXT_SIZE_Y = 1
STATUS_TEXT_MARGIN = 2

LIST_TEXT_SIZE_X = 1
LIST_TEXT_SIZE_Y = 1

RgbColor = tuple[int, int, int]


class NamedColor(Enum):
    WHITE = RgbColor((255, 255, 255))
    BLACK = RgbColor((0, 0, 0))
    RED = RgbColor((255, 0, 0))
    YELLOW = RgbColor((255, 255, 0))
    GREEN = RgbColor((0, 255, 0))
    GRAY = RgbColor((64, 64, 64))
    DARK = RgbColor((12, 12, 12))
    LIGHTGRAY = RgbColor((164, 164, 164))


@dataclass
class TextBgColor:
    fg: NamedColor
    bg: NamedColor


BUSY_COLOR = TextBgColor(NamedColor.WHITE, NamedColor.RED)
ASKING_COLOR = TextBgColor(NamedColor.BLACK, NamedColor.YELLOW)
IDLE_COLOR = TextBgColor(NamedColor.BLACK, NamedColor.GREEN)

INACTIVE_COLOR = TextBgColor(NamedColor.GRAY, NamedColor.DARK)
BLINKED_COLOR = TextBgColor(NamedColor.WHITE, NamedColor.DARK)

LIST_COLOR = NamedColor.LIGHTGRAY


@dataclass
class Status:
    name: str
    row: int
    width: int
    color: TextBgColor
    blink_color: TextBgColor | None = None
    blinks: bool = False
    value: int = 0

    def print(self, gfx: Gfx) -> None:
        color = self.color
        if not self.value:
            color = INACTIVE_COLOR
            self.blinks = False
        elif self.blink_color is not None:
            self.blinks = not self.blinks
            if self.blinks:
                color = self.blink_color

        y = (16 * STATUS_TEXT_SIZE_Y + STATUS_TEXT_MARGIN * 2) * self.row
        gfx.set_bg_color(*color.bg.value)
        gfx.fill_rect(
            0, y, self.width, 16 * STATUS_TEXT_SIZE_Y + STATUS_TEXT_MARGIN * 2, 0
        )

        s = f" {self.value:4} {self.name}"
        gfx.set_text_color(*color.fg.value)
        gfx.set_cursor(0, y + STATUS_TEXT_MARGIN * 2)
        gfx.print(s)


class ClaudeMonitor(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)
        self.w = self.gfx.get_width()
        self.h = self.gfx.get_height()

    def _run(self) -> bool:
        escaper = TimeEscaper(self)
        self.gfx.set_auto_display_off()
        self.gfx.set_text_wrap_off()

        asking = Status("ASKING", 0, self.w, ASKING_COLOR, BLINKED_COLOR)
        busy = Status("BUSY", 1, self.w, BUSY_COLOR)
        idle = Status("IDLE", 2, self.w, IDLE_COLOR)

        while True:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            sessions = get_sessions()
            counts = get_state_counts(sessions)

            asking.value = counts.get(ClaudeState.ASKING, 0)
            busy.value = counts.get(ClaudeState.BUSY, 0)
            idle.value = counts.get(ClaudeState.IDLE, 0)
            self.gfx.set_text_size(STATUS_TEXT_SIZE_X, STATUS_TEXT_SIZE_Y)
            asking.print(self.gfx)
            busy.print(self.gfx)
            idle.print(self.gfx)

            sorted_sessions = (
                [s for s in sessions if s.state == ClaudeState.ASKING]
                + [s for s in sessions if s.state == ClaudeState.IDLE]
                + [s for s in sessions if s.state == ClaudeState.BUSY]
            )

            row = 3
            y = (
                16 * STATUS_TEXT_SIZE_Y + STATUS_TEXT_MARGIN * 2
            ) * row + STATUS_TEXT_MARGIN * 2
            self.gfx.set_cursor(0, y + STATUS_TEXT_MARGIN * 2)
            self.gfx.set_text_size(LIST_TEXT_SIZE_X, LIST_TEXT_SIZE_Y)
            for session in sorted_sessions:
                y += 16 * LIST_TEXT_SIZE_Y + STATUS_TEXT_MARGIN
                if y > self.h:
                    break
                s = session.state.value.upper()
                text = f"{s:6} {session.name}"
                self.gfx.set_cursor(0, y)
                self.gfx.set_text_color(*LIST_COLOR.value)
                self.gfx.print(text)

            self.gfx.display()
            time.sleep(0.5)
