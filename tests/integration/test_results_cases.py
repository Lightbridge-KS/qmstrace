"""Verdicts through test cases (ADR-0003), on real pytest output from the `cases` fixture.

The load-bearing claims, each pinned by a test:

1. A requirement's verdict is the worst of every automated test that reaches it — directly, or
   through the test cases they run; the cases on the way are named, each with its own verdict.
2. A failure only a design element sees changes no requirement's verdict, and is still shown.
3. A test case no automated test runs contributes nothing: it neither passes nor blocks.
4. A chain of test cases is followed, and a cycle among them is walked once.
5. A sibling's own links are read for verdicts and never counted or walked as this repo's.
6. Where no test case stands between, every verdict is what direct links alone give.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.core.results import Results, Verdict
from qmstrace.workspace import Workspace

JUNIT = Path(__file__).parents[1] / "fixtures" / "junit" / "service.xml"
_RANK = {"untested": 0, "pass": 1, "skip": 2, "no-result": 3, "fail": 4}


def run_pytest(root: Path, expect: int = 0) -> Results:
    """Run the service's real tests, write JUnit, and read it back with `results`."""
    (root / "pytest.ini").write_text("[pytest]\nmarkers = verifies: trace targets\n")
    env = {key: value for key, value in os.environ.items() if key != "PYTEST_ADDOPTS"}
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pytest.ini",
            "--junitxml=report.xml",
            "tests",
            "-q",
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert done.returncode == expect, done.stdout + done.stderr
    return Workspace.open(root).results(root / "report.xml")


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, (path.name, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def verdicts(view: Results) -> dict[str, Verdict]:
    return {target.node.id: target.verdict for target in view.requirements}


# ── 1. through test cases ──────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_a_verdict_reaches_a_requirement_through_its_test_cases(cases: Path) -> None:
    view = run_pytest(cases / "service")
    assert not view.unmatched and view.matched_cases == view.scanned_cases == 5
    by_id = {target.node.id: target for target in view.requirements}
    one = by_id["REQ-SVC-01"]
    assert one.verdict == "pass"
    assert [case.node.id for case in one.via] == ["TC-SVC-01.1"]
    assert len(one.tests) == 2 and one.via[0].verdict == "pass"
    # REQ-SVC-02 is verified directly, and by a planned test case nothing runs yet.
    two = by_id["REQ-SVC-02"]
    assert two.verdict == "pass" and two.via == ()
    assert [test.id.rsplit("::", 1)[-1] for test in two.tests] == [
        "test_a_record_survives_a_restart"
    ]
    assert [(c.node.id, c.verdict, c.verifies) for c in view.other_cases] == [
        ("TC-SVC-01.2", "pass", ("DSN-SVC-01",)),
        ("TC-SVC-02.1", "pass", ("DSN-SVC-02",)),
    ]
    assert view.other_tests == ()  # each test that reaches no requirement is under its case


@pytest.mark.verifies("REQ-QMT-10")
def test_the_output_names_the_test_cases_on_the_way(cases: Path, golden) -> None:
    root = cases / "service"
    run_pytest(root)
    result = CliRunner().invoke(app, ["-C", str(root), "results", "report.xml"])
    assert result.exit_code == 0, result.output
    golden(Path(__file__).parents[1] / "cli" / "golden" / "results-cases.txt", result.output)
    assert "REQ-SVC-01  pass      via TC-SVC-01.1 · 2 automated tests" in result.output
    assert "test cases that reach no requirement" in result.output


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_a_failing_test_fails_its_test_case_and_its_requirement(cases: Path) -> None:
    root = cases / "service"
    edit(root / "tests/unit/test_api.py", 'assert "a-wrong-key" not in {"the-key"}', "assert False")
    view = run_pytest(root, expect=1)
    one = next(t for t in view.requirements if t.node.id == "REQ-SVC-01")
    assert one.verdict == "fail" and one.via[0].verdict == "fail"
    assert verdicts(view)["REQ-SVC-02"] == "pass"


# ── 2. a failure only a design element sees ────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10")
def test_a_failure_only_a_design_element_sees_is_shown_and_changes_no_requirement(
    cases: Path,
) -> None:
    root = cases / "service"
    edit(
        root / "tests/unit/test_api.py",
        "def test_the_key_check_runs_before_any_handler():\n    assert True",
        "def test_the_key_check_runs_before_any_handler():\n    assert False",
    )
    view = run_pytest(root, expect=1)
    assert set(verdicts(view).values()) == {"pass"}
    failing = {c.node.id: c for c in view.other_cases}["TC-SVC-01.2"]
    assert failing.verdict == "fail" and failing.verifies == ("DSN-SVC-01",)


# ── 3. a test case nothing runs ────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10")
def test_a_test_case_nothing_runs_neither_passes_nor_blocks(cases: Path) -> None:
    root = cases / "service"
    edit(
        root / "tests/integration/test_store.py",
        "def test_a_record_survives_a_restart():\n    assert True",
        "def test_a_record_survives_a_restart():\n    assert False",
    )
    view = run_pytest(root, expect=1)
    # REQ-SVC-02's verdict is its direct test's alone: the planned TC-SVC-02.2 adds no
    # `no-result`, and cannot mask the failure.
    assert verdicts(view)["REQ-SVC-02"] == "fail"


# ── 4. chains and cycles ───────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_a_chain_of_test_cases_is_followed_and_a_cycle_walked_once(cases: Path) -> None:
    spec = cases / "ledger/docs/test/service-test-cases.md"
    edit(spec, "verifies: DSN-SVC-02\n", "verifies: DSN-SVC-02, TC-SVC-01.1\n")
    edit(spec, "verifies: REQ-SVC-01\n", "verifies: REQ-SVC-01, TC-SVC-02.1\n")
    view = run_pytest(cases / "service")
    one = next(t for t in view.requirements if t.node.id == "REQ-SVC-01")
    # TC-SVC-02.1's test reaches REQ-SVC-01 through TC-SVC-01.1, around the cycle once.
    assert len(one.tests) == 3 and one.verdict == "pass"
    assert {c.node.id for c in one.via} == {"TC-SVC-01.1"}


# ── 5. a sibling's own links ───────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-09", "DSN-QMT-05")
def test_a_siblings_own_links_are_never_counted_or_walked_as_this_repos(cases: Path) -> None:
    root = cases / "service"
    graph = Workspace.open(root).assessment().graph
    assert len(graph.links) == 7  # five tests' verifies, two modules' Implements
    assert {link.src for node in graph.nodes.values() for link in node.declares} >= {
        "TC-SVC-01.1",
        "DSN-SVC-01",
    }
    status = CliRunner().invoke(app, ["-C", str(root), "status"])
    assert "links: 7" in status.output
    thread = CliRunner().invoke(app, ["-C", str(root), "thread", "TC-SVC-01.1"])
    assert "REQ-SVC-01" not in thread.output  # a sibling's links are not walked from here


# ── 6. where no test case stands between ───────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10")
def test_with_no_test_case_between_every_verdict_is_what_direct_links_give(project: Path) -> None:
    root = project / "service"
    (root / "report.xml").write_bytes(JUNIT.read_bytes())
    view = Workspace.open(root).results(root / "report.xml")
    for target in view.requirements:
        direct = [t.verdict for t in target.tests if target.node.id in t.verifies]
        expected = max(direct, key=_RANK.__getitem__) if direct else "untested"
        assert (target.verdict, target.via) == (expected, ()), target.node.id
        assert len(direct) == len(target.tests)
    assert view.other_cases == () and not view.through_cases
