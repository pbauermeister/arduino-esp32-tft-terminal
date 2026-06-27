"""Tier 1 — mpstat-JSON parsing in the CPU monitor.

The parse is exercised with captured-shape fixture output; the board is faked
(via `fake_board`) and the shell call is monkeypatched, so neither hardware nor
`mpstat` is needed.
"""

import json

import pytest

from arduino_esp32_tft_terminal.app.monitor_cpus import MonitorCpus
from arduino_esp32_tft_terminal.lib.board import Board

MPSTAT_JSON = json.dumps(
    {
        'sysstat': {
            'hosts': [
                {
                    'statistics': [
                        {
                            'cpu-load': [
                                {'cpu': 'all', 'usr': 30.0},
                                {'cpu': '0', 'usr': 10.4},
                                {'cpu': '1', 'usr': 50.6},
                            ]
                        }
                    ]
                }
            ]
        }
    }
)


def test_parses_per_cpu_percentages(
    fake_board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = MonitorCpus(fake_board)
    monkeypatch.setattr(app, 'shell_command', lambda *a, **k: MPSTAT_JSON)
    out = ' '.join(app.get_cpus_pcents())
    assert '51' in out  # round(50.6)
    assert '10' in out  # round(10.4)


def test_reports_error_on_failure(
    fake_board: Board, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = MonitorCpus(fake_board)

    def boom(*a: object, **k: object) -> str:
        raise RuntimeError('no mpstat')

    monkeypatch.setattr(app, 'shell_command', boom)
    assert app.get_cpus_pcents() == ['<CPUs: mpstat error>']
