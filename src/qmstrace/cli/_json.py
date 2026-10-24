"""JSON output and safe error projection at the CLI boundary.

Implements: DSN-QMT-01
"""

from __future__ import annotations

import re
from pathlib import Path

import typer

from qmstrace.cli._invocation import CURRENT
from qmstrace.render.json._common import document

# Diagnostic paths are labels, never operational handles. Do not serialize raw OSError
# representations or exception dictionaries. Authored item/report content is left literal.
_ABSOLUTE = re.compile(r"(?<![\w/])(?:[A-Za-z]:[\\/]|/)[^\s'\"\n,;:]+")


def safe_message(text: str) -> str:
    return _ABSOLUTE.sub(lambda m: Path(m[0].replace("\\", "/")).name or "<root>", text)


def emit(
    data: dict[str, object], *, code: int = 0, notices: list[str] | tuple[str, ...] = ()
) -> None:
    request = CURRENT.get()
    payload = document(request.command, request.scope, code, data, notices)
    typer.echo(payload, nl=False, color=False)


def error(category: str, message: str, next_move: str, *, code: int) -> None:
    request = CURRENT.get()
    payload = document(
        request.command,
        request.scope,
        code,
        None,
        error={
            "category": category,
            "message": safe_message(message),
            "next_move": safe_message(next_move),
        },
    )
    typer.echo(payload, nl=False, color=False)
