"""Compatibility exports keep the exact renderer objects, including shared browser evidence."""

from importlib import import_module

import pytest

from qmstrace.render import graph, text
from qmstrace.render._evidence import evidence


@pytest.mark.parametrize(
    ("owner", "names"),
    [
        ("text._status", ("status", "LISTED", "CATEGORY", "VERIFY_BY", "TESTED")),
        ("text._walks", ("thread", "impact", "ledger_thread", "ledger_impact")),
        ("text._checks", ("check", "ledger_check", "VIOLATION_HEADING", "PROJECT_GAP_HEADING")),
        ("text._results", ("results",)),
        ("text._schema", ("rules", "schema_copies")),
        ("_evidence", ("evidence",)),
    ],
)
def test_text_exports_keep_the_implementation_objects(owner: str, names: tuple[str, ...]) -> None:
    implementation = import_module(f"qmstrace.render.{owner}")
    for name in names:
        assert getattr(text, name) is getattr(implementation, name)


def test_browser_and_text_share_the_same_evidence_function() -> None:
    assert graph.evidence is evidence is text.evidence
