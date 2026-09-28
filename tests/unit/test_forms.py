"""How a marker is written — each extractor's `form()`, and the strays it reports.

The load-bearing claims, each pinned by a test:

1. Every form a gap suggests round-trips: written into text, the same extractor reads the link.
   A next move that names a syntax the tool does not read would be a hidden rule gone wrong.
2. A marker written outside the module docstring is a stray: it links nothing, and it is
   reported with its targets, so a gap can say why. A mention in prose is not a stray.
3. In Markdown, a marker the item type carries is a stray when it is written outside every
   item's section, or as a table row — which then names the item whose section holds it.
   Lines in another type's section, in a fence, or naming no ID are not strays.
"""

import re

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.extract.base import FORMS, REGISTRY

CODE = re.compile(r"`([^`]+)`")

CASES = [
    ("design_element", "docs/design/d.md", "Satisfies", "REQ-SVC-01", "## DSN-SVC-01 — X\n{}\n"),
    (
        "design_element",
        "docs/design/d.md",
        "Satisfies",
        "REQ-SVC-01",
        "## 4.1 DSN-SVC-01 — X\nBody.\n\n### Traceability\n{}\n",
    ),
    ("component", "src/service/m.py", "Implements", "DSN-SVC-01", '"""M.\n\n{}\n"""\n'),
    (
        "test_case",
        "tests/unit/test_m.py",
        "verifies",
        "REQ-SVC-01",
        "{}\ndef test_x():\n    pass\n",
    ),
]


@pytest.mark.parametrize(("type_name", "path", "marker", "target", "frame"), CASES)
def test_every_suggested_form_round_trips(
    service: TraceConfig, type_name: str, path: str, marker: str, target: str, frame: str
) -> None:
    item_type = service.item_types[type_name]
    assert item_type.extractor is not None
    suggested = FORMS[item_type.extractor](marker, target)
    written = CODE.search(suggested)
    assert written is not None, suggested
    found = REGISTRY[item_type.extractor](path, frame.format(written.group(1)), item_type, service)
    assert [(link.marker, link.dst) for link in found.links] == [(marker, target)]


def test_every_extractor_has_a_form() -> None:
    assert set(FORMS) == set(REGISTRY)


MODULE = '''\
"""Keeps records.

Implements: DSN-SVC-02
"""

# Implements: DSN-SVC-01   ← a comment: not read
IMPLEMENTS = "Implements: DSN-SVC-09"
# This module implements the store; Implements: is explained in the manual.


def keep():
    """Implements: DSN-SVC-03"""
'''


@pytest.mark.verifies("DSN-QMT-04")
def test_a_marker_outside_the_module_docstring_is_a_stray(service: TraceConfig) -> None:
    found = REGISTRY["python-module"](
        "src/service/store.py", MODULE, service.item_types["component"], service
    )
    assert [link.dst for link in found.links] == ["DSN-SVC-02"]
    assert [(s.marker, s.targets, s.line) for s in found.strays] == [
        ("Implements", ("DSN-SVC-01",), 6),
        ("Implements", ("DSN-SVC-03",), 12),
    ]


def test_a_module_without_a_docstring_reports_its_marker_as_a_stray(service: TraceConfig) -> None:
    found = REGISTRY["python-module"](
        "src/service/m.py",
        "# Implements: DSN-SVC-01\nX = 1\n",
        service.item_types["component"],
        service,
    )
    assert found.links == ()
    assert [s.line for s in found.strays] == [1]


# ── Markdown strays ────────────────────────────────────────────────────────────────────────


def design(
    service: TraceConfig, text: str
) -> list[tuple[str, tuple[str, ...], int, str, str | None]]:
    found = REGISTRY["markdown"](
        "docs/design/d.md", text, service.item_types["design_element"], service
    )
    return [(s.marker, s.targets, s.line, s.kind, s.item) for s in found.strays]


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("Satisfies: REQ-SVC-01\n\n## DSN-SVC-01 — X\nBody.\n", 1),
        ("## DSN-SVC-01 — X\nBody.\n## Links\n- **Satisfies:** REQ-SVC-01\n", 4),
    ],
)
def test_a_marker_outside_every_items_section_is_a_stray(
    service: TraceConfig, text: str, line: int
) -> None:
    assert design(service, text) == [("Satisfies", ("REQ-SVC-01",), line, "outside", None)]


@pytest.mark.parametrize(
    "row",
    [
        "| Satisfies | REQ-SVC-01, REQ-SVC-02 |",
        "| **Satisfies:** | `REQ-SVC-01` · REQ-SVC-02 |",
        "| Satisfies: REQ-SVC-01, REQ-SVC-02 |",
    ],
)
def test_a_marker_written_as_a_table_row_is_a_stray_of_its_item(
    service: TraceConfig, row: str
) -> None:
    text = f"## DSN-SVC-01 — X\n\n| Link | Target |\n|---|:---:|\n{row}\n"
    found = REGISTRY["markdown"](
        "docs/design/d.md", text, service.item_types["design_element"], service
    )
    assert found.links == ()
    assert design(service, text) == [
        ("Satisfies", ("REQ-SVC-01", "REQ-SVC-02"), 5, "table", "DSN-SVC-01")
    ]


@pytest.mark.parametrize(
    "text",
    [
        "### REQ-SVC-01 — R\nSatisfies: REQ-SVC-02\n",  # another type's section: that pass reads it
        "```\nSatisfies: REQ-SVC-01\n```\n",  # a fence
        "Implements: DSN-SVC-01\n| Implements | DSN-SVC-01 |\n",  # a marker this type never carries
        "Satisfies: see the design review.\n| Satisfies | Notes |\n",  # no ID
        "| DSN-SVC-01 | Key check |\n",  # a row of IDs, no marker
    ],
)
def test_what_is_not_a_markdown_stray(service: TraceConfig, text: str) -> None:
    assert design(service, text) == []
