# Arduino ESP32 TFT Terminal

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Board: ESP32-S3 Reverse TFT](https://img.shields.io/badge/board-ESP32--S3%20Reverse%20TFT-blue.svg)](https://www.adafruit.com/product/5345)

A small gadget with a colour TFT display, enclosed in a 3D-printed case and
driven from your computer over USB. It runs performance monitors, games, and
graphical demos — and is easy to extend.

The display is the [Adafruit ESP32-S3 Reverse TFT Feather](https://www.adafruit.com/product/5345):
an ESP32-S3 board with a 240×135 colour TFT on its back.

This repository provides all three parts:

- **[`server-esp32s3-rtft/`](server-esp32s3-rtft/)** — the Arduino firmware sketch (C++): a graphical server exposing TFT drawing primitives and button readout over USB; holds no app logic.
- **[`client-py/`](client-py/)** — the Python client (Linux): owns all app logic and the ready-to-run apps; drives the board by sending command lines and reading answers.
- **[`case-esp32s3-rtft/`](case-esp32s3-rtft/)** — the OpenSCAD 3D-printed case and cap.

The board maps most commands directly to TFT library calls; the contract
between the two sides is the [USB protocol](README-protocol.md).

![Asteriods on the TFT](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_133408-thumb.png "Asteriods running on the gadget")

## Apps

Run any of the bundled apps, or write your own:

- **Monitors** — `claude-monitor`, `monitor-host`, `monitor-cpus`, `monitor-graph` (local or remote computer).
- **Games** — `asteriods`.
- **Physics** — `collisions-elastic`, `collisions-gravity`, `bubbles-soap`, `bubbles-air`.
- **Graphics** — `cube` (3D), `starfield`, `tunnel`, `quix`, `fill`.

## Quick start

The client installs as the `arduino-esp32-tft-terminal` command. It is not on
PyPI yet — install from the cloned source for now (see [`TODO.md`](TODO.md)).
You need a flashed board connected over USB (see [Installing](#installing)).

```bash
git clone https://github.com/pbauermeister/arduino-esp32-tft-terminal.git
cd arduino-esp32-tft-terminal/client-py
uv tool install .                         # installs the `arduino-esp32-tft-terminal` command
arduino-esp32-tft-terminal -h             # list options and apps
arduino-esp32-tft-terminal --demo         # cycle through all apps
arduino-esp32-tft-terminal --only cube    # run a single app
```

## Installing

### Hardware

- An [Adafruit ESP32-S3 Reverse TFT Feather](https://www.adafruit.com/product/5345).
- Optionally, the 3D-printed case from `case-esp32s3-rtft/` (`.stl` files ready to print; `.scad` sources to customise).

### Firmware (board)

- Build and flash `server-esp32s3-rtft/` onto the board.
- It has been built and uploaded with VS Code — see [`server-esp32s3-rtft/README-VSCODE.md`](server-esp32s3-rtft/README-VSCODE.md).

### Client (computer)

- Requires Python 3.11+ on Linux.
- Install the dependencies and run as shown in [Quick start](#quick-start).
- The client talks to the board over its USB serial port.

## Writing a new app

1. Study [`client-py/app/quix.py`](client-py/app/quix.py) as a template.
2. Create a new module and class.
3. Register the class in [`client-py/src/arduino_esp32_tft_terminal/cli.py`](client-py/src/arduino_esp32_tft_terminal/cli.py).

## Documentation

- [Communication protocol](README-protocol.md) — the USB command/answer protocol between computer and board.
- [Animation techniques](README-animations.md) — flicker avoidance, in the absence of hardware double-buffering.
- [Building the firmware](server-esp32s3-rtft/README-VSCODE.md) — VS Code build and upload.
- [Claude session-state detection](https://github.com/pbauermeister/claude-busy-monitor/blob/main/README-STATE-DETECTION.md) — design notes for the `claude-monitor` app (in the `claude-busy-monitor` project).

## Videos

|                                                                                                                                              |                                                                                                                                              |                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [![Video on YouTube](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/yt-Nq5qLFQl3gA.jpg)](https://youtu.be/Nq5qLFQl3gA) | [![Video on YouTube](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/yt-HaPi0cx6-W8.jpg)](https://youtu.be/HaPi0cx6-W8) | [![Video on YouTube](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/yt-vNK-JPLklLs.jpg)](https://youtu.be/vNK-JPLklLs) |

## Photos

|                                                                                                                                          |                                                                                                                                          |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| ![CPU + net monitor](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_145648.jpg "CPU + net monitor") | ![CPU + net monitor](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_144050.jpg "CPU + net monitor") |
| ![Playing 3D cube](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_142735-thumb.png "Playing 3D cube") | ![Playing Asteriods](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_132939-thumb.png "Playing Asteriods") |
| ![TFT side](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_144544.jpg "TFT side")       | ![ESP32 side](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_144614.jpg "ESP32 side")   |
| ![Case on cap](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_124410.jpg "Case on cap") | ![Case closed](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/20240525_124520.jpg "Case closed") |
| ![Modelling in OpenSCAD](https://raw.githubusercontent.com/pbauermeister/arduino-esp32-tft-terminal/main/media/esp32s3-rtft-case.scad.png "Modelling in OpenSCAD") |                                                                                                                                         |

## Links

- **Source code:** [github.com/pbauermeister/arduino-esp32-tft-terminal](https://github.com/pbauermeister/arduino-esp32-tft-terminal)
- **License:** [GPLv3](LICENSE)
