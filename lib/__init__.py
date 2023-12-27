import contextlib
import datetime
import sys
import termios
from typing import Any, Callable, Generator

import serial  # pip3 install pyserial

READY = 'READY'
ASCII = 'ASCII'
OK = 'OK'
NONE = 'NONE'
ERROR = 'ERROR'
UNKNOWN = 'UNKNOWN'


@contextlib.contextmanager
def until(timeout: int = None) -> Generator[Callable[[], bool], None, None]:
    start = datetime.datetime.now()
    if timeout is not None:
        until = start + datetime.timedelta(seconds=timeout)

    def done() -> bool:
        if timeout is None:
            return False
        return datetime.datetime.now() >= until
    yield done


def chunkize(str: str, n: int) -> list[str]:
    return [str[i:i+n] for i in range(0, len(str), n)]


class RebootedException(Exception):
    pass


ArduinoCommExceptions = (
    serial.serialutil.SerialException,
    OSError,
    termios.error,
    UnicodeDecodeError,
)
