"""Render the generated stubs from a validated `Protocol`.

Each generator builds per-command source in Python (the logic that varies by
arg type and return shape) and feeds it to a thin Jinja2 skeleton template.
App conveniences are NOT generated — they live in the hand-written facades.
"""

from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .schema import PY_TYPE, TRAILING_TYPES, ArgType, Command, Protocol

_HERE = Path(__file__).resolve().parent
_TEMPLATES = _HERE / "templates"
REPO_ROOT = _HERE.parents[2]  # protocol/src/tft_protocol -> repo root

BANNER = (
    "# AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.\n"
    "# Regenerate with: make protocol-gen\n"
)

# Where each generated stub lands, relative to the repo root.
COMMAND_LINE_PATH = (
    "client-py/src/arduino_esp32_tft_terminal/lib/command_line_autogen.py"
)
README_PROTOCOL_PATH = "README-protocol.md"

# Managed-block markers in README-protocol.md (the table is spliced between them;
# the surrounding prose is hand-written and preserved).
DOC_BEGIN = (
    "<!-- BEGIN GENERATED COMMANDS (protocol.yaml) — "
    "do not edit; regenerate with: make protocol-gen -->"
)
DOC_END = "<!-- END GENERATED COMMANDS -->"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES)),
        autoescape=False,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def snake(name: str) -> str:
    """camelCase command name -> snake_case Python method name."""
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


# --- client command-line layer ----------------------------------------------


def _py_param(arg) -> str:
    param = f"{arg.name}: {PY_TYPE[arg.type]}"
    if arg.optional:
        param += f" = {arg.default!r}"
    return param


def _wire_arg(arg) -> str:
    # Expression embedded in the command f-string for one argument.
    if arg.type == ArgType.BOOL:
        return f"{{int({arg.name})}}"
    return f"{{{arg.name}}}"


def _docstring(text: str) -> str:
    # Backslashes are literal in the spec (e.g. print's \n) — keep them literal
    # in the generated docstring rather than letting Python interpret them.
    return text.replace("\\", "\\\\")


def _client_method(cmd: Command) -> str:
    name = snake(cmd.name)
    params = ", ".join(["self"] + [_py_param(a) for a in cmd.args])
    if cmd.args:
        wire = " ".join([cmd.name] + [_wire_arg(a) for a in cmd.args])
        cmd_expr = f"f'{wire}'"
    else:
        cmd_expr = repr(cmd.name)

    ints = cmd.returns_ints
    if ints is not None:
        ret_type = "tuple[" + ", ".join(["int"] * len(ints)) + "]"
        vals = ", ".join(f"int(_parts[{i}])" for i in range(len(ints)))
        body = [
            f"_ans = self._command.do_command({cmd_expr})",
            "_parts = _ans.split()",
            f"return ({vals})  # {' '.join(ints)}",
        ]
    elif cmd.returns == "int":
        ret_type = "int"
        body = [f"return int(self._command.do_command({cmd_expr}))"]
    elif cmd.returns == "string":
        ret_type = "str"
        body = [f"return self._command.do_command({cmd_expr})"]
    elif cmd.returns == "none":
        ret_type = "None"
        body = [f"self._command.do_command({cmd_expr}, ignore_response=True)"]
    else:  # "ok"
        ret_type = "None"
        body = [f"self._command.do_command({cmd_expr})"]

    lines = [f"    def {name}({params}) -> {ret_type}:"]
    lines.append(f'        """{_docstring(cmd.doc)}"""')
    lines += [f"        {ln}" for ln in body]
    return "\n".join(lines)


def render_command_line(proto: Protocol) -> str:
    methods = "\n\n".join(_client_method(c) for c in proto.commands)
    template = _env().get_template("command_line.py.jinja")
    return template.render(banner=BANNER, methods=methods)


# --- protocol doc (README command table) ------------------------------------


_ANSWER = {"ok": "OK", "none": "—", "int": "int", "string": "string"}


def _arg_syntax(cmd: Command) -> str:
    parts = []
    for a in cmd.args:
        token = f"<{a.name}>" if a.type in TRAILING_TYPES else a.name
        parts.append(f"[{token}]" if a.optional else token)
    return " ".join(parts) or "—"


def _answer_syntax(cmd: Command) -> str:
    ints = cmd.returns_ints
    return " ".join(ints) if ints is not None else _ANSWER[cmd.returns]


def render_protocol_doc(proto: Protocol) -> str:
    header = ["Command", "Arguments", "Answer", "Category", "Description"]
    rows = [
        [f"`{c.name}`", _arg_syntax(c), _answer_syntax(c), c.category.value, c.doc]
        for c in proto.commands
    ]
    # Pad each column to its widest cell — canonical (Prettier-equivalent) markdown,
    # so the table is stable with or without a downstream formatter.
    widths = [max(len(r[i]) for r in (header, *rows)) for i in range(len(header))]

    def line(cells: list[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join([line(header), separator, *(line(r) for r in rows)])


def _splice_managed_block(path: Path, begin: str, end: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    head = text[: text.index(begin) + len(begin)]
    tail = text[text.index(end) :]
    path.write_text(f"{head}\n\n{body}\n\n{tail}", encoding="utf-8")


def generate_all(proto: Protocol, repo_root: Path | None = None) -> list[Path]:
    root = repo_root or REPO_ROOT
    written: list[Path] = []

    command_line = root / COMMAND_LINE_PATH
    command_line.write_text(render_command_line(proto), encoding="utf-8")
    written.append(command_line)

    readme = root / README_PROTOCOL_PATH
    _splice_managed_block(readme, DOC_BEGIN, DOC_END, render_protocol_doc(proto))
    written.append(readme)

    return written
