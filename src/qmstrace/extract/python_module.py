"""Components — one per source module, its ID the module's path.

A module states what it implements in its docstring: `Implements: DSN-SVC-01`. Only the
docstring is read; the same words elsewhere — in a comment, in another string — are not a marker.
They are returned as strays, so that a gap they leave open can say why. The digest covers the
module's syntax tree, so layout and comments are not a change.
"""

from __future__ import annotations

import ast

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import ID_TOKEN, Extracted, Finding, Item, Link, Stray, text_digest
from qmstrace.extract.fields import FIELD, link_line


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one module: the component it is, the links its docstring declares, and strays."""
    if not text.strip():
        return Extracted()
    try:
        module = ast.parse(text, filename=path)
    except SyntaxError as broken:
        return Extracted(findings=(findings.cannot_parse(path, broken.lineno or 1, broken.msg),))

    name = path.rsplit("/", 1)[-1].removesuffix(".py")
    item = Item(path, item_type.name, path, 1, name, text_digest(ast.dump(module)))
    links: list[Link] = []
    wrong: list[Finding] = []
    docstring: range = range(0)
    first = module.body[0] if module.body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        docstring = range(first.lineno, (first.end_lineno or first.lineno) + 1)
        for offset, raw in enumerate(first.value.value.splitlines()):
            found = FIELD.match(raw)
            if found and found.group(1) in config.links:
                made, bad = link_line(
                    path, found.group(1), found.group(2), path, first.lineno + offset
                )
                links += made
                wrong += bad
    carried = {m for m, link in config.links.items() if item_type.name in link.sources}
    strays = _strays(path, text, docstring, carried)
    return Extracted((item,), tuple(links), tuple(wrong), strays=strays)


def form(marker: str, target: str) -> str:
    """How a module declares a link — for a gap's next move."""
    return f"`{marker}: {target}` in its docstring"


def _strays(path: str, text: str, docstring: range, markers: set[str]) -> tuple[Stray, ...]:
    """Marker lines outside the module docstring that name at least one ID — never links."""
    found: list[Stray] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if number in docstring:
            continue
        line = raw.strip().lstrip("#\"' ")  # a comment, or another docstring's first line
        match = FIELD.match(line)
        if match is None or match.group(1) not in markers:
            continue
        targets = tuple(ID_TOKEN.findall(match.group(2)))
        if targets:
            found.append(Stray(match.group(1), targets, path, number, "docstring"))
    return tuple(found)
