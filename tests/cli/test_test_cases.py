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
    assert gap.startswith("G09  ledger:docs/test/service-test-cases.md:")
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
    # A class, a Razor page and a file of top-level statements, all three marked (#64).
    assert "component         3 items in  3 files  src/**/*.cs, src/**/*.razor" in status
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


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_a_gaps_next_move_cites_only_its_own_tests_unread_marker(cases: Path) -> None:
    """Many tests share a C# file: a test's gap points at a finding about that test, never at
    the first one in its file."""
    agent = cases / "agent"
    config = agent / "qmstrace.toml"
    text = config.read_text(encoding="utf-8")
    old = 'files     = ["tests/Agent.Tests/**/*Tests.cs"]'
    assert old in text
    config.write_text(text.replace(old, 'files     = ["tests/Agent.Probe/**/*.cs"]'))
    _, output = run("-C", str(agent), "check")
    by_test = {gap.split("::")[-1].split(":")[0]: gap for gap in gaps(output) if "G07" in gap}
    # A test with no DisplayName is told to write one; nothing else in the file is its reason.
    assert "V15" not in by_test["NoDisplayName_Runs"]
    assert '[Fact(DisplayName = "<' in by_test["NoDisplayName_Runs"]
    # A test whose DisplayName is not read is sent to its own finding, on its own line.
    concatenation = next(line for line in output.splitlines() if "ConstConcatenation_Runs" in line)
    line = concatenation.split("Shapes.cs:")[1].split()[0]
    assert (
        f"first fix V15 at tests/Agent.Probe/Shapes.cs:{line} "
        in by_test["ConstConcatenation_Runs"]
    )
    assert f"Shapes.cs:{line} " not in by_test["ConstInterpolation_Runs"]


@pytest.mark.verifies("DSN-QMT-06", "DSN-QMT-15")
def test_a_test_with_nothing_to_point_at_here_is_sent_to_the_ledgers_items(cases: Path) -> None:
    """Where the ledger holds the documents (ADR-0001), a product repo declares no target of a
    test's link: the next move names the ledger, never "write the design here"."""
    agent = cases / "agent"
    source = agent / "tests/Agent.Tests/Unit/KeyCheckTests.cs"
    text = source.read_text(encoding="utf-8")
    old = '[Fact(DisplayName = "TC-SVC-01.1 a call without a key is refused")]'
    assert old in text
    source.write_text(text.replace(old, '[Fact(DisplayName = "a call without a key is refused")]'))
    _, output = run("-C", str(agent), "check")
    (gap,) = [g for g in gaps(output) if g.startswith("G07")]
    assert "::KeyCheckTests::Admits_NoKey_IsFalse: verifies nothing." in gap
    assert (
        "this repo declares no requirement or design element or test case for it to point at, "
        'but ledger does: write `[Fact(DisplayName = "<requirement or design element or test '
        'case ID> …")]` on the test method, citing an item of ledger — only if it is true'
    ) in gap
    assert "write the design here" not in gap
