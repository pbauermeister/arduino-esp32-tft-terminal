import json
import re
import subprocess
import threading
from dataclasses import dataclass

import config
from app import App, TimeEscaper
from lib.board import Board

DX = 4
Y_MARGIN = 9

COLOR_TX = 255, 64, 64
COLOR_RX = 64, 255, 64
COLOR_AXIS = COLOR_LABELS = 96, 96, 96

TRAFFIC_SCALING = 20 * 1000.


@dataclass
class CpuInfo:
    rgb: tuple[int, int, int]
    pcent: int
    previous_pcent: int


@dataclass
class Traffic:
    rx: int = 0
    tx: int = 0
    previous_rx: int | None = None
    previous_tx: int | None = None
    previous_rx_scaled = 0
    previous_tx_scaled = 0


class MonitorGraph(App):

    def __init__(self, board: Board):
        super().__init__(board, auto_read=False, name="Monitor Graph")
        self.set_pane_text_attr()
        cw, ch = self.gfx.get_text_bounds(0, 0, '9')
        self.chars_per_line = int(config.WIDTH / cw)
        self.lines = int(config.WIDTH / ch)

        self.mutex = threading.Lock()
        self.changed = False
        self.stop = False

    def set_pane_text_attr(self) -> None:
        self.gfx.set_text_size(1, 1)
        self.gfx.set_fg_color(128, 128, 128)
        self.gfx.set_text_color(1)

    def make_cpu_infos(self, pcents: list[int] | None) -> list[CpuInfo]:
        if not pcents:
            return []
        nb_cpus = len(pcents)
        cpu_infos: list[CpuInfo] = []
        dhue = 360. / nb_cpus
        for i, _ in enumerate(pcents):
            hue = 360 - dhue*i
            r, g, b = _hsv_to_rgb(hue, 100, 100)
            cpu_infos.append(CpuInfo((r, g, b), 0, 0))
        return cpu_infos

    def _run(self) -> bool:
        escaper = TimeEscaper(self)
        cursor = 0
        last_bar_x: int | None = None
        last_cpus_ttl: int | None = None

        pcents = self.get_cpus_pcents()
        cpu_infos: list[CpuInfo] = []
        nb_cpus = len(pcents)
        traffic = Traffic()

        self.gfx.set_auto_read_buttons_on()

        while True:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            # get CPU percents
            pcents = self.get_cpus_pcents()
            if len(pcents) != len(cpu_infos):
                cpu_infos = self.make_cpu_infos(pcents)
                nb_cpus = len(pcents)
            for i, pcent in enumerate(pcents):
                cpu_infos[i].pcent = pcent

            # total CPUs
            cpus_ttl = int(sum([cpu_graph.pcent/100. for cpu_graph in cpu_infos]
                               ) / nb_cpus * 100 + .5)

            # erase prev values
            if cursor:
                self.gfx.fill_rect(cursor+1, 0, DX, config.HEIGHT-1, 0)
            else:
                self.gfx.fill_rect(0, 0, DX+1, config.HEIGHT-1, 0)

            # draw axis and current time
            last_bar_x = self.render_axis(cursor, last_bar_x)

            # draw each CPUs
            for cpu_graph in cpu_infos:
                x0 = cursor
                y0 = self.make_cpu_y(cpu_graph.previous_pcent)
                x1 = cursor + DX
                y1 = self.make_cpu_y(cpu_graph.pcent)
                self.gfx.set_fg_color(*cpu_graph.rgb)
                self.gfx.draw_line(x0, y0, x1, y1, 1)
                cpu_graph.previous_pcent = cpu_graph.pcent

            # draw traffic
            traffic.rx, traffic.tx = self.get_traffic()
            if traffic.previous_rx is not None and traffic.previous_tx is not None:
                rx_delta = traffic.rx - traffic.previous_rx
                tx_delta = traffic.tx - traffic.previous_tx
                print(f'traffic: rx={rx_delta} tx={tx_delta}')

                rx_scaled = min(int(rx_delta/TRAFFIC_SCALING * 100), 100)
                tx_scaled = min(int(tx_delta/TRAFFIC_SCALING * 100), 100)
                self.render_traffic(cursor, traffic, rx_scaled, tx_scaled)

                traffic.previous_rx_scaled = rx_scaled
                traffic.previous_tx_scaled = tx_scaled
            traffic.previous_rx, traffic.previous_tx = traffic.rx, traffic.tx

            # draw labels
            self.render_labels(len(cpu_infos), cpus_ttl, last_cpus_ttl)
            last_cpus_ttl = cpus_ttl

            # display
            self.gfx.display()
            cursor += DX
            if cursor+DX >= config.WIDTH:
                cursor = 0

            print(f'CPUs: {cpus_ttl}%', pcents)

    def render_axis(self, cursor: int, last_bar_x: int | None) -> int | None:
        # erase prev marker
        if last_bar_x is not None:
            x0 = last_bar_x
            y0 = 0
            x1 = last_bar_x
            y1 = config.HEIGHT-1
            self.gfx.draw_line(x0, y0, x1, y1, 0)

        # draw t axis
        self.gfx.set_fg_color(*COLOR_AXIS)

        y = self.make_cpu_y(0)+1
        self.gfx.draw_fast_hline(0, y, config.WIDTH, 1)

        y = self.make_net_y(0)+1
        self.gfx.draw_fast_hline(0, y, config.WIDTH, 1)

        # draw marker
        bar_x = cursor + DX + 1
        if bar_x < config.WIDTH:
            x0 = bar_x
            y0 = 0
            x1 = bar_x
            y1 = config.HEIGHT-1
            self.gfx.draw_line(x0, y0, x1, y1, 1)
            last_bar_x = bar_x
        else:
            last_bar_x = None
        return last_bar_x

    def render_traffic(self, cursor: int, traffic: Traffic,
                       rx_scaled: int, tx_scaled: int) -> None:
        x0 = cursor
        x1 = cursor + DX

        # tx
        y0 = self.make_net_y(traffic.previous_tx_scaled)
        y1 = self.make_net_y(tx_scaled)
        self.gfx.set_fg_color(*COLOR_TX)
        self.gfx.draw_line(x0, y0, x1, y1, 1)

        # rx
        y0 = self.make_net_y(traffic.previous_rx_scaled)
        y1 = self.make_net_y(rx_scaled)
        self.gfx.set_fg_color(*COLOR_RX)
        self.gfx.draw_line(x0, y0, x1, y1, 1)

    def render_labels(self, nb_cpus: int,  cpus_ttl: int, last_cpus_ttl: int | None) -> None:
        self.gfx.set_text_size(1, 1)
        self.gfx.set_fg_color(*COLOR_LABELS)
        self.gfx.set_text_color(1)
        dy = 4

        # CPUs
        cpus_label = f'{nb_cpus} CPUs '
        y = self.make_cpu_y(0)
        self.gfx.set_cursor(0,  y + dy)
        self.gfx.print(cpus_label)

        if last_cpus_ttl is not None:
            xy = self.gfx
            self.gfx.set_text_color(0)
            self.gfx.print(f'{last_cpus_ttl}%')
            self.gfx.set_text_color(1)

        self.gfx.set_cursor(0,  y + dy)
        self.gfx.print(cpus_label)
        self.gfx.print(f'{cpus_ttl}%')
        last_cpus_ttl = cpus_ttl

        # Net
        y = self.make_net_y(0)
        self.gfx.set_cursor(0, y + dy)
        self.gfx.print('Net')

        # - tx
        self.gfx.set_fg_color(*COLOR_TX)
        self.gfx.set_text_color(1)
        self.gfx.print(' -')
        self.gfx.set_fg_color(*COLOR_LABELS)
        self.gfx.set_text_color(1)
        self.gfx.print('tx')

        # - rx
        self.gfx.set_fg_color(*COLOR_RX)
        self.gfx.set_text_color(1)
        self.gfx.print(' -')
        self.gfx.set_fg_color(*COLOR_LABELS)
        self.gfx.set_text_color(1)
        self.gfx.print('rx')

    def make_cpu_y(self, pcent: int) -> int:
        h = config.HEIGHT/2 - Y_MARGIN*2
        return int(h * (1 - pcent / 100.)+.5) + Y_MARGIN * 0

    def make_net_y(self, pcent: int) -> int:
        h = config.HEIGHT/2 - Y_MARGIN*2
        return int(h * (2 - pcent / 100.)+.5) + Y_MARGIN * 2

    def get_mem(self) -> list[str]:
        try:
            out = _shell_command(['free', '--giga'])
            stats = out.splitlines()[1].split()[1:]

            cols = 'Ttl Usd Fre Sha Buf Avg'.split()
            head = '  ' + ''.join([f'{s:3}' for s in cols])
            vals = '   ' + ' '.join([f'{int(v):2}' for v in stats])
            return [head, vals]
        except:
            return ['mem unavailable']

    def get_cpus_pcents(self) -> list[int]:
        try:
            # interval = config.MONITOR_CPU_INTERVAL
            interval = 1
            out = _shell_command((f'mpstat -P ALL {interval} 1 '
                                 f'-o JSON').split())
            data = json.loads(out)
            loads = data['sysstat']['hosts'][0]['statistics'][0]['cpu-load']
            cpus = [l for l in loads if l['cpu'] not in ('all', '-1')]
            pcents = [int(c['usr']+.5) for c in cpus]
            pcents = sorted(pcents)
        except:
            return []
        return pcents

    RX_REGEX = re.compile('RX packets .*bytes ([0-9]+)')
    TX_REGEX = re.compile('TX packets .*bytes ([0-9]+)')

    def get_traffic(self) -> tuple[int, int]:
        out = _shell_command(['netstat', '-e', '-n',  '-i'])
        rx = sum([int(m) for m in self.RX_REGEX.findall(out)])
        tx = sum([int(m) for m in self.TX_REGEX.findall(out)])
        return rx, tx


