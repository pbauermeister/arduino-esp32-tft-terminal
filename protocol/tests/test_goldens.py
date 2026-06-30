"""Generator goldens — feature-fixture spec vs expected emission.

Tests the generator's emission logic decoupled from the real protocol: a small
synthetic spec exercises each schema feature once, and each emitter's raw output
(pre-format, so version-independent) is compared to a committed golden.

Refresh after an intentional generator change: GOLDEN_UPDATE=1 uv run pytest
"""

import os
from pathlib import Path

import pytest

from tft_protocol.generate import (
    render_command_dispatch,
    render_command_line,
    render_protocol_doc,
    render_replay_dispatch,
    render_server_handlers,
)
from tft_protocol.load import load_protocol

_HERE = Path(__file__).resolve().parent
FIXTURE = _HERE / "fixtures" / "sample_protocol.yaml"
GOLDEN = _HERE / "golden"

CASES = {
    "command_line.py": render_command_line,
    "command_dispatch.inc": render_command_dispatch,
    "replay_dispatch.inc": render_replay_dispatch,
    "protocol_handlers.h": render_server_handlers,
    "doc.md": render_protocol_doc,
}


@pytest.mark.parametrize("name", list(CASES))
def test_golden(name: str) -> None:
    out = CASES[name](load_protocol(FIXTURE))
    path = GOLDEN / name
    if os.environ.get("GOLDEN_UPDATE") == "1":
        path.parent.mkdir(exist_ok=True)
        path.write_text(out, encoding="utf-8")
        return
    assert out == path.read_text(encoding="utf-8"), (
        f"{name} drifted from its golden (GOLDEN_UPDATE=1 uv run pytest to refresh)"
    )
