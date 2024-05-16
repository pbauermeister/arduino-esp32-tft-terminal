import json

import config
from app import TimeEscaper
from app.monitor_host import MonitorBase
from lib.board import Board

CHOICE_EXIT = 1
CHOICE_NEXT = 2
CHOICE_RESET = 3


class MonitorCpus(MonitorBase):
    def __init__(self, board: Board):
        super().__init__(board, auto_read=True)
        self.set_pane_text_attr()
        cw, _ = self.gfx.get_text_bounds(0, 0, '9')
        self.chars_per_line = int(config.WIDTH / cw)

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
            self.gfx.set_cursor(0, config.TEXT_SCALING * 12)
            lines = cpus
            for l in lines:
                self.gfx.print(f'{l}\\n')

            # Mem
            if len(lines) <= 4:
                self.gfx.set_cursor(0, config.TEXT_SCALING * 6 * 8)
                for l in mem:
                    self.gfx.print(f'{l}\\n')

            self.gfx.display()

    def get_cpus_pcents(self) -> list[str]:
        try:
            out = self.shell_command(
                (f'mpstat -P ALL {config.MONITOR_CPU_INTERVAL} 1 ' f'-o JSON').split()
            )
            data = json.loads(out)
            loads = data['sysstat']['hosts'][0]['statistics'][0]['cpu-load']
            cpus = [l for l in loads if l['cpu'] not in ('all', '-1')]
            pcents = [int(c['usr'] + 0.5) for c in cpus]

            pcents.sort(reverse=True)  # DEBATABLE
        except:
            return ['<CPUs: mpstat error>']
        lines = []
        items_per_line = int(self.chars_per_line / 4)
        line = ''
        for i, pcent in enumerate(pcents):
            line += f'{pcent:3}'
            if len(line) + 4 > self.chars_per_line:
                lines.append(line)
                line = ''
            else:
                line += ' '
        if line:
            lines.append(line)
        return lines
