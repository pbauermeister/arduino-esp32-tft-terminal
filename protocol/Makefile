# Protocol meta-spec: validation, code generation, drift gate, goldens.
# The generator writes stubs into the sibling sub-projects; this Makefile also
# formats them with the same tools those projects use (ruff, clang-format).
SHELL := /bin/bash
REPO  := ..

# Generated stubs, relative to the repo root (for the drift-gate diff).
G_CLIENT   := client-py/src/arduino_esp32_tft_terminal/lib/command_line_autogen.py
G_SERVER_H := server-esp32s3-rtft/protocol_handlers.autogen.h
GENERATED  := \
	$(G_CLIENT) \
	README-protocol.md \
	server-esp32s3-rtft/command_dispatch.autogen.inc \
	server-esp32s3-rtft/replay_dispatch.autogen.inc \
	$(G_SERVER_H)

.DEFAULT_GOAL := help

.PHONY: help
help: ## print this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

.PHONY: require
require: ## create venv + install deps (idempotent)
	uv venv -q
	uv pip install -q -e '.[dev]'

.PHONY: validate
validate: ## validate protocol.yaml against the schema
	uv run python -m tft_protocol validate

.PHONY: gen
gen: ## regenerate all stubs, then format them in place
	uv run python -m tft_protocol generate
	uv run ruff format -q $(REPO)/$(G_CLIENT)
	clang-format -i $(REPO)/$(G_SERVER_H)

.PHONY: check
check: gen ## drift gate: regenerate+format must reproduce the committed stubs
	@git -C $(REPO) diff --exit-code -- $(GENERATED) \
		&& echo "protocol stubs are up to date" \
		|| { echo "ERROR: stubs are stale — run 'make protocol-gen' and commit"; exit 1; }

.PHONY: lint
lint: ## ruff check + format-check on the generator sources
	uv run ruff check .
	uv run ruff format --check .

.PHONY: test
test: ## generator goldens (feature-fixture spec -> expected emission)
	uv run pytest -q

.PHONY: clean
clean: ## remove venv + caches
	rm -rf .venv .pytest_cache .ruff_cache src/tft_protocol/__pycache__ \
		src/tft_protocol/*/__pycache__ tests/__pycache__
