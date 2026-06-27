# Just type 'make' to get help.
# First run on a fresh box: 'make require', then 'make help'.
#
# ============================================================================
# CONVENTIONS WHEN EDITING THIS FILE — read before adding/changing targets.
# ============================================================================
#
# 1. Target dependencies — STRICT TWO-LEVEL MODEL:
#    - Low-level  targets: no other-target deps; recipe does ONE thing.
#    - High-level targets: compose low-levels only; NO high->high. MARK each
#      high-level target by putting a COLON in its '##' doc string.
# 2. Help docstrings — <=60 chars (so 'make help' lines fit 80 columns).
# 3. Order targets within a section by LOGICAL CALL SEQUENCE.
# ============================================================================

SHELL := /bin/bash
VENV  ?= .venv
CLI   ?= $(HOME)/.local/bin/arduino-esp32-tft-terminal

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
require: ## install uv (idempotent; Linux only)
	@if command -v uv >/dev/null 2>&1; then \
		echo "uv already installed: $$(uv --version)"; \
	else \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi

.PHONY: venv-activate
venv-activate: ## start an interactive shell in updated .venv
	uv sync --extra dev
	@bash --rcfile <(echo "unset MAKELEVEL"; cat ~/.bashrc $(VENV)/bin/activate)

################################################################################
## Quality:: ##

.PHONY: lint
lint: ## ruff check + format-check (read-only)
	uv sync --extra dev
	uv run ruff check src tests
	uv run ruff format --check src tests

.PHONY: format
format: ## ruff format + lint autofix (modifies code)
	uv sync --extra dev
	uv run ruff format src tests
	uv run ruff check --fix src tests

.PHONY: test
test: ## run host unit tests (no board)
	uv sync --extra dev
	uv run pytest tests

.PHONY: test-board
test-board: ## on-board acceptance suite (needs gadget on USB; not CI)
	uv sync --extra dev
	uv run python -m arduino_esp32_tft_terminal.selftest

.PHONY: check
check: lint test ## CI/pre-PR gate: lint test

################################################################################
## Build and install:: ##

.PHONY: build
build: ## build wheel + sdist into dist/
	uv build

.PHONY: install
install: ## install in user account (CLI on ~/.local/bin/) (1)
	uv tool install --reinstall .

.PHONY: verify-installed
verify-installed: ## assert command present and --version matches CHANGES.md
	@if [ ! -x "$(CLI)" ]; then \
		echo "verify-installed: missing $(CLI) (run 'make install' first)" >&2; exit 1; \
	fi; \
	EXPECTED=$$(awk -F'[ :]' '/^## Version / {print $$3; exit}' CHANGES.md); \
	if [ -z "$$EXPECTED" ]; then \
		echo "verify-installed: cannot extract version from CHANGES.md" >&2; exit 1; \
	fi; \
	ACTUAL=$$("$(CLI)" --version 2>&1 | awk '{print $$NF}'); \
	if [ "$$ACTUAL" != "$$EXPECTED" ]; then \
		echo "verify-installed: version mismatch (expected $$EXPECTED, got '$$ACTUAL')" >&2; exit 1; \
	fi; \
	echo "verify-installed: OK ($(CLI) v$$ACTUAL)"

.PHONY: uninstall
uninstall: ## uninstall from user account (1)
	uv tool uninstall arduino-esp32-tft-terminal

.PHONY: verify-uninstalled
verify-uninstalled: ## assert command absent
	@if [ -e "$(CLI)" ]; then \
		echo "verify-uninstalled: $(CLI) still present (run 'make uninstall' first)" >&2; exit 1; \
	fi; \
	echo "verify-uninstalled: OK ($(CLI) absent)"

.PHONY: cycle
cycle: ## from scratch: uninstall clean lint test install verify (1)
	@echo "About to uninstall arduino-esp32-tft-terminal and rebuild from scratch."
	@echo "Ctrl-C within 2 seconds to abort."
	@sleep 2
	-$(MAKE) uninstall
	$(MAKE) verify-uninstalled
	$(MAKE) clean
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) install
	$(MAKE) verify-installed

################################################################################
## Publish to PyPI:: ##

.PHONY: ci-green
ci-green: ## assert GitHub CI for HEAD has finished and passed (gh) (3)
	@SHA=$$(git rev-parse HEAD); \
	echo "ci-green: GitHub CI for HEAD $$SHA"; \
	RUNS=$$(gh run list --limit 40 --json databaseId,headSha \
		--jq "[.[] | select(.headSha==\"$$SHA\")] | .[].databaseId"); \
	if [ -z "$$RUNS" ]; then \
		echo "ci-green: no CI run for HEAD — push the commit and let CI start" >&2; \
		exit 1; \
	fi; \
	for r in $$RUNS; do \
		echo "ci-green: watching run $$r..."; \
		gh run watch "$$r" --exit-status \
			|| { echo "ci-green: CI run $$r did not pass" >&2; exit 1; }; \
	done; \
	echo "ci-green: all CI runs for HEAD passed."

.PHONY: publish-quality
publish-quality: ## pre-publish gate: ci-green lint test reinstall build (1)
	@echo "About to verify CI + run lint/tests/install-cycle/build. Does NOT upload."
	@echo "Ctrl-C within 2 seconds to abort."
	@sleep 2
	$(MAKE) ci-green
	$(MAKE) lint
	$(MAKE) test
	-$(MAKE) uninstall
	$(MAKE) verify-uninstalled
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) verify-installed
	$(MAKE) build
	@echo "publish-quality: all gates green; dist/ ready. Run 'make publish' to upload."

.PHONY: publish
publish: ## upload to PyPI (raw; use publish-quality first) (2)
	export UV_KEYRING_PROVIDER=subprocess; \
	export UV_PUBLISH_USERNAME=__token__; \
	uv publish

.PHONY: publish-tag
publish-tag: ## tag git from CHANGES.md version and push it
	@V=$$(awk -F'[ :]' '/^## Version / {print $$3; exit}' CHANGES.md); \
	if [ -z "$$V" ]; then echo "publish-tag: no version in CHANGES.md" >&2; exit 1; fi; \
	git tag -a "v$$V" -m "Release v$$V"; \
	git push origin "v$$V"; \
	echo "publish-tag: tagged v$$V"

################################################################################
## Cleanup:: ##

.PHONY: clean
clean: ## remove venv, build artefacts, caches
	rm -rf $(VENV) dist build *.egg-info .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +


################################################################################
##
## Notes:
## - Run all targets from client-py/ (next to pyproject.toml).
## - (1) modifies the user account (~/.local/bin, uv tools).
## - (2) prerequisite — store the PyPI token in keyring once:
##       keyring set https://upload.pypi.org/legacy/ __token__
## - (3) needs the `gh` CLI authenticated; HEAD must be pushed so CI has run.
