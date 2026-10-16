"""Several reports read as one (ADR-0005, #40).

The load-bearing claims, each pinned by a test:

1. Order never matters: any order of the same reports gives the same view, byte for byte.
2. A run in two reports is one run — its worst verdict, both reports named, counted once as a
   duplicate.
3. Each run keeps its source: the report's label and the sha256 of its bytes; a report naming a
   repo matches only that repo's automated tests.
4. A label is never a path of the machine: inside the repo, the path from the root; outside it,
   the file name. Two reports one label would hide, and a report given twice, are refused.
"""

from __future__ import annotations

import hashlib
import itertools
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.core import results
from qmstrace.core.results import (
    Report,
    ReportEntry,
    ReportSource,
    Results,
    RunResult,
    summarize,
)
from qmstrace.extract.pytest_tests import report_identity
from qmstrace.workspace import Workspace

KEY = "tests/unit/test_keys.py::test_a_call_without_a_valid_key_is_refused"
STORE = "tests/integration/test_store.py::test_a_record_survives_a_restart"
RESTART = "tests/integration/test_store.py::test_a_restart_loses_no_accepted_record"
runner = CliRunner()


def junit(path: Path, entries: list[tuple[str, str]]) -> Path:
    """A pytest JUnit report at `path`, one entry per (node ID, verdict)."""
    suite = Element("testsuite")
    for node_id, verdict in entries:
        classname, name = report_identity(node_id)
        case = SubElement(suite, "testcase", classname=classname, name=name)
        if verdict != "pass":
            SubElement(case, {"fail": "failure", "skip": "skipped"}[verdict])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(tostring(suite))
    return path


def listed_tests(view: Results) -> dict[str, results.TestResult]:
    """Every automated test in the view, wherever it is listed."""
    targets = (*view.requirements, *view.other_methods, *view.unverified_targets)
    found = [t for target in targets for t in target.tests]
    found += [*view.other_tests, *(t for case in view.other_cases for t in case.tests)]
    return {test.id: test for test in found}


def runs_of(view: Results) -> list[RunResult]:
    return [run for test in listed_tests(view).values() for run in test.runs]


def run(root: Path, *reports: str) -> tuple[int, str]:
    done = runner.invoke(app, ["-C", str(root), "results", *reports])
    return done.exit_code, done.output


# ── 1. order never matters ─────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_any_order_of_the_reports_gives_the_same_view_byte_for_byte(project: Path) -> None:
    root = project / "service"
    junit(root / "reports" / "a.xml", [(KEY, "pass"), (STORE, "fail")])
    junit(root / "reports" / "b.xml", [(KEY, "fail")])
    junit(root / "reports" / "c.xml", [(RESTART, "skip"), (STORE, "pass")])
    names = ["reports/a.xml", "reports/b.xml", "reports/c.xml"]
    outputs = {run(root, *order) for order in itertools.permutations(names)}
    assert len(outputs) == 1
    ((code, output),) = outputs
    assert code == 0, output
    first, *others = [
        Workspace.open(root).results(*(root / name for name in order))
        for order in itertools.permutations(names)
    ]
    assert all(view == first for view in others)


# ── 2. a run in two reports ────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_a_run_in_two_reports_is_one_run_with_its_worst_verdict(project: Path) -> None:
    root = project / "service"
    unit = junit(root / "reports" / "unit.xml", [(KEY, "pass"), (STORE, "pass")])
    again = junit(root / "reports" / "again.xml", [(KEY, "fail")])
    view = Workspace.open(root).results(unit, again)
    assert (view.entries, view.runs, view.duplicates) == (3, 2, 1)
    (key,) = listed_tests(view)[KEY].runs
    assert (key.verdict, key.entries) == ("fail", 2)
    assert [s.label for s in key.sources] == ["reports/again.xml", "reports/unit.xml"]
    code, output = run(root, "reports/unit.xml", "reports/again.xml")
    assert code == 0, output
    assert "reports: 2\n  reports/again.xml · 1 XML entries\n  reports/unit.xml · 2 XML" in output
    assert "1 duplicate XML entries combined by full identity" in output
    assert "· reported in reports/again.xml, reports/unit.xml" in output


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_a_test_missing_from_one_projects_report_takes_its_verdict_from_the_other(
    cases: Path,
) -> None:
    """The case #40 was filed for: one report per test project, read together."""
    trx = Path(__file__).parents[1] / "fixtures" / "trx"
    root = cases / "agent"
    for name, captured in (
        ("filtered", "cases-agent-filtered.trx"),
        ("full", "cases-agent-full.trx"),
    ):
        (root / "TestResults").mkdir(exist_ok=True)
        (root / "TestResults" / f"{name}.trx").write_bytes((trx / captured).read_bytes())
    alone = Workspace.open(root).results(root / "TestResults" / "filtered.trx")
    assert [t.verdict for t in alone.requirements] == ["no-result"]
    both = Workspace.open(root).results(
        root / "TestResults" / "filtered.trx", root / "TestResults" / "full.trx"
    )
    assert [t.verdict for t in both.requirements] == ["pass"]
    assert (both.entries, both.runs, both.duplicates) == (5, 3, 2)


