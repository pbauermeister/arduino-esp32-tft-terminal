import contextlib
import datetime
import termios
from typing import Callable, Generator

import serial  # pip3 install pyserial

READY = 'READY'
ASCII = 'ASCII'
OK = 'OK'
NONE = 'NONE'
ERROR = 'ERROR'
UNKNOWN = 'UNKNOWN'


@contextlib.contextmanager
def until(timeout: int | None = None) -> Generator[Callable[[], bool], None, None]:
    if timeout is not None:
        start = datetime.datetime.now()
        until = start + datetime.timedelta(seconds=timeout)

        def done() -> bool:
            return datetime.datetime.now() >= until
    else:
        def done() -> bool:
            return False

    yield done


def chunkize(str: str, n: int) -> list[str]:
    return [str[i:i+n] for i in range(0, len(str), n)]


class RebootedException(Exception):
    pass


ArduinoCommExceptions = (
    # serial.serialutil.SerialException,
    serial.SerialException,
    serial.PortNotOpenError,
    serial.SerialTimeoutException,
    OSError,
    termios.error,
    UnicodeDecodeError,
)
