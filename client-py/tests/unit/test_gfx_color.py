"""Tier 1 — HSV→RGB conversion (pure static method)."""

from arduino_esp32_tft_terminal.lib.gfx import Gfx


def test_primaries() -> None:
    assert Gfx.hsv_to_rgb(0, 100, 100) == (255, 0, 0)
    assert Gfx.hsv_to_rgb(120, 100, 100) == (0, 255, 0)
    assert Gfx.hsv_to_rgb(240, 100, 100) == (0, 0, 255)


def test_white_and_black() -> None:
    assert Gfx.hsv_to_rgb(0, 0, 100) == (255, 255, 255)
    assert Gfx.hsv_to_rgb(0, 0, 0) == (0, 0, 0)


def test_clamps_out_of_range_hue() -> None:
    assert Gfx.hsv_to_rgb(999, 100, 100) == Gfx.hsv_to_rgb(360, 100, 100)
