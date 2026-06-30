# AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
# Regenerate with: make protocol-gen
"""Typed command-line layer — one method per protocol command.

Generated from protocol.yaml. Each method assembles the textual command line
and parses the typed response, then defers to `CommandExecutor.do_command`.
App conveniences (text scaling, print slicing, HSV, recovery handling) live in
the hand-written Gfx facade, not here.
"""

from __future__ import annotations

from .command_executor import CommandExecutor


class CommandLine:
    def __init__(self, command: CommandExecutor) -> None:
        self._command = command

    def buf_no_args(self) -> None:
        """Buffered command with no arguments."""
        self._command.do_command('bufNoArgs')

    def buf_all_types(self, x: int, ch: int, flag: bool, sz: int, color: int) -> None:
        """Buffered command exercising every numeric arg type."""
        self._command.do_command(f'bufAllTypes {x} {ch} {int(flag)} {sz} {color}')

    def buf_optional(self, a: int, b: int = -1) -> None:
        """Buffered command with an optional defaulted arg."""
        self._command.do_command(f'bufOptional {a} {b}')

    def buf_text(self, text: str) -> None:
        """Buffered raw-rest text; supports \\n escapes."""
        self._command.do_command(f'bufText {text}')

    def q_bounds(self, x: int, s: str) -> tuple[int, int, int, int]:
        """Query with a trailing string returning an int tuple."""
        _ans = self._command.do_command(f'qBounds {x} {s}')
        _parts = _ans.split()
        return (int(_parts[0]), int(_parts[1]), int(_parts[2]), int(_parts[3]))  # a b c d

    def q_value(self) -> int:
        """Query returning a single int."""
        return int(self._command.do_command('qValue'))

    def ctl_void(self) -> None:
        """Control command with no response."""
        self._command.do_command('ctlVoid', ignore_response=True)

    def btn_read(self, ms: int = 100) -> str:
        """Button command returning a string."""
        return self._command.do_command(f'btnRead {ms}')
