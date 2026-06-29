"""Pydantic models for the TFT command protocol meta-spec (`protocol.yaml`).

Authoritative definition of the closed enums (arg type, category) and the
per-command structure. See devlog 0054 § 2.2. The generator and validator
import these models; a spec value outside an enum is a load-time error.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class ArgType(str, Enum):
    """Parse + C++ cast/handler type of a command argument."""

    INT16 = "int16"
    INT = "int"
    INT8 = "int8"
    UCHAR = "uchar"
    BOOL = "bool"
    LAST_STRING = "last-string"  # trailing text, required (read_last_str)
    RAW_REST = "raw-rest"  # line remainder verbatim, may be empty (print)


class Category(str, Enum):
    """Developer-facing behaviour cluster. Sole codegen effect:
    `buffered` selects the enqueue path on the server; every other value is
    an immediate, hand-written handler (indistinguishable to the generator)."""

    BUFFERED = "buffered"
    CONTROL = "control"
    QUERY = "query"
    BUTTON = "button"
    MISC = "misc"


# Arg types whose value is trailing free text — must be the final argument.
TRAILING_TYPES = {ArgType.LAST_STRING, ArgType.RAW_REST}

# Codegen type mappings, authoritative alongside the enum.
CPP_TYPE: dict[ArgType, str] = {
    ArgType.INT16: "int16_t",
    ArgType.INT: "int",
    ArgType.INT8: "int8_t",
    ArgType.UCHAR: "unsigned char",
    ArgType.BOOL: "bool",
    ArgType.LAST_STRING: "const char *",
    ArgType.RAW_REST: "const char *",
}

PY_TYPE: dict[ArgType, str] = {
    ArgType.INT16: "int",
    ArgType.INT: "int",
    ArgType.INT8: "int",
    ArgType.UCHAR: "int",
    ArgType.BOOL: "bool",
    ArgType.LAST_STRING: "str",
    ArgType.RAW_REST: "str",
}


class Arg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: ArgType
    optional: bool = False
    # A literal int/bool default, or the name of an earlier arg (cross-arg
    # default, e.g. setTextSize sy defaults to sx).
    default: bool | int | str | None = None

    @field_validator("name")
    @classmethod
    def _name_is_identifier(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError(f"arg name {v!r} is not a valid identifier")
        return v

    @model_validator(mode="after")
    def _default_requires_optional(self) -> "Arg":
        if self.default is not None and not self.optional:
            raise ValueError(f"arg {self.name!r} has a default but is not optional")
        return self


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str  # wire token, also the hash() key
    category: Category
    doc: str  # mandatory human description
    args: list[Arg] = []
    # Response shape; a list of field names denotes a space-separated int tuple.
    returns: Literal["ok", "none", "int", "string"] | list[str] = "ok"

    @field_validator("doc")
    @classmethod
    def _doc_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("doc must be non-empty")
        return v

    @field_validator("returns")
    @classmethod
    def _returns_fields_are_identifiers(cls, v: object) -> object:
        if isinstance(v, list):
            if not v:
                raise ValueError("an 'ints' return must list at least one field name")
            for f in v:
                if not isinstance(f, str) or not f.isidentifier():
                    raise ValueError(f"ints return field {f!r} is not an identifier")
        return v

    @model_validator(mode="after")
    def _trailing_last_and_defaults_resolve(self) -> "Command":
        for i, a in enumerate(self.args):
            if a.type in TRAILING_TYPES and i != len(self.args) - 1:
                raise ValueError(
                    f"{self.name}: {a.type.value} arg {a.name!r} must be the last argument"
                )
            if isinstance(a.default, str):
                earlier = {p.name for p in self.args[:i]}
                if a.default not in earlier:
                    raise ValueError(
                        f"{self.name}: default {a.default!r} of {a.name!r} "
                        "names no earlier argument"
                    )
        return self

    @property
    def returns_ints(self) -> list[str] | None:
        return self.returns if isinstance(self.returns, list) else None


class Protocol(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commands: list[Command]

    @model_validator(mode="after")
    def _names_and_hashes_unique(self) -> "Protocol":
        from .load import fw_hash

        seen_names: set[str] = set()
        seen_hashes: dict[int, str] = {}
        for c in self.commands:
            if c.name in seen_names:
                raise ValueError(f"duplicate command name {c.name!r}")
            seen_names.add(c.name)
            h = fw_hash(c.name)
            if h in seen_hashes:
                raise ValueError(
                    f"hash collision: {c.name!r} and {seen_hashes[h]!r} "
                    f"both hash to {h}"
                )
            seen_hashes[h] = c.name
        return self
