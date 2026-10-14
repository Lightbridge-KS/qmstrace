"""`results` over TRX (ADR-0004), on reports captured from the `cases` fixture's real C# agent.

The load-bearing claims, each pinned by a test:

1. A TRX run is matched to the xUnit method it ran, and its verdict follows `verifies` links
   through the test cases — as a pytest run's does; a Theory's rows are runs of one test.
2. A skipped or failed run gives its test case and requirement that verdict, with the reason's
   first line; a test the report leaves out is `no-result`.
3. Two methods sharing a display name are two runs, never one.
4. A report from another repo, or of another format, is refused with the next move for the
   format given.
5. Nothing of the report's paths, machine or user names, output or traces is printed.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.workspace import Workspace

TRX = Path(__file__).parents[1] / "fixtures" / "trx"
JUNIT = Path(__file__).parents[1] / "fixtures" / "junit" / "service.xml"
GOLDEN = Path(__file__).parents[1] / "cli" / "golden"


def results(root: Path, report: Path) -> tuple[int, str]:
    """Run `results` on a report copied into the repo, so its label is a short relative path."""
    shutil.copyfile(report, root / f"report{report.suffix}")
    done = CliRunner().invoke(app, ["-C", str(root), "results", f"report{report.suffix}"])
    return done.exit_code, done.output


# ── 1. a TRX run is matched to its method ──────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_a_trx_gives_verdicts_through_test_cases(cases: Path, golden) -> None:
    root = cases / "agent"
    code, output = results(root, TRX / "cases-agent-full.trx")
    assert code == 0, output
    golden(GOLDEN / "results-trx.txt", output)
    view = Workspace.open(root).results(root / "report.trx")
    assert not view.unmatched and view.matched_cases == view.scanned_cases == 2
    (requirement,) = view.requirements
    assert (requirement.node.id, requirement.verdict) == ("REQ-SVC-01", "pass")
    assert [case.node.id for case in requirement.via] == ["TC-SVC-01.1"]
    (theory,) = [test for case in view.other_cases for test in case.tests]
    assert theory.id.endswith("::KeyCheckTests::Admits_AnyKey_DecidesAlone")
    assert len(theory.runs) == 2  # a Theory's rows are runs of one automated test


# ── 2. skips, failures and runs left out ───────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_a_skip_and_a_failing_row_are_shown_with_their_reasons(cases: Path, golden) -> None:
    code, output = results(cases / "agent", TRX / "cases-agent-mixed.trx")
    assert code == 0, output
    golden(GOLDEN / "results-trx-mixed.txt", output)
    assert "REQ-SVC-01  skip      via TC-SVC-01.1" in output
    assert "NotExecuted: the key store is offline" in output
    assert "TC-SVC-01.2  fail · 1 automated tests · verifies DSN-SVC-01" in output
    assert "admitted: True) (Failed)" in output


@pytest.mark.verifies("REQ-QMT-22")
def test_a_test_the_report_leaves_out_has_no_result(cases: Path) -> None:
    root = cases / "agent"
    shutil.copyfile(TRX / "cases-agent-filtered.trx", root / "report.trx")
    view = Workspace.open(root).results(root / "report.trx")
    (requirement,) = view.requirements
    assert requirement.verdict == "no-result" and requirement.via[0].verdict == "no-result"
    assert (view.matched_cases, view.scanned_cases) == (1, 2)


# ── 3. a shared display name ───────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_two_methods_sharing_a_display_name_are_two_runs(cases: Path) -> None:
    root = cases / "agent"
    source = root / "tests/Agent.Tests/Unit/KeyCheckTests.cs"
    fact = '    [Fact(DisplayName = "TC-SVC-01.1 a call without a key is refused")]\n'
    text = source.read_text(encoding="utf-8")
    assert fact in text
    source.write_text(
        text.replace(
            fact,
            fact + "    public void Admits_EmptyKey_IsFalse() { }\n\n" + fact,
            1,
        ),
        encoding="utf-8",
    )
    trx = (TRX / "cases-agent-full.trx").read_text(encoding="utf-8-sig")
    result = '<UnitTestResult executionId="44082393'
    definition = '<UnitTest name="TC-SVC-01.1 a call without a key is refused"'
    start, end = trx.index(result), trx.index("/>", trx.index(result)) + 2
    twin = (
        trx[start:end]
        .replace('testId="df662282', 'testId="0ddba11e')
        .replace('outcome="Passed"', 'outcome="Failed"')
    )
    d_start = trx.index(definition)
    d_end = trx.index("</UnitTest>", d_start) + len("</UnitTest>")
    twin_definition = (
        trx[d_start:d_end]
        .replace('id="df662282', 'id="0ddba11e')
        .replace('name="Admits_NoKey_IsFalse"', 'name="Admits_EmptyKey_IsFalse"')
    )
    trx = trx[:end] + twin + trx[end:d_end] + twin_definition + trx[d_end:]
    (root / "report.trx").write_text(trx, encoding="utf-8")
    view = Workspace.open(root).results(root / "report.trx")
    assert (view.runs, view.matched_runs, view.duplicates) == (4, 4, 0)
    (requirement,) = view.requirements
    assert requirement.verdict == "fail"
    assert sorted((t.id.rsplit("::", 1)[-1], t.verdict) for t in requirement.tests) == [
        ("Admits_EmptyKey_IsFalse", "fail"),
        ("Admits_NoKey_IsFalse", "pass"),
    ]


# ── 4. another repo's report, or another format ────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22")
def test_a_report_that_matches_nothing_is_refused_with_its_formats_next_move(
    cases: Path,
) -> None:
    code, output = results(cases / "agent", TRX / "cases-agent-probe.trx")
    assert code == 2
    assert "no report entries match the 2 scanned automated tests" in output
    assert "('Agent.Probe.Shapes+Nested', 'TC-BAG-90.16 nested class'): no scanned automated" in (
        output
    )
    assert "use a TRX file from this repo's test projects" in output
    code, output = results(cases / "agent", JUNIT)
    assert code == 2 and "default pytest JUnit class names" in output
    code, output = results(cases / "service", TRX / "cases-agent-full.trx")
    assert code == 2 and "no report entries match the 5 scanned automated tests" in output


@pytest.mark.verifies("REQ-QMT-22")
def test_an_unmatched_trx_run_names_the_trx_way_to_match(cases: Path) -> None:
    root = cases / "agent"
    trx = (TRX / "cases-agent-full.trx").read_text(encoding="utf-8-sig")
    (root / "report.trx").write_text(
        trx.replace('name="Admits_NoKey_IsFalse"', 'name="Admits_NoKey_WasRenamed"'),
        encoding="utf-8",
    )
    done = CliRunner().invoke(app, ["-C", str(root), "results", "report.trx"])
    assert done.exit_code == 0, done.output
    assert "no scanned automated test matches this identity" in done.output
    assert "a TRX run matches by the class and method dotnet test reports" in done.output


# ── 5. nothing of the build machine is printed ─────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-22", "DSN-QMT-09")
def test_no_path_name_output_or_trace_is_printed(cases: Path) -> None:
    code, output = results(cases / "agent", TRX / "sentinel.trx")
    assert code == 0, output
    assert "SENTINEL" not in output
    # The first line of each reason is shown; the line after it, planted with SENTINEL, is not.
    assert "Failed: Expected KeyCheck.Admits" in output
    assert "NotExecuted: the key store is offline" in output
