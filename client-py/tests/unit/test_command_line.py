"""Generated command-line layer — wire formatting specific to codegen.

Complements test_protocol.py (which drives the Gfx facade) by exercising the
generated `CommandLine` directly: bool serialisation, optional-arg defaults,
and int-tuple return parsing.
"""

from typing import Any, Callable

from arduino_esp32_tft_terminal.lib.board import Board
from arduino_esp32_tft_terminal.lib.command_line_autogen import CommandLine

MakeBoard = Callable[..., tuple[Board, Any]]


def _command_line(make_board: MakeBoard, responses: dict[str, str] | None = None):
    board, chan = make_board(responses)
    return CommandLine(board.command), chan


def test_bool_args_serialise_as_0_1(make_board: MakeBoard) -> None:
    cmd, chan = _command_line(make_board)
    cmd.invert_display(True)
    cmd.set_text_wrap(False)
    cmd.auto_display(True)
    cmd.draw_char(1, 2, 65, True, False, 2)
    assert 'invertDisplay 1' in chan.written
    assert 'setTextWrap 0' in chan.written
    assert 'autoDisplay 1' in chan.written
    assert 'drawChar 1 2 65 1 0 2' in chan.written


def test_optional_defaults_are_sent(make_board: MakeBoard) -> None:
    cmd, chan = _command_line(make_board)
    cmd.set_text_size(3)  # sy defaults to -1 (square)
    cmd.invert_display()  # inv defaults to True -> 1
    cmd.watch_buttons()  # during 0, interval 100
    assert 'setTextSize 3 -1' in chan.written
    assert 'invertDisplay 1' in chan.written
    assert 'watchButtons 0 100' in chan.written


def test_ints_return_is_a_tuple(make_board: MakeBoard) -> None:
    cmd, _ = _command_line(make_board, {'getTextBounds 1 2 Hi': '1 2 12 8'})
    assert cmd.get_text_bounds(1, 2, 'Hi') == (1, 2, 12, 8)
