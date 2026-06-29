"""Load and validate `protocol.yaml`, and port the firmware `hash()`."""

from __future__ import annotations

from pathlib import Path

import yaml

from .schema import Protocol


def fw_hash(s: str) -> int:
    """Port of the firmware constexpr `hash()` (server `command.h`).

    Case-insensitive (ORs each byte with 0x20), 32-bit unsigned, evaluated
    right-to-left, base 5381. Used to assert command-hash uniqueness at
    generation time — the runtime switch silently assumes no collisions."""
    h = 5381
    for ch in reversed(s):
        h = ((h * 33) & 0xFFFFFFFF) ^ (ord(ch) | 0x20)
        h &= 0xFFFFFFFF
    return h


def load_protocol(path: str | Path) -> Protocol:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("protocol.yaml top level must be a list of commands")
    return Protocol(commands=data)
