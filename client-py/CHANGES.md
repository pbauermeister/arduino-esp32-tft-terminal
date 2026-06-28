# Changes

## Version 0.2.0:

- `print` now slices long text to the board's per-action capacity (negotiated at runtime via `getPrintMaxLength`, with a safe fallback for older firmware), so long strings are no longer truncated.
- The connect banner reports the firmware version and the print capacity.
- Added an on-board acceptance self-test (`make test-board`).

## Version 0.1.0:

- First packaged release: the Python client becomes pip/uv-installable with an `arduino-esp32-tft-terminal` console entry point.
- Tooling: adopted ruff (format + lint), dropped mypy.
- Documentation brought to a reference level of finish (top-level README).
- Repository hygiene: ignore caches, relocate the CPU-load utility, deprecate the obsolete FeatherWing server.
