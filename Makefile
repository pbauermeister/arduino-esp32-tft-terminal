
MYPY_OPTS :=
MYPY_OPTS += --explicit-package-bases
MYPY_OPTS += --follow-imports=silent
MYPY_OPTS += --ignore-missing-imports
MYPY_OPTS += --namespace-packages
MYPY_OPTS += --no-strict-optional
MYPY_OPTS += --pretty
MYPY_OPTS += --strict
MYPY_OPTS += --strict-equality
MYPY_OPTS += --warn-redundant-casts
MYPY_OPTS += --warn-return-any
MYPY_OPTS += --warn-unreachable

.PHONY: *

help:	## print this help
	@echo "usage: make COMMAND"
	@echo
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

require: ## install dependencies (Python)
	pip install -r client-py/requirements.txt

lint: ## lint (Python)
	mypy $(MYPY_OPTS) $$(find -P -name "*.py")

clean: ## remove tmp files
	rm -rf .mypy_cache
