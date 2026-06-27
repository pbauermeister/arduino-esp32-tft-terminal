"""Tier 1 — CLI / config argument parsing."""

import sys

import pytest

from arduino_esp32_tft_terminal.app.cube import Cube
from arduino_esp32_tft_terminal.lib.args import get_args, get_config_args_specs


def test_config_specs_are_scalar() -> None:
    specs = get_config_args_specs()
    names = {s.name for s in specs}
    assert 'SCREEN_ROTATION' in names
    assert all(s.type in (str, bool, int, float) for s in specs)


def test_only_selects_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['prog', '--only', 'cube'])
    _, apps = get_args([Cube])
    assert apps == [Cube]


def test_unknown_app_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['prog', '--only', 'nope'])
    with pytest.raises(SystemExit):
        get_args([Cube])


def test_version_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, 'argv', ['prog', '--version'])
    with pytest.raises(SystemExit) as exc:
        get_args([Cube])
    assert exc.value.code == 0
