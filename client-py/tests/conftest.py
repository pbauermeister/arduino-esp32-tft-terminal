"""Shared test fixtures.

The whole client talks to the board through a single serial boundary,
`lib.channel.Channel`. `FakeChannel` stands in for it, so everything above
(Command, Gfx, Board) runs as real code with no hardware. Tests focus on the
protocol contract — command formatting, response parsing, button decoding —
which is where the bug surface is (devlog 0019, revised per review in 0021).
"""

from typing import Any, Callable

import pytest

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.lib.board import Board

FAKE_WIDTH = 240
FAKE_HEIGHT = 135


class FakeChannel:
    """In-memory stand-in for `lib.channel.Channel`.

    Records every command written, and answers the synchronous request/response
    protocol. `responses` overrides the answer for an exact command string
    (used to script button reads, errors, etc.); otherwise queries get canned
    values and every other command gets `OK`.
    """

    def __init__(
        self,
        width: int = FAKE_WIDTH,
        height: int = FAKE_HEIGHT,
        responses: dict[str, str] | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.responses = dict(responses or {})
        self.ser: Any = object()  # truthy; never touched (methods overridden)
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
        if s in self.responses:
            return self.responses[s]
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


def _reset_config() -> None:
    config.WIDTH = 0
    config.HEIGHT = 0
    config.once = False
    config.APPS_INTERFRAME_DELAY_MS = 0  # no per-frame sleep in tests
    config.APPS_TITLE_DURATION = 0


@pytest.fixture
def fake_board() -> Board:
    """A `Board` backed by a default `FakeChannel` (240x135)."""
    _reset_config()
    return Board(FakeChannel())


@pytest.fixture
def make_board() -> Callable[..., tuple[Board, FakeChannel]]:
    """Factory: build a `(Board, FakeChannel)` with scripted `responses`."""

    def _make(responses: dict[str, str] | None = None) -> tuple[Board, FakeChannel]:
        _reset_config()
        chan = FakeChannel(responses=responses)
        return Board(chan), chan

    return _make
