"""TRX reports (ADR-0004) — read by class and method, with nothing of the build machine kept.

The load-bearing claims, each pinned by a test:

1. The root element decides the format: a TeamTest `TestRun` is TRX, a `testsuite` or
   `testsuites` is JUnit, anything else is refused — never guessed at.
2. A run is one result: its identity is the class and method its definition names, its name the
   result's `testName`, so a Theory's rows are separate runs of one automated test; nested classes
   are joined with `+`.
3. `Passed` is a pass and `NotExecuted` a skip; any other outcome, or none, is a failure that
   keeps the raw outcome. Only the first line of the error message is kept.
4. Paths, machine and user names, output, stack traces and attachments are never read: a
   sentinel planted in each never reaches the report. No summary count is trusted.
5. Every run in a real probe report matches the identity its xUnit extractor recorded — the
   join this reader exists for.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.results import Report
from qmstrace.extract import reports
from qmstrace.extract.csharp import xunit

TRX = Path(__file__).parents[1] / "fixtures" / "trx"
CASES = Path(__file__).parents[1] / "fixtures" / "cases"
NS = "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"


def read(name: str) -> Report:
    report = reports.read((TRX / name).read_bytes())
    assert report.problem is None, report.problem
    return report


def one_result(outcome: str | None, message: str = "") -> bytes:
    """A TRX file of one result, as small as a reader accepts."""
    outcome_attribute = f' outcome="{outcome}"' if outcome is not None else ""
    error = (
        f"<Output><ErrorInfo><Message>{message}</Message></ErrorInfo></Output>" if message else ""
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<TestRun xmlns="{NS}">
  <Results><UnitTestResult testId="t1" testName="TC-X-1 a test"{outcome_attribute}>{error}
  </UnitTestResult></Results>
  <TestDefinitions><UnitTest id="t1">
    <TestMethod className="Agent.Tests.ATests" name="A_Runs" />
  </UnitTest></TestDefinitions>
</TestRun>""".encode()


# ── 1. the format is decided by the root ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("payload", "problem"),
    [
        (b"<TestRun/>", "TRX TestRun root"),  # no TeamTest namespace: not TRX
        (b"<assemblies/>", "TRX TestRun root"),  # xUnit's own XML is not read
        (f'<TestRun xmlns="{NS}"><Results/></TestRun>'.encode(), "no test results"),
        (f'<!DOCTYPE x><TestRun xmlns="{NS}"/>'.encode(), "DTDForbidden"),
    ],
)
@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_what_is_not_a_trx_with_results_is_refused(payload: bytes, problem: str) -> None:
    report = reports.read(payload)
    assert report.problem is not None and problem in report.problem
    assert not report.entries


@pytest.mark.verifies("REQ-QMT-22")
def test_each_format_is_told_by_its_root() -> None:
    assert read("cases-agent-full.trx").format == "trx"
    junit = reports.read(
        b'<testsuite><testcase classname="tests.test_x" name="test_x"/></testsuite>'
    )
    assert junit.format == "junit"


@pytest.mark.verifies("REQ-QMT-22")
def test_a_captured_trx_keeps_its_byte_order_mark_and_is_read() -> None:
    payload = (TRX / "cases-agent-full.trx").read_bytes()
    assert payload.startswith(b"\xef\xbb\xbf")
    assert len(reports.read(payload).entries) == 3


# ── 2. a run is one result, identified by class and method ─────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_a_theorys_rows_are_runs_of_one_method() -> None:
    entries = sorted(read("cases-agent-full.trx").entries, key=lambda e: e.name)
    assert [(e.classname, e.test, e.verdict) for e in entries] == [
        ("Agent.Tests.Unit.KeyCheckTests", "Admits_NoKey_IsFalse", "pass"),
        ("Agent.Tests.Unit.KeyCheckTests", "Admits_AnyKey_DecidesAlone", "pass"),
        ("Agent.Tests.Unit.KeyCheckTests", "Admits_AnyKey_DecidesAlone", "pass"),
    ]
    assert [e.name for e in entries] == [
        "TC-SVC-01.1 a call without a key is refused",
        'TC-SVC-01.2 the key check decides before any handler(key: "a-wrong-key", admitted: False)',
        'TC-SVC-01.2 the key check decides before any handler(key: "the-key", admitted: True)',
    ]


