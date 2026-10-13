"""The report boundary accepts pytest XML, retains its entries and refuses unsafe payloads."""

import pytest

from qmstrace.extract import junit
from qmstrace.extract.python.pytest_tests import report_identity


@pytest.mark.parametrize(
    ("payload", "problem"),
    [
        (b"not xml", "unreadable JUnit XML"),
        (b"<other/>", "testsuite or testsuites"),
        (b"<testsuite/>", "no testcase entries"),
        (b"<!DOCTYPE x><testsuite/>", "DTDForbidden"),
        (b'<!DOCTYPE x [<!ENTITY e "expanded">]><testsuite>&e;</testsuite>', "DTDForbidden"),
        (b'<!DOCTYPE x SYSTEM "https://example.invalid/entity"><testsuite/>', "DTDForbidden"),
    ],
)
@pytest.mark.verifies("DSN-QMT-09")
def test_bad_payload_is_a_diagnostic(payload: bytes, problem: str) -> None:
    report = junit.read(payload)
    assert report.problem is not None and problem in report.problem
    assert not report.entries


@pytest.mark.parametrize("namespace", ["", ' xmlns="urn:junit"'])
def test_nested_suites_outcomes_and_missing_identity(namespace: str) -> None:
    report = junit.read(
        f"""<testsuites{namespace}><testsuite tests="999"><testsuite>
      <testcase classname="tests.test_x" name="test_x[a[b]]"/>
      <testcase classname="tests.test_x" name="test_x[c]"><skipped type="pytest.xfail"/></testcase>
      <testcase classname="tests.test_x" name="test_y"><failure/><error/></testcase>
      <testcase name="test_z"/>
    </testsuite></testsuite></testsuites>""".encode()
    )
    assert report.problem is None
    assert [e.verdict for e in report.entries] == ["pass", "skip", "fail", "pass"]
    assert report.entries[2].kinds == ("error", "failure")
    assert report.entries[3].classname == ""


def test_xml_encoding_is_honored() -> None:
    payload = (
        '<?xml version="1.0" encoding="utf-16"?><testsuite>'
        '<testcase classname="tests.test_x" name="test_x[ไทย]"/></testsuite>'
    ).encode("utf-16")
    assert junit.read(payload).entries[0].name == "test_x[ไทย]"


@pytest.mark.parametrize(
    ("node_id", "key"),
    [
        ("tests/unit/test_keys.py::test_x", ("tests.unit.test_keys", "test_x")),
        (
            "tests/test_keys.py::TestOuter::TestInner::test_x",
            ("tests.test_keys.TestOuter.TestInner", "test_x"),
        ),
    ],
)
@pytest.mark.verifies("DSN-QMT-09")
def test_identity_matches_pytest(node_id: str, key: tuple[str, str]) -> None:
    assert report_identity(node_id) == key
