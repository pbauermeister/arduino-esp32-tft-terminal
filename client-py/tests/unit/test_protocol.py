"""Protocol contract — command formatting and response parsing.

The client's job over USB is to format commands and parse answers correctly;
that's the bug surface. `FakeChannel` records what was written and scripts the
answers, so these run with no hardware.
"""

from typing import Any, Callable

import pytest

from arduino_esp32_tft_terminal.lib.board import Board

MakeBoard = Callable[..., tuple[Board, Any]]


def test_draw_commands_are_formatted(make_board: MakeBoard) -> None:
    board, chan = make_board()
    board.gfx.draw_circle(10, 20, 5, 1)
    board.gfx.fill_rect(0, 0, 240, 8, 1)
    board.gfx.draw_line(1, 2, 3, 4, 0)
    board.gfx.set_text_color(255, 128, 0)
    assert 'drawCircle 10 20 5 1' in chan.written
    assert 'fillRect 0 0 240 8 1' in chan.written
    assert 'drawLine 1 2 3 4 0' in chan.written
    assert 'setTextColor 255 128 0' in chan.written


def test_width_height_queries_parse(make_board: MakeBoard) -> None:
    board, chan = make_board()
    assert board.gfx.get_width() == 240
    assert board.gfx.get_height() == 135
    assert 'width' in chan.written
    assert 'height' in chan.written


def test_get_text_bounds_parses_last_two_ints(make_board: MakeBoard) -> None:
    board, _ = make_board({'getTextBounds 0 0 AB': '0 0 12 8'})
    assert board.gfx.get_text_bounds(0, 0, 'AB') == (12, 8)


def test_error_response_is_rejected(make_board: MakeBoard) -> None:
    board, _ = make_board({'reset': 'ERROR bad arg'})
    with pytest.raises(AssertionError):
        board.gfx.reset()
