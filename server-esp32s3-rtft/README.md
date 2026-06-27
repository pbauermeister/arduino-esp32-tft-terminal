# server-esp32s3-rtft — board firmware

The board-side firmware of the
[Arduino ESP32 TFT Terminal](../README.md). It is a graphical server (C++):
it exposes the TFT drawing primitives and button readout over USB, and holds
no application logic — all behaviour lives in the [Python client](../client-py/).

## Hardware

- [Adafruit ESP32-S3 Reverse TFT Feather](https://www.adafruit.com/product/5345) (ESP32-S3 + 240×135 colour TFT).

## Building and uploading

Build and flash with `make` (`arduino-cli` under the hood), from this directory:

```bash
make require          # one-time: arduino-cli + esp32 core + libraries
make firmware-upload  # build, flash the board, verify
```

Run `make help` for all targets (`firmware-build`, `format`, `format-check`, ...).

## Protocol

- The computer sends textual commands; the board answers. Most commands map directly to TFT library calls.
- Specified in [`../README-protocol.md`](../README-protocol.md).

## Layout

- `server-esp32s3-rtft.ino` — main loop: read a command line, interpret it, answer.
- `command.cpp` / `command.h` — parse and dispatch commands (compile-time string hashing).
- `transaction.cpp` / `transaction.h` — buffered action execution.
- `esp32s3-display.cpp` / `esp32s3-display.h` — TFT primitives over Adafruit ST7789 + buttons.
- `neopixel.cpp` / `neopixel.h` — on-board NeoPixel LED.
- `config.h` — buffer sizing and board configuration.
