import datetime
import json
import socket
import subprocess
import threading
import time

import config
from app import App
from lib.board import Board

CHOICE_EXIT = 1
CHOICE_NEXT = 2
CHOICE_RESET = 3


class Monitor(App):

    def __init__(self, board: Board):
        super().__init__(board, auto_read=False)
        self.set_pane_text_attr()
        cw, ch = self.gfx.get_text_bounds(0, 0, '9')
        self.chars_per_line = int(config.WIDTH / cw)
        self.lines = int(config.WIDTH / ch)

        self.mutex = threading.Lock()
        self.changed = False
        self.stop = False

    def set_pane_text_attr(self) -> None:
        # self.gfx.set_text_size(.5, 1)
        self.gfx.set_text_size(1, 1)
        self.gfx.set_fg_color(128, 128, 128)
        self.gfx.set_text_color(1)

    def _run(self) -> bool:
        ans: int | None = None
        while True:
            if config.MONITOR_HOST_TIMEOUT:
                ans = self.show_host()
                if ans == CHOICE_EXIT:
                    return False
                if ans == CHOICE_RESET:
                    return True

            if config.MONITOR_CPU_TIMEOUT:
                ans = self.show_cpu()
                if ans == CHOICE_EXIT:
                    return False
                if ans == CHOICE_RESET:
                    return True

            if ans is not None:
                continue
            if not config.MONITOR_ONLY:
                break
        return False

    def show_header(self, title: str, menu: str | None = None, with_banner: bool = False) -> None:
        self.gfx.set_fg_color(255, 255, 255)
        self.gfx.set_text_color(1)
        self.gfx.set_text_size(1, 1)

        super().show_header(title, 'A:next C:exit', with_banner)

        self.set_pane_text_attr()

    def wait_button(self, timeout: int) -> int | None:
        if timeout == 0:
            ans = self.board.read_buttons()
        else:
            ans = self.board.wait_button(timeout)
        if 'A' in ans:
            return CHOICE_NEXT
        if 'C' in ans:
            return CHOICE_EXIT
        if 'R' in ans:
            return CHOICE_RESET
        return None

    def show_host(self) -> int | None:
        title = 'Host'
        self.show_header(title, with_banner=True)
        self.gfx.display()
        self.board.wait_no_button(timeout=1)
        if self.board.read_buttons(flush=True):
            return CHOICE_NEXT
        self.board.begin_read_buttons()

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

        if 'A' in self.board.end_read_buttons():
            return CHOICE_NEXT

        self.show_header(title)
        for l in lines:
            l = shorten(l)
            self.gfx.print(f'{l}\\n')
        self.gfx.display()

        return self.wait_button(config.MONITOR_HOST_TIMEOUT)

    def show_cpu(self) -> int | None:
        start = datetime.datetime.now()
        until = start + datetime.timedelta(seconds=config.MONITOR_CPU_TIMEOUT)

        th = threading.Thread(target=self.task)
        self.stop = False
        th.start()

        title = 'CPU %'
        self.show_header(title, with_banner=True)
        self.board.wait_no_button(timeout=1)
        if self.board.read_buttons(flush=True):
            return CHOICE_NEXT

        while True:
            cpus: list[str] = []
            mem: list[str] = []
            with self.mutex:
                if self.changed:
                    cpus, mem = self.cpus, self.mem
                    self.changed = False
            if cpus:
                self.show_header(title)

                # CPUs
                self.gfx.set_cursor(0, config.TEXT_SCALING*12)
                lines = cpus
                for l in lines:
                    self.gfx.print(f'{l}\\n')
                # Mem
                if len(lines) <= 4:
                    self.gfx.set_cursor(0, config.TEXT_SCALING*6*8)
                    for l in mem:
                        self.gfx.print(f'{l}\\n')
                self.gfx.display()

            choice = self.wait_button(timeout=0)
            if choice:
                self.stop = True
                # th.join()
                return choice

            now = datetime.datetime.now()
            if now >= until:
                self.stop = True
                # th.join()
                return None

    def task(self) -> None:
        self.changed = False
        while not self.stop:
            cpus = self.get_cpus_pcents()
            mem = self.get_mem()
            if self.stop:  # can be set by other thread
                break  # type:ignore[unreachable]
            with self.mutex:
                self.cpus, self.mem = cpus, mem
                self.changed = True

    def get_hostname(self) -> str:
        try:
            return shell_command(['hostname'])
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
            out = shell_command(['host', host], force_local=True, check=False)
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
            out = shell_command(['who'])
            return len(out.splitlines())
        except:
            return None

    def get_date(self) -> str:
        try:
            out = shell_command(['date', '--rfc-3339=seconds'])
            return out.split('+')[0]
        except:
            return '<date unavail>'

    def get_uptime(self) -> str:
        try:
            uptime = shell_command(['uptime', '-p'])
        except:
            return '<uptime unavail>'
        for unit in 'hour', 'minute', 'day', 'week', 'month', 'year':
            initial = unit[0]
            what = ' ' + unit
            uptime = uptime.replace(what+'s', initial).replace(what, initial)
        return uptime

    def get_mem(self) -> list[str]:
        try:
            out = shell_command(['free', '--giga'])
            stats = out.splitlines()[1].split()[1:]

            cols = 'Ttl Usd Fre Sha Buf Avg'.split()
            head = '  ' + ''.join([f'{s:3}' for s in cols])
            vals = '   ' + ' '.join([f'{int(v):2}' for v in stats])
            return [head, vals]
        except:
            return ['mem unavailable']

    def get_cpus_pcents(self) -> list[str]:
        try:
            out = shell_command((f'mpstat -P ALL {config.MONITOR_CPU_INTERVAL} 1 '
                                 f'-o JSON').split())
            data = json.loads(out)
            loads = data['sysstat']['hosts'][0]['statistics'][0]['cpu-load']
            cpus = [l for l in loads if l['cpu'] not in ('all', '-1')]
            pcents = [int(c['usr']+.5) for c in cpus]

            pcents.sort(reverse=True)  # DEBATABLE
        except:
            return ['<CPUs: mpstat error>']
        lines = []
        items_per_line = int(self.chars_per_line/4)
        line = ''
        for i, pcent in enumerate(pcents):
            line += f'{pcent:3}'
            if len(line)+4 > self.chars_per_line:
                lines.append(line)
                line = ''
            else:
                line += ' '
        if line:
            lines.append(line)
        return lines


def shell_command(cmd: list[str], force_local: bool = False, check: bool = True) -> str:
    if config.MONITOR_SSH_AUTHORITY and not force_local:
        cmd = ['ssh', config.MONITOR_SSH_AUTHORITY] + cmd
    try:
        return subprocess.run(cmd, encoding='utf-8',
                              check=check, stdout=subprocess.PIPE).stdout
    except Exception as e:
        print(f'Error >>> {cmd}')
        raise


def shorten(txt: str) -> str:
    txt = txt.rstrip()
    return txt[:config.COLUMNS]
