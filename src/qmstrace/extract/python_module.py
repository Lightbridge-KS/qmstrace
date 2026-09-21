"""Components — one per source module, its ID the module's path.

A module states what it implements in its docstring: `Implements: DSN-SVC-01`. Only the
docstring is read; the same words in a comment are not a marker. The digest covers the
module's syntax tree, so layout and comments are not a change.
"""

from __future__ import annotations

import ast

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import Extracted, Finding, Item, Link, text_digest
from qmstrace.extract.fields import FIELD, link_line


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one module: the component it is, and the links its docstring declares."""
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
    first = module.body[0] if module.body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        for offset, raw in enumerate(first.value.value.splitlines()):
            found = FIELD.match(raw)
            if found and found.group(1) in config.links:
                made, bad = link_line(
                    path, found.group(1), found.group(2), path, first.lineno + offset
                )
                links += made
                wrong += bad
    return Extracted((item,), tuple(links), tuple(wrong))
