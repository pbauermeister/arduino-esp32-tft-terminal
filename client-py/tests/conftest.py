"""Shared test fixtures.

The whole client talks to the board through a single serial boundary,
`lib.channel.Channel`. `FakeChannel` stands in for it, so everything above
(Command, Gfx, Board, App, the apps) runs as real code with no hardware.

See devlog 0019 for the strategy.
"""

import random
from typing import Any, Callable

import numpy as np
import pytest

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.app import TimeEscaper
from arduino_esp32_tft_terminal.lib.board import Board

FAKE_WIDTH = 240
FAKE_HEIGHT = 135


class FakeChannel:
    """In-memory stand-in for `lib.channel.Channel`.

    Records every command written and answers the synchronous request/response
    protocol: queries get canned values, every other (draw) command gets `OK`.
    """

    def __init__(self, width: int = FAKE_WIDTH, height: int = FAKE_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.ser: Any = object()  # truthy; never touched (methods are overridden)
        self.on_message: str | None = None
        self.on_fn: Callable[[Any], None] | None = None
        self.written: list[str] = []
        self._response = 'OK'

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def clear(self) -> None:
        pass

    def flush_in(self) -> None:
        pass

    def set_callback(self, message: str, fn: Callable[[Any], None] | None) -> None:
        self.on_message = message
        self.on_fn = fn

    def write(self, s: str) -> None:
        self.written.append(s)
        self._response = self._answer(s)

    def read(self) -> str:
        return self._response

    def _answer(self, s: str) -> str:
        if s == 'width':
            return str(self.width)
        if s == 'height':
            return str(self.height)
        if s.startswith('getTextBounds'):
            parts = s.split(' ', 3)
            text = parts[3] if len(parts) > 3 else ''
            return f'0 0 {len(text) * 6} 8'  # deterministic glyph metrics
        if s == 'readButtons':
            return 'NONE'
        return 'OK'


@pytest.fixture
def fake_board() -> Board:
    """A `Board` backed by a `FakeChannel`, configured to 240x135."""
    config.WIDTH = 0
    config.HEIGHT = 0
    config.once = False
    config.APPS_INTERFRAME_DELAY_MS = 0  # no per-frame sleep in tests
    config.APPS_TITLE_DURATION = 0  # skip the title animation
    return Board(FakeChannel())


@pytest.fixture
def capture_stream(monkeypatch: pytest.MonkeyPatch) -> Callable[..., list[str]]:
    """Run an app for N frames against a FakeChannel and return the command stream.

    RNG is seeded; `TimeEscaper.check` is patched to end the loop after N frames.
    Only the commands emitted by `_run()` are returned (setup/title excluded).
    """

    def _capture(app_cls: Any, n_frames: int = 8) -> list[str]:
        random.seed(0)
        np.random.seed(0)
        config.WIDTH = 0
        config.HEIGHT = 0
        config.once = False
        config.APPS_INTERFRAME_DELAY_MS = 0
        config.APPS_TITLE_DURATION = 0

        counter = {'n': 0}

        def fake_check(self: TimeEscaper) -> bool:
            counter['n'] += 1
            return counter['n'] > n_frames

        monkeypatch.setattr(TimeEscaper, 'check', fake_check)

        chan = FakeChannel()
        board = Board(chan)
        app = app_cls(board)  # triggers configure + (skipped) title
        chan.written.clear()  # snapshot only the run loop
        app._run()
        return chan.written

    return _capture
