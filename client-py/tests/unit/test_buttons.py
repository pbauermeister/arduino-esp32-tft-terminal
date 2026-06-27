"""Button state / event decoding.

The board reports button state via `readButtons` and pushes events as
`OK <codes>` on any response (auto-read mode). These tests script those
answers through `FakeChannel` and assert the client decodes them correctly.
"""

from typing import Any, Callable

from arduino_esp32_tft_terminal.lib.board import Board

MakeBoard = Callable[..., tuple[Board, Any]]


def test_no_buttons(make_board: MakeBoard) -> None:
    board, _ = make_board({'readButtons': 'NONE'})
    assert board.read_buttons() == set()


def test_multiple_buttons(make_board: MakeBoard) -> None:
    board, _ = make_board({'readButtons': 'AB'})
    assert board.read_buttons() == {'A', 'B'}


def test_invalid_codes_ignored(make_board: MakeBoard) -> None:
    board, _ = make_board({'readButtons': 'XY'})
    assert board.read_buttons() == set()


def test_auto_read_accumulates_events(make_board: MakeBoard) -> None:
    # A response of "OK A" feeds the auto-button handler.
    board, _ = make_board({'display': 'OK A'})
    board.gfx.display()
    assert board.auto_read_buttons() == {'A'}
