"""Option-aware output selection before Typer validation; no configuration is read.

Implements: DSN-QMT-01
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Invocation:
    json: bool = False
    occurrences: int = 0
    command: str | None = None
    scope: str | None = None
    eager: bool = False


DEFAULT = Invocation()
CURRENT: ContextVar[Invocation] = ContextVar("qmstrace_invocation", default=DEFAULT)


def select(args: list[str], root: Any) -> Invocation:
    """Read option arities from the command tree, respecting values and the -- delimiter.

    This selects presentation only; Typer still validates every argument and option.
    Unknown options consume no speculative value. A malformed invocation can therefore
    request JSON without making an English error message part of the protocol.
    """
    current = root
    names: list[str] = []
    count, eager, skip = 0, False, 0
    dispatch = True
    for word in args:
        if skip:
            skip -= 1
            continue
        if word == "--":
            break
        option, equals, _ = word.partition("=")
        if word == "--help":
            eager = True
        options = {
            name: p
            for p in current.params
            for name in getattr(p, "opts", ())
            if name.startswith("-")
        }
        if option in options:
            parameter = options[option]
            if option == "--json":
                count += 1
            if option in ("--help", "--version"):
                eager = True
            if not parameter.is_flag and not equals:
                skip = max(1, parameter.nargs)
            continue
        # Attached -Cpath is a value, not a command or another flag.
        if word.startswith("-C") and word != "-C" and "-C" in options:
            continue
        commands = getattr(current, "commands", {})
        if commands and not word.startswith("-"):
            if dispatch and word in commands:
                names.append(word)
                current = commands[word]
            else:
                dispatch = False
    command = " ".join(names) or None
    scope = (
        "project"
        if len(names) > 1 and names[0] == "ledger"
        else ("local" if names and names[0] != "ledger" else None)
    )
    return Invocation(bool(count), count, command, scope, eager)
