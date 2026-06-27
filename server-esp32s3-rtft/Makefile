# Firmware build / format helpers for the ESP32-S3 board.
# Run from this directory. Needs `arduino-cli` (+ the esp32 core) and
# `clang-format`. Board settings mirror .vscode/arduino.json.

SHELL := /bin/bash

FQBN := esp32:esp32:adafruit_feather_esp32s3_reversetft
# Key board options (the full set lives in .vscode/arduino.json).
OPTS := USBMode=default,CDCOnBoot=cdc,PSRAM=enabled,PartitionScheme=tinyuf2,FlashSize=4M
PORT ?= /dev/ttyACM0
SRC  := $(wildcard *.ino *.cpp *.h)

.PHONY: help
help: ## print this help
	@echo "usage: make COMMAND   (PORT=$(PORT) for upload)"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

.PHONY: format
format: ## clang-format the sources in place
	clang-format -i $(SRC)

.PHONY: format-check
format-check: ## check formatting (read-only)
	clang-format --dry-run --Werror $(SRC)

.PHONY: firmware-build
firmware-build: ## compile the sketch (arduino-cli)
	arduino-cli compile -b "$(FQBN):$(OPTS)" .

.PHONY: firmware-upload
firmware-upload: firmware-build ## build + flash the board + verify (set PORT=...)
	arduino-cli upload -b "$(FQBN):$(OPTS)" -p "$(PORT)" -t .

ARDUINO_CLI_BINDIR ?= $(HOME)/.local/bin

.PHONY: require
require: ## install the toolchain (arduino-cli + esp32 core)
	@command -v arduino-cli >/dev/null || { \
		echo "installing arduino-cli into $(ARDUINO_CLI_BINDIR) ..."; \
		mkdir -p "$(ARDUINO_CLI_BINDIR)"; \
		curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh \
			| BINDIR="$(ARDUINO_CLI_BINDIR)" sh; \
		echo "note: ensure $(ARDUINO_CLI_BINDIR) is on your PATH"; \
	}
	arduino-cli config add board_manager.additional_urls \
		https://espressif.github.io/arduino-esp32/package_esp32_index.json || true
	arduino-cli core update-index
	arduino-cli core install esp32:esp32
