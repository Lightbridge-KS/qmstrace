"""Test cases in the trace (ADR-0003) — a Test Specification in the ledger, run by automated tests.

The load-bearing claims, each pinned by a test:

1. A test case is declared by a heading in a Test Specification, its `verifies:` line its link;
   an automated test verifies a test case, or a requirement directly — both in one project.
2. The ledger's check judges them together: a test case no automated test runs is a gap, and
   its next move names where to write the link, in the repo that holds automated tests.
3. One repo's own check names every way a link can be made, including a source read in another
   repo — never only the first one it scans.

Regenerate a golden after an intended change: `QMSTRACE_REGOLD=1 uv run pytest tests/cli`, then
read the diff before committing it.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
Golden = Callable[[Path, str], None]
runner = CliRunner()


def run(*words: str) -> tuple[int, str]:
    result = runner.invoke(app, list(words))
    return result.exit_code, result.output


def gaps(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.startswith("  G")]


# ── 1 & 2. the project as a whole ──────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-02", "DSN-QMT-06", "DSN-QMT-14")
def test_the_ledgers_check_judges_test_cases_with_the_automated_tests_that_run_them(
    cases: Path, golden: Golden
) -> None:
    code, output = run("-C", str(cases / "ledger"), "ledger", "check", "--strict")
    assert code == 1
    golden(GOLDEN / "ledger-check-cases.txt", output)
    # Every test case is read whole and run, but one: the planned TC-SVC-02.2.
    (gap,) = gaps(output)
    assert gap.startswith("G09  docs/test/service-test-cases.md:")
    assert "TC-SVC-02.2: no automated test runs it yet." in gap
    # Two repos run automated tests, read by two extractors: the next move names both ways.
    assert 'on the automated test in service, `@pytest.mark.verifies("TC-SVC-02.2")`' in gap
    assert 'on the automated test in agent, `[Fact(DisplayName = "TC-SVC-02.2 …")]`' in gap
    assert "on the test case" not in gap  # a test case verifying a test case is never suggested


@pytest.mark.verifies("REQ-QMT-02")
def test_test_cases_are_items_of_the_ledger(cases: Path) -> None:
    code, output = run("-C", str(cases / "ledger"), "status")
    assert code == 0
    assert "test_case         4 items in  1 file   docs/test/*-test-cases.md" in output


# ── 3. one repo's own check ────────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-06")
def test_the_ledgers_own_check_names_the_automated_tests_another_repo_holds(
    cases: Path, golden: Golden
) -> None:
    code, output = run("-C", str(cases / "ledger"), "check", "--strict")
    assert code == 1
    golden(GOLDEN / "check-cases-ledger.txt", output)
    g09 = [gap for gap in gaps(output) if gap.startswith("G09")]
    assert len(g09) == 4
    for gap in g09:
        assert "this repo declares no automated test" in gap
        assert "qmstrace ledger check, run in the ledger, judges that" in gap
        assert "on the test case, write" not in gap


# ── 4. a C# repo in the same project (ADR-0004) ────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_a_csharp_repos_status_and_gate(cases: Path, golden: Golden) -> None:
    agent = str(cases / "agent")
    code, status = run("-C", agent, "status")
    assert code == 0
    golden(GOLDEN / "status-cases-agent.txt", status)
    assert "component         1 item  in  1 file   src/**/*.cs" in status
    assert "[Fact]/[Theory] methods: a Theory is one automated test" in status
    code, output = run("-C", agent, "check", "--strict")
    assert code == 0, output
    golden(GOLDEN / "check-cases-agent.txt", output)


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-06", "DSN-QMT-14")
def test_a_gap_three_ways_can_meet_names_all_three_in_the_ledgers_check(cases: Path) -> None:
    spec = cases / "ledger/docs/test/service-test-cases.md"
    spec.write_text(spec.read_text(encoding="utf-8").replace("verifies: REQ-SVC-01\n", "", 1))
    code, output = run("-C", str(cases / "ledger"), "ledger", "check")
    assert code == 0
    (g02,) = [gap for gap in gaps(output) if gap.startswith("G02")]
    assert "REQ-SVC-01" in g02 and "write one of these — " in g02
    for way in (
        'on the automated test in agent, `[Fact(DisplayName = "REQ-SVC-01 …")]` on the test method',
        'on the automated test in service, `@pytest.mark.verifies("REQ-SVC-01")` on the test',
        "on the test case in ledger, `verifies: REQ-SVC-01` under its heading",
    ):
        assert way in g02, way
    assert any(gap.startswith("G08") and "TC-SVC-01.1" in gap for gap in gaps(output))
