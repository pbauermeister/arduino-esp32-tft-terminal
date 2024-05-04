import socket
import subprocess

import config
from app import App, TimeEscaper
from lib.board import Board

CHOICE_EXIT = 1
CHOICE_NEXT = 2
CHOICE_RESET = 3


class MonitorBase(App):
    def show_header(
        self, title: str, menu: str | None = None, with_banner: bool = False
    ) -> None:
        self.gfx.set_text_color(255, 255, 255)
        self.gfx.set_text_size(1, 1)
        super().show_header(title, '', with_banner)
        self.set_pane_text_attr()

    def set_pane_text_attr(self) -> None:
        self.gfx.set_text_size(1, 1)
        self.gfx.set_text_color(128, 128, 128)

    def get_mem(self) -> list[str]:
        try:
            out = self.shell_command(['free', '--giga'])
            stats = out.splitlines()[1].split()[1:]

            cols = 'Ttl Usd Fre Sha Buf Avg'.split()
            head = '  ' + ''.join([f'{s:3}' for s in cols])
            vals = '   ' + ' '.join([f'{int(v):2}' for v in stats])
            return [head, vals]
        except:
            return ['mem unavailable']

    def shell_command(
        self, cmd: list[str], force_local: bool = False, check: bool = True
    ) -> str:
        if config.MONITOR_SSH_AUTHORITY and not force_local:
            cmd = ['ssh', config.MONITOR_SSH_AUTHORITY] + cmd
        try:
            return subprocess.run(
                cmd, encoding='utf-8', check=check, stdout=subprocess.PIPE
            ).stdout
        except Exception as e:
            print(f'Error >>> {cmd}')
            raise

    def shorten(self, txt: str) -> str:
        txt = txt.rstrip()
        return txt[: config.COLUMNS]


class MonitorHost(MonitorBase):

    def __init__(self, board: Board):
        super().__init__(board, auto_read=False)
        self.set_pane_text_attr()

    def _run(self) -> bool:
        title = 'Host'
        escaper = TimeEscaper(self)
        while True:
            self.show_header(title)

            nb_users = self.get_nb_users()
            users = f'{nb_users or "???"} user' + ('' if nb_users == 1 else 's')
            date = self.get_date()
            lines = [
                self.get_hostname(),
                self.get_ip(),
                users,
                date,
                self.get_uptime(),
            ] + self.get_mem()

            for l in lines:
                l = self.shorten(l)
                self.gfx.print(f'{l}\\n')
            self.gfx.display()

            btns = self.board.wait_button(2)
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

    def get_hostname(self) -> str:
        try:
            return self.shell_command(['hostname'])
        except:
            return '<hostname unavail>'

    def get_ip(self) -> str:
        if config.MONITOR_SSH_AUTHORITY:
            return self.get_remote_ip()
        else:
            return self.get_local_ip()

    def get_remote_ip(self) -> str:
        try:
            host = config.MONITOR_SSH_AUTHORITY.split('@')[-1]
            out = self.shell_command(['host', host], force_local=True, check=False)
            return out.splitlines()[0].split(' ')[-1]
        except:
            return '<rmt ip addr unavail>'

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
        except:
            return '<ip addr unavail>'

    def get_nb_users(self) -> int | None:
        try:
            out = self.shell_command(['who'])
            return len(out.splitlines())
        except:
            return None

    def get_date(self) -> str:
        try:
            out = self.shell_command(['date', '--rfc-3339=seconds'])
            return out.split('+')[0]
        except:
            return '<date unavail>'

    def get_uptime(self) -> str:
        try:
            uptime = self.shell_command(['uptime', '-p'])
        except:
            return '<uptime unavail>'
        for unit in 'hour', 'minute', 'day', 'week', 'month', 'year':
            initial = unit[0]
            what = ' ' + unit
            uptime = uptime.replace(what + 's', initial).replace(what, initial)
        return uptime

    def get_mem(self) -> list[str]:
        try:
            out = self.shell_command(['free', '--giga'])
            stats = out.splitlines()[1].split()[1:]

            cols = 'Ttl Usd Fre Sha Buf Avg'.split()
            head = '  ' + ''.join([f'{s:3}' for s in cols])
            vals = '   ' + ' '.join([f'{int(v):2}' for v in stats])
            return [head, vals]
        except:
            return ['mem unavailable']
