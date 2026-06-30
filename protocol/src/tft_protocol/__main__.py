"""CLI for the protocol meta-spec.

- `validate`: load `protocol.yaml`, run all schema + uniqueness checks,
  print a per-category summary.
- `generate`: validate, then render the generated stubs into their target
  subprojects.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .generate import generate_all
from .load import load_protocol

DEFAULT_SPEC = Path(__file__).resolve().parents[2] / "protocol.yaml"


def _validate(spec_path: Path):
    proto = load_protocol(spec_path)
    by_category: dict[str, int] = {}
    for c in proto.commands:
        by_category[c.category.value] = by_category.get(c.category.value, 0) + 1
    print(
        f"OK: {spec_path.name} — {len(proto.commands)} commands, names + hashes unique."
    )
    for category in sorted(by_category):
        print(f"  {category:9} {by_category[category]}")
    return proto


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "validate"
    spec_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_SPEC

    if command == "validate":
        _validate(spec_path)
        return 0

    if command == "generate":
        proto = _validate(spec_path)
        for path in generate_all(proto):
            print(f"  wrote {path}")
        return 0

    print(
        f"unknown command {command!r}; supported: validate, generate", file=sys.stderr
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
