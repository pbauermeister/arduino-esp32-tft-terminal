import json
import re
import threading
import time
from dataclasses import dataclass

import config
from app import TimeEscaper
from app.monitor_host import MonitorBase
from lib.board import Board

DX = 4
Y_MARGIN = 8 * config.TEXT_SCALING + 1
Y_SPACING = 8

COLOR_TX = 255, 64, 64
COLOR_RX = 64, 255, 64
COLOR_AXIS = COLOR_LABELS = 96, 96, 96
COLOR_MARKER = 192, 192, 192
COLOR_ERROR = 255, 64, 64
TRAFFIC_SCALING = 20 * 1000.

RX_REGEX = re.compile('RX packets .*bytes ([0-9]+)')
TX_REGEX = re.compile('TX packets .*bytes ([0-9]+)')


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


class State:
    def __init__(self) -> None:
        self.last_bar_x: int | None = None
        self.last_cpus_ttl: int | None = None
        self.pcents: list[int] = []
        self.cpu_infos: list[CpuInfo] = []
        self.nb_cpus: int = 0
        self.cpus_ttl: int = 0
        self.traffic: Traffic = Traffic()
        self.errors: set[int] = set()


class MonitorGraph(MonitorBase):

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
        self.gfx.set_text_color(128, 128, 128)

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

    def handle_cpus(self, cursor: int, state: State) -> None:
        # get CPU percents
        pcents, err = self.get_cpus_pcents()
        if err:
            y = self.make_cpu_y(0) - config.TEXT_SCALING * 10
            self.gfx.set_cursor(00, y)
            self.gfx.set_text_color(*COLOR_ERROR)
            self.gfx.set_text_size(1, 1)
            self.gfx.print(err)
            state.errors.add(1)
            return
        state.errors.discard(1)

        if len(pcents) != state.nb_cpus:
            state.cpu_infos = self.make_cpu_infos(pcents)
            state.nb_cpus = len(pcents)
        for i, pcent in enumerate(pcents):
            state.cpu_infos[i].pcent = pcent

        # total CPUs
        state.cpus_ttl = int(sum([cpu_graph.pcent/100. for cpu_graph in state.cpu_infos]
                                 ) / state.nb_cpus * 100 + .5)
        print(f'CPUs: {state.cpus_ttl}%', pcents)

        # erase prev values
        if cursor:
            self.gfx.fill_rect(cursor+1, 0, DX, config.HEIGHT-1, 0)
        else:
            self.gfx.fill_rect(0, 0, DX+1, config.HEIGHT-1, 0)

        # draw each CPUs
        for cpu_graph in state.cpu_infos:
            x0 = cursor
            y0 = self.make_cpu_y(cpu_graph.previous_pcent)
            x1 = cursor + DX
            y1 = self.make_cpu_y(cpu_graph.pcent)
            self.gfx.set_fg_color(*cpu_graph.rgb)
            self.gfx.draw_line(x0, y0, x1, y1, 1)
            cpu_graph.previous_pcent = cpu_graph.pcent

    def handle_traffic(self, cursor: int, state: State) -> None:
        # draw traffic
        state.traffic.rx, state.traffic.tx, err = self.get_traffic()
        if err:
            y = self.make_net_y(0) - config.TEXT_SCALING * 10
            self.gfx.set_cursor(00, y)
            self.gfx.set_text_color(*COLOR_ERROR)
            self.gfx.set_text_size(1, 1)
            self.gfx.print(err)
            state.errors.add(2)
            return
        state.errors.discard(2)

        if state.traffic.previous_rx is not None and state.traffic.previous_tx is not None:
            rx_delta = state.traffic.rx - state.traffic.previous_rx
            tx_delta = state.traffic.tx - state.traffic.previous_tx
            print(f'traffic: rx={rx_delta} tx={tx_delta}')

            rx_scaled = min(int(rx_delta/TRAFFIC_SCALING * 100), 100)
            tx_scaled = min(int(tx_delta/TRAFFIC_SCALING * 100), 100)
            self.draw_traffic(cursor, state.traffic, rx_scaled, tx_scaled)

            state.traffic.previous_rx_scaled = rx_scaled
            state.traffic.previous_tx_scaled = tx_scaled
        state.traffic.previous_rx = state.traffic.rx
        state.traffic.previous_tx = state.traffic.tx

    def _run(self) -> bool:
        escaper = TimeEscaper(self)
        cursor = 0
        state = State()

        self.gfx.set_auto_read_buttons_on()

        while True:
            btns = self.board.auto_read_buttons()
            if 'R' in btns:
                return True
            if btns:
                return False
            if escaper.check():
                return False

            self.erase_marker(state)

            errs: set[int] = set()
            errs |= state.errors
            self.handle_cpus(cursor, state)
            self.handle_traffic(cursor, state)
            errs_changed = errs != state.errors

            # draw labels
            self.draw_labels(state)
            state.last_cpus_ttl = state.cpus_ttl

            # draw axis and current time
            self.draw_axis_and_marker(cursor, state)

            # display
            self.gfx.display()
            if (errs_changed):
                self.gfx.clear()

            cursor += DX
            if cursor+DX >= config.WIDTH:
                cursor = 0

    def erase_marker(self, state: State) -> None:
        # erase prev marker
        if state.last_bar_x is not None:
            x0 = state.last_bar_x
            y0 = 0
            x1 = state.last_bar_x
            y1 = config.HEIGHT-1
            self.gfx.draw_line(x0, y0, x1, y1, 0)

    def draw_axis_and_marker(self, cursor: int, state: State) -> None:
        # draw t axis
        self.gfx.set_fg_color(*COLOR_AXIS)

        y = self.make_cpu_y(0)+1
        self.gfx.draw_fast_hline(0, y, config.WIDTH, 1)

        y = self.make_net_y(0)+1
        self.gfx.draw_fast_hline(0, y, config.WIDTH, 1)

        # draw marker
        bar_x = cursor + DX + 1
        self.gfx.set_fg_color(*COLOR_MARKER)
        if bar_x < config.WIDTH:
            x0 = bar_x
            y0 = 0
            x1 = bar_x
            y1 = config.HEIGHT-1
            self.gfx.draw_line(x0, y0, x1, y1, 1)
            state.last_bar_x = bar_x
        else:
            state.last_bar_x = None

    def draw_traffic(self, cursor: int, traffic: Traffic,
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

    def draw_labels(self, state: State) -> None:
        self.gfx.set_text_size(1, 1)
        self.gfx.set_text_color(*COLOR_LABELS)
        dy = 4

        # CPUs
        cpus_label = f'{state.nb_cpus} CPUs '
        y = self.make_cpu_y(0)
        self.gfx.set_cursor(0,  y + dy)
        self.gfx.print(cpus_label)

        if state.last_cpus_ttl is not None:
            xy = self.gfx
            self.gfx.set_text_color(0, 0, 0)
            self.gfx.print(f'{state.last_cpus_ttl}%')
            self.gfx.set_text_color(*COLOR_LABELS)

        self.gfx.set_cursor(0,  y + dy)
        self.gfx.print(cpus_label)
        self.gfx.print(f'{state.cpus_ttl}%')
        last_cpus_ttl = state.cpus_ttl

        # Net
        y = self.make_net_y(0)
        self.gfx.set_cursor(0, y + dy)
        self.gfx.print('Net')

        # - tx
        self.gfx.set_text_color(*COLOR_TX)
        self.gfx.print(' -')
        self.gfx.set_text_color(*COLOR_LABELS)
        self.gfx.print('tx')

        # - rx
        self.gfx.set_text_color(*COLOR_RX)
        self.gfx.print(' -')
        self.gfx.set_text_color(*COLOR_LABELS)
        self.gfx.print('rx')

    def make_cpu_y(self, pcent: int) -> int:
        h = (config.HEIGHT - Y_SPACING)/2 - Y_MARGIN
        return int(h * (1 - pcent / 100.)+.5)

    def make_net_y(self, pcent: int) -> int:
        h = (config.HEIGHT - Y_SPACING)/2 - Y_MARGIN
        return int(h * (2 - pcent / 100.)+.5) + Y_MARGIN + Y_SPACING - 1

    def get_cpus_pcents(self) -> tuple[list[int], str]:
        try:
            # interval = config.MONITOR_CPU_INTERVAL
            interval = 1
            out = self.shell_command((f'mpstat -P ALL {interval} 1 '
                                      f'-o JSON').split())
            data = json.loads(out)
            loads = data['sysstat']['hosts'][0]['statistics'][0]['cpu-load']
            cpus = [l for l in loads if l['cpu'] not in ('all', '-1')]
            pcents = [int(c['usr']+.5) for c in cpus]
            pcents = sorted(pcents)
        except:
            return [], '<mpstat error>'
        return pcents, ''

    def get_traffic(self) -> tuple[int, int, str]:
        try:
            out = self.shell_command(['netstat', '-e', '-n',  '-i'])
            rx = sum([int(m) for m in RX_REGEX.findall(out)])
            tx = sum([int(m) for m in TX_REGEX.findall(out)])
            return rx, tx, ''
        except:
            return 0, 0, '<netstat error>'


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
