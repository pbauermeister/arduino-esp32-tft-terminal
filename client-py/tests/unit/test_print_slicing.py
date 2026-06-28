"""Print slicing + capability negotiation (devlog 0052).

The board stores each buffered `print` in a fixed `str` buffer; `getPrintMaxLength`
reports its usable size. The client slices long prints to fit, never splitting a
backslash escape, and respects the command-line wire limit.
"""

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.lib.gfx import _slice_print


def _unescape(s: str) -> str:
    """Mirror the firmware's unescape, to check escapes survive slicing."""
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def test_slice_respects_max_text() -> None:
    s = 'a' * 300
    chunks = _slice_print(s, 127, 190)
    assert chunks == ['a' * 127, 'a' * 127, 'a' * 46]
    assert ''.join(chunks) == s


def test_slice_does_not_split_escape() -> None:
    # the \n escape straddles the 127th-character boundary
    s = 'x' * 126 + '\\n' + 'y' * 50
    chunks = _slice_print(s, 127, 190)
    assert ''.join(chunks) == s  # lossless on the wire
    # escapes intact: per-chunk unescape concatenates to the whole
    assert ''.join(_unescape(c) for c in chunks) == _unescape(s)
    assert all(len(_unescape(c)) <= 127 for c in chunks)


def test_slice_escape_counts_as_one_but_respects_wire() -> None:
    s = '\\n' * 200  # 200 unescaped chars, 400 wire chars
    chunks = _slice_print(s, 127, 190)
    assert ''.join(chunks) == s
    assert all(len(_unescape(c)) <= 127 for c in chunks)  # str capacity
    assert all(len(c) <= 190 for c in chunks)  # command-line wire cap


def test_default_print_max(fake_board) -> None:
    assert fake_board.gfx.print_max == config.DEFAULT_PRINT_MAX


def test_print_fast_path(make_board) -> None:
    board, chan = make_board()
    board.gfx.print('hi')
    assert [w for w in chan.written if w.startswith('print ')] == ['print hi']


def test_print_slices_long(make_board) -> None:
    board, chan = make_board()
    board.gfx.print_max = 10
    board.gfx.print('a' * 25)
    payloads = [w[len('print ') :] for w in chan.written if w.startswith('print ')]
    assert len(payloads) == 3
    assert all(len(p) <= 10 for p in payloads)
    assert ''.join(payloads) == 'a' * 25


def test_get_print_max_length(make_board) -> None:
    board, _ = make_board(responses={'getPrintMaxLength': '127'})
    assert board.gfx.get_print_max_length() == 127


def test_negotiation_sets_print_max(make_board) -> None:
    board, _ = make_board(responses={'getPrintMaxLength': '120'})
    board.configure()
    assert board.gfx.print_max == 120


def test_negotiation_fallback_keeps_default(fake_board) -> None:
    # default FakeChannel answers 'OK' to getPrintMaxLength -> int() fails -> default
    fake_board.configure()
    assert fake_board.gfx.print_max == config.DEFAULT_PRINT_MAX
