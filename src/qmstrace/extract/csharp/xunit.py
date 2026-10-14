"""Automated tests in C# — one per xUnit `[Fact]` or `[Theory]` method (ADR-0004).

Its ID is `path::Outer::Inner::Method`. Its link is the ID that starts its `DisplayName`, when
that is a string literal — regular, verbatim or raw — and the link is the one its item type
carries: `[Fact(DisplayName = "TC-SVC-01.1 a call without a key is refused")]`. A `[Theory]` is
one automated test; its rows are runs.

A test report names a run by its class — namespace-qualified, nested classes joined with `+` —
and its method, never by the `DisplayName`. So the extractor records those identities: the
declaring class when it is concrete, and every concrete subclass in the same file when it is
abstract, since xUnit runs an inherited test once per subclass.

A marker in a form this extractor does not read must never silently yield no link: a
`DisplayName` that is not a literal, a `[Trait]` named after a link (traits never reach a test
report), a test attribute other than xUnit's own, a test inside conditional compilation. Each is
reported. A test attribute written in a comment is a stray. The level is read from the folder
the file sits in, regardless of case. The digest covers the method's tokens, attributes
included, comments left out.

Implements: DSN-QMT-15
"""

from __future__ import annotations

import re
from typing import Final

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import (
    ID_TOKEN,
    Extracted,
    Finding,
    Identity,
    Item,
    Link,
    Stray,
    text_digest,
)
from qmstrace.extract.csharp import _syntax

_XUNIT: Final = {"Fact", "Theory"}
_DISPLAY: Final = "DisplayName"
# A first word that is shaped like an attempt at an ID, though not a whole one.
_ID_LIKE: Final = re.compile(r"[A-Z][A-Z0-9]*-\S*\d")
# A test attribute written in a comment: `// [Fact(DisplayName = "TC-SVC-01.1 …")]`.
_COMMENTED: Final = re.compile(r'\[\s*(?:\w+\.)*\w+\s*\(\s*DisplayName\s*=\s*@?"(\S+)')
_FIX: Final = (
    "Fix: start the test's DisplayName with the ID, as a string literal: [Fact(DisplayName = \"ID "
    '…")] on an xUnit [Fact] or [Theory] method.'
)


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one C# test file for automated tests and the link each one's DisplayName declares."""
    source = _syntax.parse(text)
    if source.error is not None:
        return Extracted(findings=(findings.cannot_parse(path, *source.error),))
    carried = [m for m, link in config.links.items() if item_type.name in link.sources]
    marker = carried[0] if len(carried) == 1 else None  # the configuration refuses otherwise
    folders = [part.lower() for part in path.split("/")[:-1]]
    level = next((lv for part in folders for lv in item_type.levels if part == lv.lower()), None)

    items: list[Item] = []
    links: list[Link] = []
    wrong: list[Finding] = []
    for declared in source.types:
        for method in declared.methods:
            tests = [a for a in method.attributes if _simple(a.name) in _XUNIT]
            custom = [
                a
                for a in method.attributes
                if a not in tests and _simple(a.name).endswith(("Fact", "Theory"))
            ]
            for attribute in (a for a in method.attributes if _simple(a.name) == "Trait"):
                if marker is not None and _trait_names(attribute, marker):
                    wrong.append(
                        _unread(
                            path,
                            attribute.line,
                            marker,
                            "written as a [Trait], which never reaches a test report",
                        )
                    )
            if method.conditional and (tests or custom):
                if marker is not None:
                    wrong.append(
                        _unread(
                            path,
                            method.line,
                            marker,
                            "on a test inside conditional compilation (#if)",
                        )
                    )
                continue
            if not tests:
                if custom and marker is not None:
                    wrong.append(
                        _unread(
                            path,
                            custom[0].line,
                            marker,
                            f"on [{custom[0].name}], a test attribute this tool does not read",
                        )
                    )
                continue
            test_id = "::".join([path, *declared.outer, declared.name, method.name])
            item = Item(
                test_id,
                item_type.name,
                path,
                method.line,
                method.name,
                text_digest(method.digest_text),
                level=level,
                runs_as=_identities(declared, method.name, source.types),
            )
            items.append(item)
            if level is None and item_type.levels:
                wrong.append(findings.no_level(item, item_type.levels))
            if marker is None:
                continue
            display = next((a for a in tests[0].arguments if a.name == _DISPLAY), None)
            if display is None:
                continue
            if display.value is None:
                wrong.append(
                    _unread(
                        path,
                        display.line,
                        marker,
                        "given a DisplayName that is not a string literal",
                    )
                )
                continue
            first = display.value.split()[0] if display.value.split() else ""
            if ID_TOKEN.fullmatch(first):
                links.append(Link(test_id, first, marker, path, display.line))
            elif _ID_LIKE.match(first):
                wrong.append(findings.not_an_id(test_id, marker, first, path, display.line))
    strays = tuple(
        Stray(marker, (found.group(1),), path, comment.line, "comment")
        for comment in source.comments
        if marker is not None
        for found in [_COMMENTED.search(comment.text)]
        if found is not None and ID_TOKEN.fullmatch(found.group(1))
    )
    return Extracted(tuple(items), tuple(links), tuple(wrong), strays=strays)


def form(marker: str, target: str) -> str:
    """How an xUnit test declares its link — for a gap's next move."""
    return f'`[Fact(DisplayName = "{target} …")]` on the test method'


def _identities(
    declared: _syntax.TypeDecl, method: str, types: tuple[_syntax.TypeDecl, ...]
) -> tuple[Identity, ...]:
    """The report identities a test's runs carry: its concrete class and, in this file, every
    concrete class that derives from it — directly or through another."""
    classes = [declared] if not declared.abstract else []
    family = {declared.name}
    grew = True
    while grew:
        grew = False
        for other in types:
            if other.name not in family and family & set(other.bases):
                family.add(other.name)
                grew = True
                if not other.abstract:
                    classes.append(other)
    return tuple((_class_name(c), method) for c in classes)


def _class_name(declared: _syntax.TypeDecl) -> str:
    nested = "+".join([*declared.outer, declared.name])
    return f"{declared.namespace}.{nested}" if declared.namespace else nested


def _simple(name: str) -> str:
    """`Xunit.FactAttribute`, `global::Xunit.Fact` → `Fact`."""
    return name.rsplit(".", 1)[-1].rsplit("::", 1)[-1].removesuffix("Attribute")


def _trait_names(attribute: _syntax.Attribute, marker: str) -> bool:
    first = attribute.arguments[0] if attribute.arguments else None
    return first is not None and first.value == marker


def _unread(path: str, line: int, marker: str, form: str) -> Finding:
    return findings.unread_marker(path, line, marker, form, fix=_FIX)
