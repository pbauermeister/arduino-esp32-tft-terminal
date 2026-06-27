"""Tier 2 — command-stream snapshot (golden) tests.

Run a deterministic app for N frames against a FakeChannel, capture the USB
command stream it emits, and diff it against a committed golden file. This is
the dfd non-regression idea retargeted to the command stream (devlog 0019).

Regenerate goldens after a reviewed change: `make snapshot-regenerate`
(sets `SNAPSHOT_UPDATE=1`).
"""

import os
from pathlib import Path
from typing import Callable

import pytest

from arduino_esp32_tft_terminal.app.cube import Cube
from arduino_esp32_tft_terminal.app.fill import Fill
from arduino_esp32_tft_terminal.app.starfield import Starfield
from arduino_esp32_tft_terminal.app.tunnel import Tunnel

GOLDEN = Path(__file__).parent / 'golden'
APPS = {'cube': Cube, 'fill': Fill, 'starfield': Starfield, 'tunnel': Tunnel}


@pytest.mark.parametrize('name', sorted(APPS))
def test_command_stream(name: str, capture_stream: Callable[..., list[str]]) -> None:
    stream = capture_stream(APPS[name], n_frames=8)
    assert stream, f'{name} produced no commands'
    text = '\n'.join(stream) + '\n'

    golden = GOLDEN / f'{name}.txt'
    if os.environ.get('SNAPSHOT_UPDATE') or not golden.exists():
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(text)
        pytest.skip(f'regenerated golden for {name}')

    assert text == golden.read_text(), (
        f'{name} command stream changed; if intended run '
        f'`make snapshot-regenerate` and review the diff'
    )
