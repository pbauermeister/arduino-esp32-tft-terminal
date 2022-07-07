from lib import *
from lib.app import App
import time
import random
import math
import datetime
import config
import socket
import subprocess
import textwrap
import json
import threading

CHOICE_EXIT = 1
CHOICE_NEXT = 2

class Monitor(App):

    def __init__(self, board):
        self.boots = board.boots
        super().__init__(board)
        self.chars_per_line = int(config.WIDTH / 6.4)
        self.lines = int(config.WIDTH / 8)
        self.command = self.board.command
        self.mutex = threading.Lock()

        while True:
            if config.MONITOR_HOST_TIMEOUT:
                ans = self.show_host()
                if ans == CHOICE_EXIT: return

            if config.MONITOR_CPU_TIMEOUT:
                ans = self.show_cpu()
                if ans == CHOICE_EXIT: return

            if ans is not None: continue
            if not config.MONITOR_ONLY: return

    def show_header(self, title, with_banner=False):
        super().show_header(title, 'C:next R:exit', with_banner)

    def wait_no_button(self):  # TODO: move to base class
        while self.command('readButtons') != NONE:
            pass

    def wait_button(self, timeout):  # TODO: move to parent, also read_buttons
        if timeout is not None:
            start = datetime.datetime.now()
            until = start + datetime.timedelta(seconds=timeout)

        while True:
            ans = self.command('readButtons')
            if ans == 'C':
                return CHOICE_NEXT
            if self.boots != self.board.boots:
                return CHOICE_EXIT
            if timeout is None:
                return None
            now = datetime.datetime.now()
            if now >= until:
                return None

    def show_host(self):
        title = 'Host'
        self.show_header(title, with_banner=True)
        self.command(f'display')

        self.wait_no_button()
        self.board.begin_read_buttons()

        users = self.get_nb_users()
        users = f'{users or "???"} user' + ('' if users==1 else 's')

        date = self.get_date()

        lines = [
            self.get_hostname(),
            self.get_ip(),
            users,
            date,
            self.get_uptime(),
            ] + self.get_mem()

        if 'C' in self.board.end_read_buttons():
            return CHOICE_NEXT

        self.show_header(title)
        for l in lines:
            l = shorten(l)
            self.command(f'print {l}\\n')
        self.command(f'display')

        return self.wait_button(config.MONITOR_HOST_TIMEOUT)

    def show_cpu(self):
        start = datetime.datetime.now()
        until = start + datetime.timedelta(seconds=config.MONITOR_CPU_TIMEOUT)

        th = threading.Thread(target=self.task)
        self.stop = False
        th.start()

        title = 'CPU %'
        self.show_header(title, with_banner=True)
        self.command(f'display')
        self.wait_no_button()

        while True:
            cpus, mem = None, None
            with self.mutex:
                if self.changed:
                    cpus, mem = self.cpus, self.mem
                    self.changed = False
            if cpus is not None:
                self.show_header(title)
                # CPUs
                self.command(f'setCursor 0 12')
                lines = cpus
                for l in lines:
                    self.command(f'print {l}\\n')
                # Mem
                if len(lines) <= 4:
                    self.command(f'setCursor 0 {6*8}')
                    for l in mem:
                        self.command(f'print {l}\\n')
                self.command(f'display')

            choice = self.wait_button(timeout=None)
            if choice:
                self.stop = True
                #th.join()
                return choice

            now = datetime.datetime.now()
            if now >= until:
                self.stop = True
                #th.join()
                return None

    def task(self):
        self.changed = False
        while not self.stop:
            cpus = self.get_cpus_pcents()
            mem = self.get_mem()
            if self.stop: break
            with self.mutex:
                self.cpus, self.mem = cpus, mem
                self.changed = True

    def get_hostname(self):
        try:
            return command(['hostname'])
        except:
            return '<hostname unavail>'

    def get_ip(self):
        if config.REMOTE_SSH_AUTHORITY:
            return self.get_remote_ip()
        else:
            return self.get_local_ip()

    def get_remote_ip(self):
        try:
            host = config.REMOTE_SSH_AUTHORITY.split('@')[-1]
            out = command(['host', host], force_local=True, check=False)
            return out.splitlines()[0].split(' ')[-1]
        except:
            return '<rmt ip addr unavail>'

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except:
            return '<ip addr unavail>'

    def get_nb_users(self):
        try:
            out = command(['who'])
            return len(out.splitlines())
        except:
            return None

    def get_date(self):
        try:
            out = command(['date', '--rfc-3339=seconds'])
            return out.split('+')[0]
        except:
            return '<date unavail>'

    def get_uptime(self):
        try:
            uptime = command(['uptime', '-p'])
        except:
            return '<uptime unavail>'
        for unit in 'hour', 'minute', 'day', 'week', 'month', 'year':
            initial = unit[0]
            what = ' ' + unit
            uptime = uptime.replace(what+'s', initial).replace(what, initial)
        return uptime

    def get_mem(self):
        try:
            out = command(['free', '--giga'])
            stats = out.splitlines()[1].split()[1:]

            cols = 'Ttl Usd Fre Sha Buf Avg'.split()
            head = '  ' + ''.join([f'{s:3}' for s in cols])
            vals = '   ' + ' '.join([f'{int(v):2}' for v in stats])
            return [head, vals]
        except:
            return ['mem unavailable']

    def get_cpus_pcents(self):
        try:
            out = command((f'mpstat -P ALL {config.MONITOR_CPU_INTERVAL} 1 '
                           f'-o JSON').split())
            data = json.loads(out)
            loads = data['sysstat']['hosts'][0]['statistics'][0]['cpu-load']
            cpus = [l for l in loads if l['cpu'] != 'all']
            pcents = [int(c['usr']+.5) for c in cpus]
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
        if line: lines.append(line)
        return lines


def command(cmd, force_local=False, check=True):
    if config.REMOTE_SSH_AUTHORITY and not force_local:
        cmd = ['ssh', config.REMOTE_SSH_AUTHORITY] + cmd
    try:
        return subprocess.run(cmd, encoding='utf-8',
                              check=check, stdout=subprocess.PIPE).stdout
    except Exception as e:
        print(f'Error >>> {cmd}')
        raise

def shorten(txt):
    txt = txt.rstrip()
    return txt[:config.COLUMNS]
