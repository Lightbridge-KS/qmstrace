"""How a marker is written — each extractor's `form()`, and the strays it reports.

The load-bearing claims, each pinned by a test:

1. Every form a gap suggests round-trips: written into text, the same extractor reads the link.
   A next move that names a syntax the tool does not read would be a hidden rule gone wrong.
2. A marker written outside the module docstring is a stray: it links nothing, and it is
   reported with its targets, so a gap can say why. A mention in prose is not a stray.
"""

import re

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.extract.base import FORMS, REGISTRY

CODE = re.compile(r"`([^`]+)`")

CASES = [
    ("design_element", "docs/design/d.md", "Satisfies", "REQ-SVC-01", "## DSN-SVC-01 — X\n{}\n"),
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
