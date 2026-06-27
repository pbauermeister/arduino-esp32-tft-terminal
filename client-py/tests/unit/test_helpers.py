"""Tier 1 — name-casing helpers (pure)."""

from arduino_esp32_tft_terminal.app import (
    camel_to_kebab,
    camel_to_snake,
    camel_to_title,
)


def test_camel_to_snake() -> None:
    assert camel_to_snake('MonitorCpus') == 'monitor_cpus'
    assert camel_to_snake('BubblesAir') == 'bubbles_air'


def test_camel_to_kebab() -> None:
    assert camel_to_kebab('MonitorCpus') == 'monitor-cpus'
    assert camel_to_kebab('CollisionsElastic') == 'collisions-elastic'


def test_camel_to_title() -> None:
    assert camel_to_title('MonitorCpus') == 'Monitor Cpus'
