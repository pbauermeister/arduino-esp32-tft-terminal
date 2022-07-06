from lib import *
from lib.app import App
import time
import random
import math
import datetime
import config
import socket
import subprocess
import json

PAGE_HOST_TIMEOUT = 8
PAGE_CPU_TIMEOUT = 60 - PAGE_HOST_TIMEOUT
PAGE_REFRESH = 2

CHOICE_EXIT = 1
CHOICE_NEXT = 2

class Monitor(App):

    def __init__(self, board):
        super().__init__(board)
        self.chars_per_line = int(config.WIDTH / 6.4)
        self.lines = int(config.WIDTH / 8)
        self.command = self.board.command
        self.boots = self.board.boots

        while True:
            ans =self.show_host()
            if ans == CHOICE_EXIT: return

            ans = self.show_cpu()
            if ans == CHOICE_EXIT: return
            if ans == None: return

    def make_header(self, title):
        self.command(f'waitButton 100 1')
        self.command(f'reset')
        self.command(f'fillRect 0 0 {config.WIDTH} 8 1')
        self.command(f'setTextColor 0')
        self.command(f'setCursor 1 0')
        self.command(f'print {title}')
        txt = 'C:next R:exit'
        w, h = self.get_text_size(txt)
        x = config.WIDTH - w - 3
        self.command(f'setCursor {x} 0')
        self.command(f'print {txt}')

        self.command(f'setTextColor 1')
        self.command(f'home')
        self.command(f'print \\n')

    def wait_button(self, timeout):
        start = datetime.datetime.now()
        until = start + datetime.timedelta(seconds=timeout)

        while True:
            ans = self.command('readButtons')
            if ans == 'C':
                return CHOICE_NEXT
            if self.boots != self.board.boots:
                return CHOICE_EXIT
            now = datetime.datetime.now()
            if now > until:
                return None

    def show_host(self):
        self.make_header('Host')
        self.command(f'display')
        users = self.get_nb_users()
        users = f'{users or "???"} user' + ('' if users==1 else 's')
        lines = [
            self.get_hostname(),
            self.get_ip(),
            self.get_uptime(),
            users,
            ] + self.get_mem()
        for l in lines:
            self.command(f'print {l}\\n')
        self.command(f'display')
        return self.wait_button(PAGE_HOST_TIMEOUT)

    def show_cpu(self):
        for i in range(int(PAGE_CPU_TIMEOUT/PAGE_REFRESH)):
            self.make_header('CPU %')
            if i==0: self.command(f'display')
            lines = self.get_cpus_pcents()

            if len(lines) < 3:
                lines.append('')
                lines += self.get_mem()[1:]

            if len(lines) < 7:
                self.command(f'print \\n')
            for l in lines:
                self.command(f'print {l}\\n')
            self.command(f'display')
            choice = self.wait_button(PAGE_REFRESH)
            print('s', choice)
            if choice:
                return choice
        return None

    def get_hostname(self):
        try:
            return socket.gethostname()
        except:
            return '<hostname unavail>'

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except:
            return '<ip addr unavail>'

    def get_nb_users(self):
        try:
            out = subprocess.check_output(['who'], encoding='utf-8').strip()
            return len(out.splitlines())
        except:
            return None

    def get_uptime(self):
        try:
            uptime = subprocess.check_output(['uptime', '-p'], encoding='utf-8').strip()
        except:
            return '<uptime unavail>'
        uptime = uptime.replace(' hours', 'h').replace(' hour', 'h')
        uptime = uptime.replace(' minutes', 'm').replace(' minute', 'm')
        uptime = uptime.replace(' days', 'd').replace(' day', 'd')
        return uptime

    def get_mem(self):
        try:
            out = subprocess.check_output(['free', '--giga'], encoding='utf-8').strip()
            stats = out.splitlines()[1].split()[1:]

            cols = 'Ttl Usd Fre Sha Buf Avg'.split()
            head = '  ' + ''.join([f'{s:3}' for s in cols])
            vals = '   ' + ' '.join([f'{int(v):2}' for v in stats])
            return ['mem [GB]:', head, vals]
        except:
            return ['mem unavailable']

    def get_cpus_pcents(self):
        try:
            out = subprocess.check_output('mpstat -P ALL 1 1 -o JSON'.split(),
                                          encoding='utf-8')
            data = json.loads(out)
            loads = data['sysstat']['hosts'][0]['statistics'][0]['cpu-load']
            cpus = [l for l in loads if l['cpu'] != 'all']
            pcents = [int(c['usr']+.5) for c in cpus]
        except:
            return ['<cpus: mpstat error>']
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