# ── 3. each run keeps its source ───────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_each_run_keeps_the_label_and_sha256_of_its_report(project: Path) -> None:
    root = project / "service"
    unit = junit(root / "reports" / "unit.xml", [(KEY, "pass")])
    store = junit(root / "reports" / "store.xml", [(STORE, "fail")])
    view = Workspace.open(root).results(unit, store)
    digests = {s.label: s.sha256 for r in view.reports for s in [r.source]}
    assert digests == {
        "reports/store.xml": hashlib.sha256(store.read_bytes()).hexdigest(),
        "reports/unit.xml": hashlib.sha256(unit.read_bytes()).hexdigest(),
    }
    sources = [source for found in runs_of(view) for source in found.sources]
    assert {s.label for s in sources} == set(digests)
    assert all(s.sha256 == digests[s.label] for s in sources)


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_a_report_naming_a_repo_matches_only_that_repos_tests(project: Path) -> None:
    root = project / "service"
    assessment = Workspace.open(root).assessment()
    identities = {i.id: i.runs_as for i in assessment.graph.items() if i.runs_as}
    classname, name = report_identity(KEY)
    entry = Report((ReportEntry(classname, name, "fail"),), format="junit")
    passed = Report((ReportEntry(classname, name, "pass"),), format="junit")
    repos = dict.fromkeys(identities, "service")
    view = summarize(
        assessment,
        {
            ReportSource("other.xml", "1", "client"): entry,
            ReportSource("own.xml", "2", "service"): passed,
        },
        identities,
        repos,
    )
    (other,) = view.unmatched
    assert other.run.verdict == "fail" and [s.repo for s in other.run.sources] == ["client"]
    assert view.matched_runs == 1 and view.duplicates == 0  # one identity, two repos: two runs


# ── 4. a label is never a path of the machine ──────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_a_report_outside_the_repo_is_shown_by_its_file_name_alone(
    project: Path, tmp_path: Path
) -> None:
    root = project / "service"
    outside = junit(tmp_path / "SENTINEL-build" / "agent-07" / "unit.xml", [(KEY, "pass")])
    inside = junit(root / "reports" / "store.xml", [(STORE, "pass")])
    code, output = run(root, str(outside), "reports/store.xml")
    assert code == 0, output
    assert "SENTINEL" not in output
    assert str(tmp_path) not in output
    assert "  unit.xml · 1 XML entries" in output
    view = Workspace.open(root).results(outside.resolve(), inside)
    assert [r.source.label for r in view.reports] == ["reports/store.xml", "unit.xml"]


@pytest.mark.verifies("REQ-QMT-10")
def test_two_reports_one_label_and_a_report_given_twice_are_refused(
    project: Path, tmp_path: Path
) -> None:
    root = project / "service"
    first = junit(tmp_path / "one" / "report.xml", [(KEY, "pass")])
    second = junit(tmp_path / "two" / "report.xml", [(KEY, "fail")])
    code, output = run(root, str(first), str(second))
    assert code == 2
    assert "Two reports would both be shown as report.xml" in output
    assert "give them distinct file names, or copy them into the repo" in output
    junit(root / "report.xml", [(KEY, "pass")])
    code, output = run(root, "report.xml", "./report.xml")
    assert code == 2 and "Report report.xml is given twice" in output


@pytest.mark.verifies("REQ-QMT-10", "DSN-QMT-09")
def test_two_trx_files_golden(cases: Path, golden) -> None:
    """Two captured runs of the agent's tests, read together: each report listed with its count,
    the worst verdict kept, and each run that did not pass naming the report it came from."""
    trx = Path(__file__).parents[1] / "fixtures" / "trx"
    root = cases / "agent"
    (root / "TestResults").mkdir()
    (root / "TestResults" / "first.trx").write_bytes((trx / "cases-agent-full.trx").read_bytes())
    (root / "TestResults" / "second.trx").write_bytes((trx / "cases-agent-mixed.trx").read_bytes())
    code, output = run(root, "TestResults/second.trx", "TestResults/first.trx")
    assert code == 0, output
    golden(Path(__file__).parents[1] / "cli" / "golden" / "results-trx-several.txt", output)
    assert "2 duplicate XML entries combined by full identity" in output
