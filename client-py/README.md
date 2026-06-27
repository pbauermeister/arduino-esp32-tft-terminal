# client-py — Python client

The computer-side program of the
[Arduino ESP32 TFT Terminal](../README.md). It owns all application logic and
drives the board over USB, sending command lines and reading answers.

## Requirements

- Python 3.10+ on Linux.
- A flashed board (see [`../server-esp32s3-rtft/`](../server-esp32s3-rtft/)) connected over USB.
- Dependencies: `numpy`, `pyserial`, `claude-busy-monitor`.

## Running

Install the `arduino-esp32-tft-terminal` command (not on PyPI yet — install from this directory; see [`../TODO.md`](../TODO.md)):

```bash
uv tool install .                         # installs the command
arduino-esp32-tft-terminal -h             # list options and apps
arduino-esp32-tft-terminal --demo         # cycle through all apps
arduino-esp32-tft-terminal --only cube    # run a single app
```

For development, use an editable install (`uv pip install -e .` in a venv).

## Layout

Package source lives under `src/arduino_esp32_tft_terminal/`:

- `app/` — one module + class per app (`quix.py` is the template).
- `lib/` — board communication: serial channel, command protocol, `Board`, `Gfx`, CLI args.
- `cli.py` — entry point (`main()`); registers the apps.
- `config.py` — runtime configuration (also exposed as CLI flags).

## Writing a new app

1. Study [`src/arduino_esp32_tft_terminal/app/quix.py`](src/arduino_esp32_tft_terminal/app/quix.py) as a template.
2. Create a new module and class.
3. Register the class in [`src/arduino_esp32_tft_terminal/cli.py`](src/arduino_esp32_tft_terminal/cli.py).

## Development

- Format + lint with [ruff](https://docs.astral.sh/ruff/): `make format` / `make lint` (from the repo root).
- See the top-level [README](../README.md) and [`../TODO.md`](../TODO.md) for the wider toolchain.
