# Just type 'make' to get help.
# First run on a fresh box: 'make require', then 'make help'.
#
# ============================================================================
# CONVENTIONS WHEN EDITING THIS FILE — read before adding/changing targets.
# ============================================================================
#
# 1. Target dependencies — STRICT TWO-LEVEL MODEL:
#    - Low-level  targets: no other-target deps; recipe does ONE thing.
#    - High-level targets: compose low-levels only. MARK each high-level
#      target by putting a COLON in its '##' doc string.
# 2. Help docstrings — <=60 chars (so 'make help' lines fit 80 columns).
# 3. Order targets within a section by LOGICAL CALL SEQUENCE.
# 4. Board settings (FQBN + options) mirror .vscode/arduino.json.
# ============================================================================

SHELL := /bin/bash

FQBN := esp32:esp32:adafruit_feather_esp32s3_reversetft
# Key board options (the full set lives in .vscode/arduino.json).
OPTS := USBMode=default,CDCOnBoot=cdc,PSRAM=enabled,PartitionScheme=tinyuf2,FlashSize=4M
PORT ?= /dev/ttyACM0
# version.h is generated from CHANGES.md (see below) — excluded from formatting.
SRC  := $(filter-out version.h,$(wildcard *.ino *.cpp *.h))
ARDUINO_CLI_BINDIR ?= $(HOME)/.local/bin
# Pinned for reproducibility. After the transaction DRAM trim the firmware uses
# ~62% of static RAM (was 84%), so 3.3.10 now fits with ~121 KB to spare.
ESP32_CORE := esp32:esp32@3.3.10

################################################################################
## General:: ##

.PHONY: help
help: ## print this help
	@echo "Usage: make [TARGET]..."
	@echo
	@echo "TARGETs:"
	@grep -E '^#* *[ a-zA-Z0-9_-]+:.*?##.*$$' Makefile \
	| awk 'BEGIN {FS = ":[^:]*?##"}; {printf "  %-18s%s\n", $$1, $$2}' \
	| sed -E 's/^ *#+/\n/g' \
	| sed -E 's/ +$$//g' \
	| sed -E 's/\\n/\n                      /g'
	@grep -E '^##[^#]*$$' Makefile | sed -E 's/^## ?//g'

################################################################################
## Setup:: ##

.PHONY: require
require: ## install the toolchain (arduino-cli + core + libs)
	@set -e; \
	if ! command -v arduino-cli >/dev/null; then \
		echo "installing arduino-cli into $(ARDUINO_CLI_BINDIR) ..."; \
		mkdir -p "$(ARDUINO_CLI_BINDIR)"; \
		curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh \
			| BINDIR="$(ARDUINO_CLI_BINDIR)" sh; \
		echo "note: ensure $(ARDUINO_CLI_BINDIR) is on your PATH"; \
	fi; \
	export PATH="$(ARDUINO_CLI_BINDIR):$$PATH"; \
	arduino-cli config add board_manager.additional_urls \
		https://espressif.github.io/arduino-esp32/package_esp32_index.json || true; \
	arduino-cli core update-index; \
	arduino-cli core install $(ESP32_CORE); \
	arduino-cli lib install \
		"Adafruit GFX Library" \
		"Adafruit ST7735 and ST7789 Library" \
		"Adafruit NeoPixel" \
		"Adafruit TestBed" \
		"Button"

################################################################################
## Quality:: ##

.PHONY: format
format: ## clang-format the sources in place
	clang-format -i $(SRC)

.PHONY: format-check
format-check: ## check formatting (read-only)
	clang-format --dry-run --Werror $(SRC)

################################################################################
## Build and flash:: ##

# Generated so the firmware can report its version (the `version` command).
version.h: CHANGES.md
	@V=$$(awk -F'[ :]' '/^## Version / {print $$3; exit}' CHANGES.md); \
	if [ -z "$$V" ]; then echo "version.h: no version in CHANGES.md" >&2; exit 1; fi; \
	printf '// generated from CHANGES.md by make — do not edit\n#define FW_VERSION "%s"\n' "$$V" > version.h; \
	echo "version.h: FW_VERSION=$$V"

.PHONY: firmware-build
firmware-build: version.h ## compile the sketch (arduino-cli)
	arduino-cli compile -b "$(FQBN):$(OPTS)" .

.PHONY: firmware-upload
firmware-upload: firmware-build ## build, flash + verify: set PORT (1)
	arduino-cli upload -b "$(FQBN):$(OPTS)" -p "$(PORT)" -t .

################################################################################
## Test:: ##

.PHONY: test-board
test-board: ## on-board acceptance suite (relays to client-py)
	$(MAKE) -C ../client-py test-board


################################################################################
##
## Notes:
## - Run all targets from server-esp32s3-rtft/ (next to the .ino).
## - Board FQBN + options mirror .vscode/arduino.json.
## - (1) flashes the board on PORT (default /dev/ttyACM0); override PORT=...