def _shell_command(cmd: list[str], force_local: bool = False, check: bool = True) -> str:
    if config.MONITOR_SSH_AUTHORITY and not force_local:
        cmd = ['ssh', config.MONITOR_SSH_AUTHORITY] + cmd
    try:
        return subprocess.run(cmd, encoding='utf-8',
                              check=check, stdout=subprocess.PIPE).stdout
    except Exception as e:
        print(f'Error >>> {cmd}')
        raise


def _hsv_to_rgb(hue: int | float, sat: int | float, val: int | float) -> tuple[int, int, int]:
    hue = min(hue, 360)
    hue = max(hue, 0)
    sat = min(sat, 100)
    sat = max(sat, 0)
    val = min(val, 100)
    val = max(val, 0)

    s = sat / 100.
    v = val / 100.
    c = s * v
    x = c * (1 - abs(((hue / 60.0) % 2.) - 1))
    m = v - c

    if hue >= 0 and hue < 60:
        r = c
        g = x
        b = 0.
    elif hue >= 60 and hue < 120:
        r = x
        g = c
        b = 0.
    elif hue >= 120 and hue < 180:
        r = 0
        g = c
        b = x
    elif hue >= 180 and hue < 240:
        r = 0.
        g = x
        b = c
    elif hue >= 240 and hue < 300:
        r = x
        g = 0.
        b = c
    else:
        r = c
        g = 0.
        b = x

    red = int((r + m) * 255+.5)
    green = int((g + m) * 255+.5)
    blue = int((b + m) * 255+.5)
    return red, green, blue
