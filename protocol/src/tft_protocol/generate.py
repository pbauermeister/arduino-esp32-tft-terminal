"""Render the generated stubs from a validated `Protocol`.

Each generator builds per-command source in Python (the logic that varies by
arg type and return shape) and feeds it to a thin Jinja2 skeleton template.
App conveniences are NOT generated — they live in the hand-written facades.
"""

from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .schema import (
    CPP_TYPE,
    PY_TYPE,
    TRAILING_TYPES,
    ArgType,
    Category,
    Command,
    Protocol,
)

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

CPP_BANNER = (
    "// AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.\n"
    "// Regenerate with: make protocol-gen\n"
)
SERVER_DISPATCH_PATH = "server-esp32s3-rtft/command_dispatch.autogen.inc"
SERVER_REPLAY_PATH = "server-esp32s3-rtft/replay_dispatch.autogen.inc"
SERVER_HANDLERS_PATH = "server-esp32s3-rtft/protocol_handlers.autogen.h"


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


# --- server C++ (parse dispatch, replay dispatch, handler header) ------------


def _is_buffered(cmd: Command) -> bool:
    return cmd.category == Category.BUFFERED


def _cpp_default(arg) -> str:
    if isinstance(arg.default, bool):
        return "1" if arg.default else "0"
    return str(arg.default)


def _cpp_parse_case(cmd: Command) -> str:
    """One `interpret()` switch case: read + validate args, then dispatch."""
    lines = [f'case hash("{cmd.name}"): {{']
    numeric = []
    raw_rest = cmd.args and cmd.args[0].type == ArgType.RAW_REST
    for a in cmd.args:
        if a.type == ArgType.RAW_REST:
            continue  # consumed as the remaining `rest`, no read
        elif a.type == ArgType.LAST_STRING:
            lines.append(f"const char *{a.name} = read_last_str(&rest, error);")
        elif a.optional:
            lines.append(
                f"int {a.name} = read_int(&rest, error, true, {_cpp_default(a)});"
            )
            numeric.append(a.name)
        else:
            lines.append(f"int {a.name} = read_int(&rest, error);")
            numeric.append(a.name)

    if not cmd.args:
        lines.append("no_arg(&rest, error);")
        lines.append("if (error.message) return error.message;")
    elif not raw_rest:
        lines.append("if (error.message) return error.message;")

    if _is_buffered(cmd):
        if raw_rest:
            lines.append("transaction.action()->set(hh, rest);")
        elif cmd.args:
            lines.append(f"transaction.action()->set(hh, {', '.join(numeric)});")
        else:
            lines.append("transaction.action()->set(hh);")
        lines.append("transaction.add();")
        lines.append("return ok();")
    else:
        call = ", ".join(a.name for a in cmd.args)
        lines.append(f"return handle_{cmd.name}({call});")
    body = "\n".join(f"    {ln}" for ln in lines[1:])
    return f"{lines[0]}\n{body}\n}}"


def _cpp_replay_case(cmd: Command) -> str:
    """One `do_action()` switch case: extract typed args, call the binding."""
    exprs = []
    idx = 0
    for a in cmd.args:
        if a.type in TRAILING_TYPES:
            exprs.append("action->str")
        else:
            exprs.append(f"({CPP_TYPE[a.type]})action->args[{idx}]")
            idx += 1
    return (
        f'case hash("{cmd.name}"): {{\n'
        f"    replay_{cmd.name}({', '.join(exprs)});\n"
        f"    break;\n}}"
    )


def _cpp_proto(cmd: Command) -> str:
    params = ", ".join(f"{CPP_TYPE[a.type]} {a.name}" for a in cmd.args)
    if _is_buffered(cmd):
        return f"void replay_{cmd.name}({params});"
    return f"const char *handle_{cmd.name}({params});"


def render_command_dispatch(proto: Protocol) -> str:
    cases = "\n\n".join(_cpp_parse_case(c) for c in proto.commands)
    return f"{CPP_BANNER}\n{cases}\n"


def render_replay_dispatch(proto: Protocol) -> str:
    cases = "\n\n".join(_cpp_replay_case(c) for c in proto.commands if _is_buffered(c))
    return f"{CPP_BANNER}\n{cases}\n"


def render_server_handlers(proto: Protocol) -> str:
    replay = [_cpp_proto(c) for c in proto.commands if _is_buffered(c)]
    handle = [_cpp_proto(c) for c in proto.commands if not _is_buffered(c)]
    return (
        f"{CPP_BANNER}\n"
        "#ifndef PROTOCOL_HANDLERS_AUTOGEN_H\n"
        "#define PROTOCOL_HANDLERS_AUTOGEN_H\n\n"
        "#include <stdint.h>\n\n"
        "// Buffered replay handlers — the TFT binding for each draw command.\n"
        "// Hand-written in transaction.cpp; a missing one is a link error.\n"
        + "\n".join(replay)
        + "\n\n"
        "// Immediate command handlers — return the response string.\n"
        "// Hand-written in command.cpp.\n"
        + "\n".join(handle)
        + "\n\n#endif  // PROTOCOL_HANDLERS_AUTOGEN_H\n"
    )


def generate_all(proto: Protocol, repo_root: Path | None = None) -> list[Path]:
    root = repo_root or REPO_ROOT
    written: list[Path] = []

    command_line = root / COMMAND_LINE_PATH
    command_line.write_text(render_command_line(proto), encoding="utf-8")
    written.append(command_line)

    readme = root / README_PROTOCOL_PATH
    _splice_managed_block(readme, DOC_BEGIN, DOC_END, render_protocol_doc(proto))
    written.append(readme)

    for rel, text in (
        (SERVER_DISPATCH_PATH, render_command_dispatch(proto)),
        (SERVER_REPLAY_PATH, render_replay_dispatch(proto)),
        (SERVER_HANDLERS_PATH, render_server_handlers(proto)),
    ):
        path = root / rel
        path.write_text(text, encoding="utf-8")
        written.append(path)

    return written
