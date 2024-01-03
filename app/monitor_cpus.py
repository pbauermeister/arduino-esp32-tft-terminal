import datetime
import json
import socket
import subprocess
import threading
import time

import config
from app import App, TimeEscaper
from lib.board import Board

CHOICE_EXIT = 1
CHOICE_NEXT = 2
CHOICE_RESET = 3


class MonitorCpus(App):

    def __init__(self, board: Board):
        super().__init__(board, auto_read=True, name="Monitor CPUs")
        self.set_pane_text_attr()
        cw, _ = self.gfx.get_text_bounds(0, 0, '9')
        self.chars_per_line = int(config.WIDTH / cw)

    def set_pane_text_attr(self) -> None:
        self.gfx.set_text_size(1, 1)
        self.gfx.set_text_color(128, 128, 128)

    def _run(self) -> bool:
        title = 'CPU % and memory'
        escaper = TimeEscaper(self)
        self.gfx.set_auto_read_buttons_on()
        while True:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            cpus = self.get_cpus_pcents()
            mem = self.get_mem()

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

    def show_header(self, title: str, menu: str | None = None, with_banner: bool = False) -> None:
        self.gfx.set_text_color(255, 255, 255)
        self.gfx.set_text_size(1, 1)
        super().show_header(title, '', with_banner)
        self.set_pane_text_attr()

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
