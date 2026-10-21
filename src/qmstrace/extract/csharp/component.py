"""Components in C# — one per file, its ID the file's path (ADR-0004).

A file with a type states what it implements in the leading `///` doc comment of its first type:
`/// <remarks> … Implements: DSN-SVC-01 </remarks>`, a field line with XML tags allowed around
it. Only that comment is read; the same line in another comment is a stray, so a gap it leaves
open can say why. A mention in prose — `(REQ-SVC-01)` — is neither. The digest covers the file's
tokens with ordinary comments left out, so layout and comments are not a change.

A file with **no type to document** is marked in its own leading comment instead (ADR-0007): a
`.razor` page in the Razor comment at its head, read by `_razor` without the C# parser, and a
`.cs` file of top-level statements in the comment block that opens it. A file that has a type is
never read this way, so a marker above its first type stays a stray.

Implements: DSN-QMT-15
"""

from __future__ import annotations

import re
from typing import Final

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import Extracted, Finding, Item, Link, Stray, id_tokens, text_digest
from qmstrace.extract.csharp import _razor, _syntax
from qmstrace.extract.fields import FIELD, link_line

_TAG: Final = re.compile(r"</?[A-Za-z][^>]*>")
RAZOR: Final = ".razor"


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one C# or Razor file: the component it is, the links its leading comment declares,
    and strays."""
    if not text.strip():
        return Extracted()
    if path.endswith(RAZOR):
        return _read_razor(path, text, item_type, config)
    source = _syntax.parse(text)
    if source.error is not None:
        return Extracted(findings=(findings.cannot_parse(path, *source.error),))

    item = _item(path, item_type, source.digest_text)
    links: list[Link] = []
    wrong: list[Finding] = []
    read: set[int] = set()
    # A file with no type has no doc comment to read, so its own leading comment carries the
    # marker; a file that has one is read there and nowhere else.
    lines = source.types[0].doc if source.types else _leading(text, source)
    for number, raw in lines:
        found = FIELD.match(_TAG.sub(" ", raw.lstrip("/")))
        if found and found.group(1) in config.links:
            made, bad = link_line(path, found.group(1), found.group(2), path, number)
            links += made
            wrong += bad
        read.add(number)
    strays = [
        Stray(marker, targets, path, number, "doccomment")
        for number, raw in ((c.line, c.text) for c in source.comments if c.line not in read)
        for marker, targets in _stray(raw.lstrip("/").lstrip("*"), item_type, config)
    ]
    return Extracted((item,), tuple(links), tuple(wrong), strays=tuple(strays))


def _read_razor(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one Razor file: its head's comment carries the marker, one below it is a stray."""
    razor = _razor.parse(text)
    item = _item(path, item_type, razor.digest_text)
    links: list[Link] = []
    wrong: list[Finding] = []
    strays: list[Stray] = []
    for number, raw in razor.lines:
        if number > razor.head:
            strays += [
                Stray(marker, targets, path, number, "razor")
                for marker, targets in _stray(raw, item_type, config)
            ]
            continue
        found = FIELD.match(_TAG.sub(" ", raw))
        if found and found.group(1) in config.links:
            made, bad = link_line(path, found.group(1), found.group(2), path, number)
            links += made
            wrong += bad
    # `///` is a C# comment, which Razor renders as page text: a marker there is read by nobody.
    strays += [
        Stray(marker, targets, path, number, "razor")
        for number, raw in razor.slashed
        for marker, targets in _stray(raw, item_type, config)
    ]
    return Extracted((item,), tuple(links), tuple(wrong), strays=tuple(sorted(strays, key=_at)))


def _at(stray: Stray) -> int:
    return stray.line


def _item(path: str, item_type: ItemType, digest_text: str) -> Item:
    """The one component a file is — named by the file, without its extension."""
    name = path.rsplit("/", 1)[-1]
    return Item(
        path, item_type.name, path, 1, name.rsplit(".", 1)[0] or name, text_digest(digest_text)
    )


def _leading(text: str, source: _syntax.Source) -> tuple[tuple[int, str], ...]:
    """The comment block a file of top-level statements opens with — every comment line from the
    first, up to the first line that is neither blank nor a comment."""
    held = {comment.line: comment.text for comment in source.comments}
    found: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if number not in held:
            break
        found.append((number, held[number]))
    return tuple(found)


def _stray(raw: str, item_type: ItemType, config: TraceConfig) -> list[tuple[str, tuple[str, ...]]]:
    """The marker and whole IDs a line written where it is not read would have declared."""
    carried = {m for m, link in config.links.items() if item_type.name in link.sources}
    found = FIELD.match(_TAG.sub(" ", raw))
    if found is None or found.group(1) not in carried:
        return []
    targets = id_tokens(found.group(2))
    return [(found.group(1), targets)] if targets else []


def form(marker: str, target: str) -> str:
    """How a C# or Razor file declares a link — for a gap's next move."""
    return (
        f"`/// {marker}: {target}` in the first type's leading doc comment, or "
        f"`@* {marker}: {target} *@` at the head of a Razor page, or "
        f"`// {marker}: {target}` at the top of a file that declares no type"
    )
