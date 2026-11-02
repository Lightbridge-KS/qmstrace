"""Components — one per source module, its ID the module's path.

A module states what it implements in its docstring: `Implements: DSN-SVC-01`. Only the
docstring is read; the same words elsewhere — in a comment, in another string — are not a marker.
They are returned as strays, so that a gap they leave open can say why. The digest covers the
module's syntax tree, so layout and comments are not a change.

Implements: DSN-QMT-04
"""

from __future__ import annotations

import ast

from qmstrace.plugin_api.v1 import (
    Diagnostic,
    Extraction,
    ExtractRequest,
    Item,
    Link,
    Stray,
    id_tokens,
    text_digest,
)
from qmstrace_lang_python import _diagnostics as findings
from qmstrace_lang_python._fields import FIELD, link_line


def extract(request: ExtractRequest) -> Extraction:
    """Read one module: the component it is, the links its docstring declares, and strays."""
    path, text = request.path, request.text
    if not text.strip():
        return Extraction()
    try:
        module = ast.parse(text, filename=path)
    except SyntaxError as broken:
        return Extraction(
            diagnostics=(findings.cannot_parse(path, broken.lineno or 1, broken.msg),)
        )

    name = path.rsplit("/", 1)[-1].removesuffix(".py")
    item = Item(path, request.item_type, path, 1, name, text_digest(ast.dump(module)))
    links: list[Link] = []
    wrong: list[Diagnostic] = []
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
            if found and found.group(1) in request.markers:
                made, bad = link_line(
                    path, found.group(1), found.group(2), path, first.lineno + offset
                )
                links += made
                wrong += bad
    carried = set(request.permitted_markers)
    strays = _strays(path, text, docstring, carried)
    return Extraction((item,), tuple(links), tuple(wrong), strays=strays)


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
        targets = id_tokens(match.group(2))
        if targets:
            found.append(
                Stray(
                    match.group(1),
                    targets,
                    path,
                    number,
                    f"the '{match.group(1)}:' line at {{location}} "
                    "is outside the module docstring, "
                    "so it is not "
                    "read — move it into the docstring.",
                    kind="docstring",
                )
            )
    return tuple(found)
