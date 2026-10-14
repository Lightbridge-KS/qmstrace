"""Test cases — one per pytest test function, its ID the test's node ID without parameters.

A test states what it verifies with the framework's own marker:
`@pytest.mark.verifies("REQ-SVC-01", "DSN-SVC-01")` on the function, or on its test class, whose
tests inherit it. A parametrised function is one test case that runs several times.

A marker in a form this extractor does not read — through `pytestmark`, inside
`pytest.param(marks=…)`, with an argument that is not a literal string, with no IDs, as a bare
decorator, under another name, on something pytest does not collect — must never silently
yield no link. Every `mark.<link marker>` in the module is either read or reported.

A test's level is read from the folder it sits in. The digest covers the function's own syntax
tree, decorators included, so a comment or a neighbour's edit is not a change.

Implements: DSN-QMT-04, DSN-QMT-09
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import ID_TOKEN, Extracted, Finding, Identity, Item, Link, text_digest

_Owner = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


@dataclass
class _Reading:
    """One module being read."""

    path: str
    item_type: ItemType
    level: str | None
    items: list[Item] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    wrong: list[Finding] = field(default_factory=list)
    read: set[int] = field(default_factory=set)  # id() of every marker node that was read


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one test module for test cases and the links their markers declare."""
    try:
        module = ast.parse(text, filename=path)
    except SyntaxError as broken:
        return Extracted(findings=(findings.cannot_parse(path, broken.lineno or 1, broken.msg),))

    folders = path.split("/")[:-1]
    level = next((part for part in folders if part in item_type.levels), None)
    reading = _Reading(path, item_type, level)
    _visit(reading, module.body, path, ())
    reading.wrong += _unread(reading, module, frozenset(config.links))
    return Extracted(tuple(reading.items), tuple(reading.links), tuple(reading.wrong))


def form(marker: str, target: str) -> str:
    """How a test declares a link — for a gap's next move."""
    return f'`@pytest.mark.{marker}("{target}")` on the test'


def report_identity(test_id: str) -> Identity:
    """The classname/name emitted by default pytest JUnit for one scanned node ID."""
    path, *owners, name = test_id.split("::")
    module = path.removesuffix(".py").replace("/", ".")
    return ".".join([module, *owners]), name


def _visit(
    reading: _Reading, body: list[ast.stmt], scope: str, inherited: tuple[Link, ...]
) -> None:
    for node in body:
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            name = f"{scope}::{node.name}"
            _visit(reading, node.body, name, inherited + _declared(reading, node, name))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_test_name(node):
            test_id = f"{scope}::{node.name}"
            item = Item(
                test_id,
                reading.item_type.name,
                reading.path,
                node.lineno,
                node.name,
                text_digest(ast.dump(node)),
                level=reading.level,
                runs_as=(report_identity(test_id),),
            )
            reading.items.append(item)
            if reading.level is None and reading.item_type.levels:
                reading.wrong.append(findings.no_level(item, reading.item_type.levels))
            for link in (*inherited, *_declared(reading, node, test_id)):
                reading.links.append(
                    Link(test_id, link.dst, link.marker, reading.path, node.lineno)
                )


def _declared(reading: _Reading, owner: _Owner, src: str) -> tuple[Link, ...]:
    """The links an owner's decorators declare, in the one form that is read."""
    found: list[Link] = []
    for decorator in owner.decorator_list:
        if not isinstance(decorator, ast.Call) or decorator.keywords or not decorator.args:
            continue
        marker = _marker(decorator.func)
        values = [a.value for a in decorator.args if isinstance(a, ast.Constant)]
        if marker is None or len(values) != len(decorator.args):
            continue
        if not all(isinstance(value, str) for value in values):
            continue
        reading.read.add(id(decorator.func))
        for value in map(str, values):
            if ID_TOKEN.fullmatch(value):
                found.append(Link(src, value, marker, reading.path, decorator.lineno))
            else:
                reading.wrong.append(
                    findings.not_an_id(src, marker, value, reading.path, decorator.lineno)
                )
    return tuple(found)


def _marker(node: ast.expr) -> str | None:
    """The `<m>` of `pytest.mark.<m>` or `mark.<m>`, else None."""
    if not isinstance(node, ast.Attribute):
        return None
    owner = node.value
    if isinstance(owner, ast.Attribute) and owner.attr == "mark":
        return node.attr
    if isinstance(owner, ast.Name) and owner.id == "mark":
        return node.attr
    return None


def _unread(reading: _Reading, module: ast.Module, markers: frozenset[str]) -> list[Finding]:
    """A finding for every `mark.<link marker>` that `_declared` did not read."""
    parents = {
        id(child): parent for parent in ast.walk(module) for child in ast.iter_child_nodes(parent)
    }
    unread: list[Finding] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Attribute) or id(node) in reading.read:
            continue
        marker = _marker(node)
        if marker in markers:
            form = _form(node, parents)
            unread.append(findings.unread_marker(reading.path, node.lineno, node.attr, form))
    return unread


def _form(node: ast.Attribute, parents: dict[int, ast.AST]) -> str:
    """How an unread marker was written, in the words of the finding."""
    parent = parents.get(id(node))
    written: ast.expr = parent if isinstance(parent, ast.Call) and parent.func is node else node
    enclosing = _ancestors(written, parents)
    statement = next((a for a in enclosing if isinstance(a, ast.stmt)), None)
    if isinstance(statement, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "pytestmark" for target in statement.targets
    ):
        return "set through pytestmark"
    if any(isinstance(a, ast.keyword) for a in enclosing):
        return "given inside pytest.param(marks=…)"
    owner = parents.get(id(written))
    if isinstance(owner, _Owner) and any(d is written for d in owner.decorator_list):
        if not _is_collected(owner, parents):
            return "on something pytest does not collect as a test"
        if written is node:
            return "used as a bare decorator, with no IDs"
        if isinstance(written, ast.Call) and not written.args and not written.keywords:
            return "given no IDs"
        return "given an argument that is not a literal string"
    return "used under another name, or outside a decorator"


def _ancestors(node: ast.AST, parents: dict[int, ast.AST]) -> list[ast.AST]:
    found: list[ast.AST] = []
    current = parents.get(id(node))
    while current is not None:
        found.append(current)
        current = parents.get(id(current))
    return found


def _is_test_name(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return node.name.startswith("test_")


def _is_collected(owner: _Owner, parents: dict[int, ast.AST]) -> bool:
    """Whether pytest collects this function or class as a test, by its default rules."""
    if isinstance(owner, ast.ClassDef):
        named = owner.name.startswith("Test")
    else:
        named = _is_test_name(owner)
    parent = parents.get(id(owner))
    while isinstance(parent, ast.ClassDef):
        named = named and parent.name.startswith("Test")
        parent = parents.get(id(parent))
    return named and isinstance(parent, ast.Module)
