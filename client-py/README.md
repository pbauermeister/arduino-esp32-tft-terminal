# client-py — Python client

The computer-side program of the
[Arduino ESP32 TFT Terminal](../README.md). It owns all application logic and
drives the board over USB, sending command lines and reading answers.

## Requirements

- Python 3.10+ on Linux.
- A flashed board (see [`../server-esp32s3-rtft/`](../server-esp32s3-rtft/)) connected over USB.
- Dependencies: `numpy`, `pyserial`, `claude-busy-monitor`.

## Running

From source (a pip/uv-installable package is on the way — see [`../TODO.md`](../TODO.md)):

```bash
pip install -r requirements.txt
./run.py -h           # list options and apps
./run.py --demo       # cycle through all apps
./run.py --only cube  # run a single app
```

## Layout

- `app/` — one module + class per app (`quix.py` is the template).
- `lib/` — board communication: serial channel, command protocol, `Board`, `Gfx`, CLI args.
- `run.py` — entry point; registers the apps.
- `config.py` — runtime configuration (also exposed as CLI flags).

## Writing a new app

1. Study [`app/quix.py`](app/quix.py) as a template.
2. Create a new module and class.
3. Register the class in [`run.py`](run.py).

## Development

- Format + lint with [ruff](https://docs.astral.sh/ruff/): `make format` / `make lint` (from the repo root).
- See the top-level [README](../README.md) and [`../TODO.md`](../TODO.md) for the wider toolchain.
