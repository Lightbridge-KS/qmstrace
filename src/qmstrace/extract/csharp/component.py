"""Components in C# — one per `.cs` file, its ID the file's path (ADR-0004).

A file states what it implements in the leading `///` doc comment of its first type:
`/// <remarks> … Implements: DSN-SVC-01 </remarks>`, a field line with XML tags allowed around
it. Only that comment is read; the same line in another comment is a stray, so a gap it leaves
open can say why. A mention in prose — `(REQ-SVC-01)` — is neither. The digest covers the file's
tokens with ordinary comments left out, so layout and comments are not a change.

Implements: DSN-QMT-15
"""

from __future__ import annotations

import re
from typing import Final

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import Extracted, Finding, Item, Link, Stray, id_tokens, text_digest
from qmstrace.extract.csharp import _syntax
from qmstrace.extract.fields import FIELD, link_line

_TAG: Final = re.compile(r"</?[A-Za-z][^>]*>")


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one C# file: the component it is, the links its first type's doc comment declares,
    and strays."""
    if not text.strip():
        return Extracted()
    source = _syntax.parse(text)
    if source.error is not None:
        return Extracted(findings=(findings.cannot_parse(path, *source.error),))

    name = path.rsplit("/", 1)[-1].removesuffix(".cs")
    item = Item(path, item_type.name, path, 1, name, text_digest(source.digest_text))
    links: list[Link] = []
    wrong: list[Finding] = []
    read: set[int] = set()
    if source.types:
        for number, raw in source.types[0].doc:
            found = FIELD.match(_TAG.sub(" ", raw))
            if found and found.group(1) in config.links:
                made, bad = link_line(path, found.group(1), found.group(2), path, number)
                links += made
                wrong += bad
            read.add(number)
    carried = {m for m, link in config.links.items() if item_type.name in link.sources}
    strays: list[Stray] = []
    for comment in source.comments:
        if comment.line in read:
            continue
        found = FIELD.match(_TAG.sub(" ", comment.text.lstrip("/").lstrip("*")))
        if found is None or found.group(1) not in carried:
            continue
        if targets := id_tokens(found.group(2)):
            strays.append(Stray(found.group(1), targets, path, comment.line, "doccomment"))
    return Extracted((item,), tuple(links), tuple(wrong), strays=tuple(strays))


def form(marker: str, target: str) -> str:
    """How a C# file declares a link — for a gap's next move."""
    return f"`/// {marker}: {target}` in the first type's leading doc comment"
