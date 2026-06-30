# Top-level signpost — this repository has no build of its own.
# The work lives in the sub-projects, each with its own Makefile:
#
#   client-py/            Python client + app logic + the test suites
#   server-esp32s3-rtft/  board firmware (build / flash via arduino-cli)
#   protocol/             command-protocol meta-spec + code generator
#
# Run 'make' here for this signpost; 'cd' into a sub-project and 'make help'.
# The one cross-cutting target lives here: 'make protocol-gen'.

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "arduino-esp32-tft-terminal — no top-level build; work in the sub-projects:"
	@echo
	@echo "  client-py/            Python client, apps, and the test suites"
	@echo "                          cd client-py && make help"
	@echo "                          (tests live here: a running app drives the board)"
	@echo
	@echo "  server-esp32s3-rtft/  board firmware (build / flash via arduino-cli)"
	@echo "                          cd server-esp32s3-rtft && make help"
	@echo
	@echo "  protocol/             command-protocol meta-spec + code generator"
	@echo "                          cd protocol && make help"
	@echo
	@echo "Cross-cutting target:"
	@echo "  make protocol-gen     regenerate client + server + docs stubs from the spec"

.PHONY: protocol-gen
protocol-gen: ## regenerate the generated stubs from protocol/protocol.yaml
	$(MAKE) -C protocol gen
