"""A Razor file read by its lines — never by the C# parser (ADR-0007).

A `.razor` page declares its class implicitly, so it has no type to document. It states what it
implements in a Razor comment at its head: `@* Implements: DSN-SVC-03 *@`. The head is the file's
leading run of blank lines, Razor comments and directives — so the comment may sit before
`@page "/clients"` or after it, as Razor pages are actually written. Markup, or a code block,
ends the head; a marker in a comment below it is a stray.

The C# grammar does not read Razor: a `.razor` file parses as garbage, and whether that garbage
is reported as unparsable depends on where the markup happens to sit, so this module touches
neither `_syntax` nor tree-sitter. The digest covers the file's lines with its comments left
out, so layout and comments are not a change.

Implements: DSN-QMT-15
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

_COMMENT: Final = re.compile(r"@\*.*?\*@", re.S)
_DIRECTIVE: Final = re.compile(r"^\s*@[A-Za-z]")
_BLOCK: Final = re.compile(r"^\s*@(?:code|functions)\b")
_SLASHED: Final = re.compile(r"^\s*//")


@dataclass(frozen=True, slots=True)
class Razor:
    """One Razor file: the lines its comments hold, where its head ends, and its digest text.

    `lines` pairs a 1-based line number with that line's comment text, `@*` and `*@` stripped —
    one pair per line a comment spans, so a field line is matched the way every other reader
    matches one. `head` is the last line number belonging to the head; a comment line above it
    is read, one below it is a stray.
    """

    lines: tuple[tuple[int, str], ...]
    head: int
    digest_text: str
    slashed: tuple[tuple[int, str], ...] = ()
    """Lines written as a C# comment — `//` or `///` — which Razor renders as page text rather
    than reading. A marker there is a stray, not silently dropped."""


def parse(text: str) -> Razor:
    """Read one Razor file's text. Never raises for the user's source."""
    inside: dict[int, str] = {}
    for found in _COMMENT.finditer(text):
        first = text.count("\n", 0, found.start()) + 1
        body = found.group(0).removeprefix("@*").removesuffix("*@")
        for offset, line in enumerate(body.splitlines() or [""]):
            inside[first + offset] = line
    slashed = tuple(
        (number, line.strip().lstrip("/"))
        for number, line in enumerate(text.splitlines(), start=1)
        if number not in inside and _SLASHED.match(line)
    )
    return Razor(
        tuple(sorted(inside.items())), _head(text.splitlines(), inside), _digest(text), slashed
    )


def _head(lines: list[str], inside: dict[int, str]) -> int:
    """The last line number of the file's head — 0 where the first line already ends it."""
    for number, line in enumerate(lines, start=1):
        if not line.strip() or number in inside:
            continue
        if _DIRECTIVE.match(line) and not _BLOCK.match(line):
            continue
        return number - 1
    return len(lines)


def _digest(text: str) -> str:
    """The file's text with its Razor comments removed, so a comment is not a change."""
    return " ".join(_COMMENT.sub(" ", text).split())
