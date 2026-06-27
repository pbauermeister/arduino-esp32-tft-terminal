SHELL := /bin/bash

# Interim ruff-based quality targets (mypy dropped, #9).
# The full uv-based two-level Makefile lands with task G (#TODO item 5).

.PHONY: *

help:	## print this help
	@echo "usage: make COMMAND"
	@echo
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

require: ## install dependencies (Python)
	pip install -r client-py/requirements.txt

lint: ## lint + format-check (ruff, read-only)
	cd client-py && uv tool run ruff check . && uv tool run ruff format --check .

format: ## format + lint autofix (ruff, modifies code)
	cd client-py && uv tool run ruff format . && uv tool run ruff check --fix .

clean: ## remove caches
	rm -rf .ruff_cache .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