@pytest.mark.verifies("REQ-QMT-22")
def test_a_nested_class_and_an_inherited_test_are_reported_as_dotnet_names_them() -> None:
    identities = {(e.classname, e.test) for e in read("cases-agent-probe.trx").entries}
    assert ("Agent.Probe.Shapes+Nested", "Nested_Runs") in identities
    assert {("Agent.Probe.FirstDerived", "Inherited_Runs")} < identities
    assert {("Agent.Probe.SecondDerived", "Inherited_Runs")} < identities


@pytest.mark.verifies("REQ-QMT-22")
def test_a_result_without_a_definition_keeps_its_name_and_no_identity() -> None:
    payload = one_result("Passed").replace(b'testId="t1"', b'testId="elsewhere"')
    (entry,) = reports.read(payload).entries
    assert (entry.classname, entry.name, entry.test) == ("", "TC-X-1 a test", "")


# ── 3. outcomes ────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("outcome", "verdict", "kinds"),
    [
        ("Passed", "pass", ()),
        ("NotExecuted", "skip", ("NotExecuted",)),
        ("Failed", "fail", ("Failed",)),
        ("Error", "fail", ("Error",)),
        ("Timeout", "fail", ("Timeout",)),
        ("Aborted", "fail", ("Aborted",)),
        ("Inconclusive", "fail", ("Inconclusive",)),
        ("PassedButRunAborted", "fail", ("PassedButRunAborted",)),
        ("", "fail", ("no outcome",)),
        (None, "fail", ("no outcome",)),
    ],
)
@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_only_passed_passes_and_only_not_executed_skips(
    outcome: str | None, verdict: str, kinds: tuple[str, ...]
) -> None:
    (entry,) = reports.read(one_result(outcome)).entries
    assert (entry.verdict, entry.kinds) == (verdict, kinds)


@pytest.mark.verifies("REQ-QMT-22")
def test_only_the_first_line_of_an_error_message_is_kept() -> None:
    (entry,) = reports.read(one_result("Failed", "\n  Expected 1, but found 2.\nmore\n")).entries
    assert entry.details == ("Failed: Expected 1, but found 2.",)
    (passed,) = reports.read(one_result("Passed", "a message on a pass")).entries
    assert passed.details == ()


@pytest.mark.verifies("REQ-QMT-22")
def test_a_real_skip_and_failure_keep_their_reasons() -> None:
    entries = {e.name: e for e in read("cases-agent-mixed.trx").entries}
    skipped = entries["TC-SVC-01.1 a call without a key is refused"]
    assert (skipped.verdict, skipped.details) == (
        "skip",
        ("NotExecuted: the key store is offline",),
    )
    failed = next(e for e in entries.values() if e.verdict == "fail")
    assert failed.details == (
        'Failed: Expected KeyCheck.Admits(key, "the-key") to be True, but found False.',
    )


# ── 4. nothing of the build machine is read ────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_no_path_name_output_or_trace_reaches_the_report() -> None:
    payload = (TRX / "sentinel.trx").read_bytes()
    assert payload.count(b"SENTINEL") > 20  # planted in every field the reader must not read
    report = reports.read(payload)
    assert len(report.entries) == 3  # the summary's 999 is not trusted
    assert "SENTINEL" not in repr(report)


# ── 5. the join ────────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09", "DSN-QMT-15")
def test_every_probe_run_matches_the_identity_its_extractor_recorded() -> None:
    schema = (CASES / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")
    config = TraceConfig.parse(
        (CASES / "agent" / "qmstrace.toml").read_text(encoding="utf-8"), schema
    )
    probe = CASES / "agent" / "tests" / "Agent.Probe"
    recorded: dict[tuple[str, str], list[str]] = {}
    for path in sorted(probe.glob("*.cs")):
        found = xunit.extract(
            f"tests/Agent.Probe/{path.name}",
            path.read_text(encoding="utf-8"),
            config.item_types["automated_test"],
            config,
        )
        for item in found.items:
            for identity in item.runs_as:
                recorded.setdefault(identity, []).append(item.id)
    reported = {(e.classname, e.test) for e in read("cases-agent-probe.trx").entries}
    # The custom fact attribute runs, but is reported V15 rather than read as a test.
    assert reported - set(recorded) == {("Agent.Probe.Shapes", "CustomAttribute_Runs")}
    assert all(len(tests) == 1 for tests in recorded.values())
    # Each scanned test ran — a test inside #if is not scanned, so none is left over.
    assert set(recorded) <= reported
