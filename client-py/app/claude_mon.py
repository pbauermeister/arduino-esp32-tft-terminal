from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum

from app import App, TimeEscaper
from claude_busy_monitor import (
    ClaudeSession,
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
LIST_TEXT_MARGIN = 2
LIST_OFFSET_Y = (16 * STATUS_TEXT_SIZE_Y + STATUS_TEXT_MARGIN * 2) * 4


RgbColor = tuple[int, int, int]


class NamedColor(Enum):
    WHITE = RgbColor((255, 255, 255))
    LIGHTGRAY = RgbColor((164, 164, 164))
    GRAY = RgbColor((72, 72, 72))
    DARK = RgbColor((32, 32, 32))
    BLACK = RgbColor((0, 0, 0))

    RED = RgbColor((255, 0, 0))
    YELLOW = RgbColor((255, 255, 0))
    GREEN = RgbColor((0, 255, 0))
    ORANGE = RgbColor((255, 165, 0))


@dataclass
class TextBgColor:
    fg: NamedColor
    bg: NamedColor


BUSY_COLOR = TextBgColor(NamedColor.BLACK, NamedColor.ORANGE)
ASKING_COLOR = TextBgColor(NamedColor.BLACK, NamedColor.YELLOW)
IDLE_COLOR = TextBgColor(NamedColor.BLACK, NamedColor.GREEN)

INACTIVE_COLOR = TextBgColor(NamedColor.GRAY, NamedColor.DARK)
BLINKED_COLOR = TextBgColor(NamedColor.WHITE, NamedColor.DARK)

LIST_COLOR = TextBgColor(NamedColor.LIGHTGRAY, NamedColor.BLACK)

CLAUDING_COLOR = TextBgColor(NamedColor.WHITE, NamedColor.ORANGE)


@dataclass
class StateCountStatus:
    name: str
    row: int
    width: int
    color: TextBgColor
    blink_color: TextBgColor | None = None
    blinks: bool = False
    value: int = 0
    last_value: tuple[bool, int] | None = None  # to avoid flickering when unchanged

    def print(self, gfx: Gfx) -> None:
        color = self.color
        if not self.value:
            color = INACTIVE_COLOR
            self.blinks = False
        elif self.blink_color is not None:
            self.blinks = not self.blinks
            if self.blinks:
                color = self.blink_color

        # No change, skip to reduce flickering
        if self.last_value == (value := (self.blinks, self.value)):
            return
        self.last_value = value

        # Render
        y = (16 * STATUS_TEXT_SIZE_Y + STATUS_TEXT_MARGIN * 2) * self.row
        h = 16 * STATUS_TEXT_SIZE_Y + STATUS_TEXT_MARGIN * 2
        s = f" {self.value:3} {self.name}"

        gfx.set_bg_color(*color.bg.value)
        gfx.fill_rect(0, y, self.width, h, 0)
        gfx.set_text_color(*color.fg.value)
        gfx.set_cursor(0, y + STATUS_TEXT_MARGIN * 2)
        gfx.print(s)


@dataclass
class SessionLine:
    idx: int
    width: int
    last_value: tuple[ClaudeState, str] | None = (
        None  # to avoid flickering when unchanged
    )

    def print(self, gfx: Gfx, session: ClaudeSession) -> int:
        y = LIST_OFFSET_Y + (16 * LIST_TEXT_SIZE_Y + LIST_TEXT_MARGIN) * self.idx

        # No change, skip to reduce flickering
        if self.last_value == (session.state, session.name):
            return y
        self.last_value = (session.state, session.name)

        # Erase line
        h = 16 * LIST_TEXT_SIZE_Y
        gfx.set_bg_color(*LIST_COLOR.bg.value)
        gfx.fill_rect(0, y, self.width, h, 0)

        # Print new text
        s = f"{session.state.value.upper():6} {session.name}"
        gfx.set_cursor(0, y)
        gfx.set_text_color(*LIST_COLOR.fg.value)
        gfx.print(s)

        return y

    @staticmethod
    def clear(gfx: Gfx, idx: int, width: int) -> None:
        y = LIST_OFFSET_Y + (16 * LIST_TEXT_SIZE_Y + LIST_TEXT_MARGIN) * idx
        h = 16 * LIST_TEXT_SIZE_Y
        gfx.set_bg_color(*LIST_COLOR.bg.value)
        gfx.fill_rect(0, y, width, h, 0)


class ClaudeChar:
    @dataclass(frozen=True)
    class SubChar:
        char: str
        x_offset: int
        y_offset: int
        sx: int = 2
        sy: int = 2

    CompositeChar = list[SubChar]

    DIM: CompositeChar = [
        SubChar('+', 0, 0),
    ]

    FLORAL_STAR: CompositeChar = [
        SubChar('+', 0, 0),
        SubChar('.', -2, -22),
        SubChar('.', -2, 2),
        SubChar('.', -12, -3),
        SubChar('.', 8, -3),
        SubChar('.', -12, -18),
        SubChar('.', 8, -18),
    ]

    FLORAL_STAR2: CompositeChar = [
        SubChar('+', 0, 0),
        SubChar('.', -2, -24),
        SubChar('.', -2, 4),
        SubChar('.', -16, -3),
        SubChar('.', 12, -3),
        SubChar('.', -16, -18),
        SubChar('.', 12, -18),
    ]

    EIGHT_STAR: CompositeChar = [
        SubChar('+', 0, 0),
        SubChar('-', -9, 0),
        SubChar('-', 11, 0),
        SubChar('/', -6, 6),
        SubChar('/', 6, -6),
        SubChar('\\\\', -6, -6),
        SubChar('\\\\', 6, 6),
        SubChar('|', 0, 6),
        SubChar('|', 0, -6),
    ]

    SIX_POINTED_STAR: CompositeChar = [
        SubChar('/', -6, 11, sx=2, sy=1),
        SubChar('/', 6, 3, sx=2, sy=1),
        SubChar('\\\\', -6, 3, sx=2, sy=1),
        SubChar('\\\\', 6, 11, sx=2, sy=1),
        SubChar('|', 0, 2),
        SubChar('|', 0, -2),
    ]

    FOUR_POINTED_STAR: CompositeChar = [
        SubChar('+', 0, 0),
        SubChar('.', -2, -24),
        SubChar('.', -2, 4),
        SubChar('.', -16, -10),
        SubChar('.', 12, -10),
    ]

    ALL_CHARS: list[CompositeChar] = [
        DIM,
        FLORAL_STAR,
        FLORAL_STAR2,
        SIX_POINTED_STAR,
        EIGHT_STAR,
        FOUR_POINTED_STAR,
    ]

    def draw(self, gfx: Gfx, char: CompositeChar, x: int, y: int) -> None:
        for sc in char:
            gfx.set_text_size(sc.sx // 2, sc.sy // 2)
            gfx.set_cursor(x + sc.x_offset // 2, y + sc.y_offset // 2)
            gfx.print(sc.char)


class Clauding:
    def __init__(self, width):
        self.width = width
        self.claude_chars = ClaudeChar()

    def draw(self, gfx: Gfx, n: int) -> None:
        gfx.set_bg_color(*CLAUDING_COLOR.bg.value)
        lh = 16 * STATUS_TEXT_SIZE_Y + STATUS_TEXT_MARGIN * 2
        h = lh * 3

        # display busy counter on background
        gfx.fill_rect(0, 0, self.width, h, 0)
        gfx.set_text_size(STATUS_TEXT_SIZE_X, STATUS_TEXT_SIZE_Y)
        gfx.set_text_color(*CLAUDING_COLOR.fg.value)
        gfx.set_cursor(60, lh + STATUS_TEXT_MARGIN * 2)
        s = f"{n} BUSY"
        gfx.print(s)

        # animate claude logo
        for c in self.claude_chars.ALL_CHARS:
            gfx.set_text_color(*CLAUDING_COLOR.fg.value)
            x = 24 + random.randint(0, 6)
            y = lh - 10 * 0 + random.randint(0, 6)
            self.claude_chars.draw(gfx, c, x, y)
            gfx.display()
            time.sleep(0.1)

            gfx.set_text_color(*CLAUDING_COLOR.bg.value)
            self.claude_chars.draw(gfx, c, x, y)
            gfx.display()


class ClaudeMonitor(App):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)
        self.w = self.gfx.get_width()
        self.h = self.gfx.get_height()

    def _run(self) -> bool:
        escaper = TimeEscaper(self)
        self.gfx.set_auto_display_off()
        self.gfx.set_text_wrap_off()
        clauding = Clauding(self.w)

        asking = StateCountStatus("ASKING", 0, self.w, ASKING_COLOR, BLINKED_COLOR)
        busy = StateCountStatus("BUSY", 1, self.w, BUSY_COLOR)
        idle = StateCountStatus("IDLE", 2, self.w, IDLE_COLOR)
        session_by_idx: dict[int, SessionLine] = {}

        last_max = -1

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

            # Counts
            asking.value = counts.get(ClaudeState.ASKING, 0)
            busy.value = counts.get(ClaudeState.BUSY, 0)
            idle.value = counts.get(ClaudeState.IDLE, 0)

            is_clauding = asking.value == 0 and idle.value == 0 and busy.value > 0
            if is_clauding:
                clauding.draw(self.gfx, busy.value)
                asking.last_value = idle.last_value = busy.last_value = None
            else:
                self.gfx.set_text_size(STATUS_TEXT_SIZE_X, STATUS_TEXT_SIZE_Y)
                asking.print(self.gfx)
                busy.print(self.gfx)
                idle.print(self.gfx)

            # Sessions
            sorted_sessions = (
                [s for s in sessions if s.state == ClaudeState.ASKING]
                + [s for s in sessions if s.state == ClaudeState.IDLE]
                + [s for s in sessions if s.state == ClaudeState.BUSY]
            )

            self.gfx.set_text_size(LIST_TEXT_SIZE_X, LIST_TEXT_SIZE_Y)

            idx = -1
            for idx, session in enumerate(sorted_sessions):
                session_line = session_by_idx.setdefault(idx, SessionLine(idx, self.w))
                y = session_line.print(self.gfx, session)
                if y + 16 * LIST_TEXT_SIZE_Y + LIST_TEXT_MARGIN * 2 > self.h:
                    break
            if not sorted_sessions:
                session_by_idx.clear()

            # clear remaining lines if sessions have decreased
            if idx < last_max:
                for i in range(idx + 1, last_max + 1):
                    SessionLine.clear(self.gfx, i, self.w)

            last_max = idx

            self.gfx.display()
            if not is_clauding:
                time.sleep(0.5)
