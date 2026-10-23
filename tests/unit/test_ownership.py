"""A controlled document must name exactly one configured subject before a baseline exists.

Implements: DSN-QMT-07
"""

from dataclasses import replace

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.judge import ownership_findings
from qmstrace.core.model import Item


def item(item_id: str, kind: str = "requirement") -> Item:
    return Item(item_id, kind, "docs/req/srs.md", 12, "A title", "sha256:x")


@pytest.mark.verifies("DSN-QMT-07", "REQ-QMT-03")
def test_missing_key_is_a_finding_even_without_tags(service: TraceConfig) -> None:
    (finding,) = ownership_findings(service, (item("REQ-03"),))
    assert finding.code == "V17"
    assert finding.file == "docs/req/srs.md" and finding.line == 12
    assert "service=SVC" in finding.what
    assert "before cutting a baseline" in finding.next_move


@pytest.mark.verifies("DSN-QMT-07")
def test_two_keys_and_duplicate_subject_declarations_are_ambiguous(
    service: TraceConfig,
) -> None:
    from qmstrace.core.config import Subject

    two = replace(service, subjects={**service.subjects, "client": Subject("client", "CLT")})
    (finding,) = ownership_findings(two, (item("REQ-SVC-CLT-03"),))
    assert "client=CLT" in finding.what and "service=SVC" in finding.what
    assert "more than one subject" in finding.what

    duplicate = replace(
        service, subjects={**service.subjects, "duplicate": Subject("duplicate", "SVC")}
    )
    (finding,) = ownership_findings(duplicate, (item("REQ-SVC-03"),))
    assert "duplicate=SVC" in finding.what and "service=SVC" in finding.what
    assert "changing only this ID cannot distinguish" in finding.next_move

    (repeated,) = ownership_findings(service, (item("REQ-SVC-SVC-03"),))
    assert "repeats a subject key" in repeated.what
    assert "exactly one configured subject key" in repeated.next_move


@pytest.mark.verifies("DSN-QMT-07")
def test_only_document_types_in_a_baseline_scope_are_checked(service: TraceConfig) -> None:
    assert ownership_findings(service, (item("REQ-SVC-03"),)) == ()
    assert ownership_findings(service, (item("REQ-03", "component"),)) == ()
    assert ownership_findings(replace(service, baselines={}), (item("REQ-03"),)) == ()
    assert ownership_findings(service, (item("REQ-03"), item("REQ-SVC-03")))[0].item == "REQ-03"


def test_subject_key_must_be_a_complete_internal_segment(service: TraceConfig) -> None:
    wrong = ownership_findings(
        service, (item("REQ-SVCX-03"), item("SVC-REQ-03"), item("REQ-03-SVC"))
    )
    assert [f.item for f in wrong] == ["REQ-SVCX-03", "SVC-REQ-03", "REQ-03-SVC"]
