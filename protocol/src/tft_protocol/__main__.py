"""CLI for the protocol meta-spec.

`validate` loads `protocol.yaml`, runs all schema + uniqueness checks, and
prints a per-category summary. Generation subcommands are added later.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .load import fw_hash, load_protocol

DEFAULT_SPEC = Path(__file__).resolve().parents[2] / "protocol.yaml"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else "validate"
    spec_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_SPEC

    if command != "validate":
        print(f"unknown command {command!r}; supported: validate", file=sys.stderr)
        return 2

    proto = load_protocol(spec_path)

    by_category: dict[str, int] = {}
    for c in proto.commands:
        by_category[c.category.value] = by_category.get(c.category.value, 0) + 1

    print(
        f"OK: {spec_path.name} — {len(proto.commands)} commands, names + hashes unique."
    )
    for category in sorted(by_category):
        print(f"  {category:9} {by_category[category]}")

    # Surface the hash port so a collision regression is visible in the log.
    print(f"  (hash sample: width={fw_hash('width')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
