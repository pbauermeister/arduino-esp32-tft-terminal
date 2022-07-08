import contextlib
import datetime
import sys

READY   = 'READY'
ASCII   = 'ASCII'
OK      = 'OK'
NONE    = 'NONE'
ERROR   = 'ERROR'
UNKNOWN = 'UNKNOWN'


@contextlib.contextmanager
def until(timeout=None):
    start = datetime.datetime.now()
    if timeout is not None:
        until = start + datetime.timedelta(seconds=timeout)
    def done():
        if timeout is None:
            return False
        return datetime.datetime.now() >= until
    yield done


def chunkize(str, n):
    return [str[i:i+n] for i in range(0, len(str), n)]


class RebootedException(Exception):
    pass


def fatal(board, msg):
    print(msg)
    board.command('home')
    board.command('setTextSize 1')
    board.command('setTextWrap 1')
    board.command('reset')

    msg = ' '.join(msg.split())
    msg = msg[-20*8:]
    for chunk in chunkize(msg.replace('\n', ' '), 20):
        board.command(f'print {chunk}')
    board.command('display')
    sys.exit(1)
