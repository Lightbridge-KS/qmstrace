"""Results are informational, direct, exact, and explicit about incomplete evidence."""

from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.core.results import Results
from qmstrace.extract.pytest_tests import report_identity
from qmstrace.render import text
from qmstrace.workspace import Workspace

GOLDEN = Path(__file__).parent / "golden"
FIXTURE = Path(__file__).parents[1] / "fixtures/junit/service.xml"
runner = CliRunner()
KEY = "tests/unit/test_keys.py::test_a_call_without_a_valid_key_is_refused"
STORE = "tests/integration/test_store.py::test_a_record_survives_a_restart"
RESTART = "tests/integration/test_store.py::test_a_restart_loses_no_accepted_record"


def report(root: Path, entries: list[tuple[str, str]]) -> Path:
    suite = Element("testsuite")
    for node_id, verdict in entries:
        classname, name = report_identity(node_id)
        case = SubElement(suite, "testcase", classname=classname, name=name)
        if verdict != "pass":
            SubElement(case, {"fail": "failure", "skip": "skipped", "error": "error"}[verdict])
    path = root / "report.xml"
    path.write_bytes(tostring(suite))
    return path


def verdicts(view: Results) -> dict[str, str]:
    return {target.node.id: target.verdict for target in view.requirements}


@pytest.mark.verifies("REQ-QMT-10")
def test_partial_failure_golden(project: Path, golden: Callable[[Path, str], None]) -> None:
    root = project / "service"
    (root / "report.xml").write_bytes(FIXTURE.read_bytes())
    result = runner.invoke(app, ["-C", str(root), "results", "report.xml"])
    assert result.exit_code == 0, result.output
    assert "6 XML entries · 5 reported runs" in result.output
    assert "matched: 4 runs of 3 automated tests" in result.output
    assert "shared: also verifies DSN-SVC-02" in result.output
    assert "record missing after restart" in result.output
    assert "no-result" in result.output and "unmatched report entries" in result.output
    golden(GOLDEN / "results-partial.txt", result.output)
    view = Workspace.open(root).results(root / "report.xml")
    assert verdicts(view) == {"REQ-SVC-01": "pass", "REQ-SVC-02": "fail"}
    assert view.duplicates == 1 and view.matched_cases == 3 and view.scanned_cases == 4


def test_input_order_does_not_change_output(project: Path) -> None:
    root = project / "service"
    entries = [(KEY + "[b[c]]", "skip"), (KEY + "[a]", "pass"), (STORE, "fail"), (STORE, "error")]
    workspace = Workspace.open(root)
    first = text.results(workspace.results(report(root, entries)))
    assert first == text.results(workspace.results(report(root, entries[::-1])))


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        ([(STORE, "pass")], "no-result"),
        ([(STORE, "skip")], "no-result"),
        ([(STORE, "fail")], "fail"),
        ([(STORE, "pass"), (RESTART, "skip")], "skip"),
        ([(STORE, "pass"), (RESTART, "pass")], "pass"),
    ],
)
@pytest.mark.verifies("DSN-QMT-09")
def test_requirement_precedence(
    project: Path, entries: list[tuple[str, str]], expected: str
) -> None:
    root = project / "service"
    view = Workspace.open(root).results(report(root, entries))
    assert verdicts(view)["REQ-SVC-02"] == expected


def test_test_case_precedence_and_duplicate_link_counts(project: Path) -> None:
    root = project / "service"
    source = root / "tests/unit/test_keys.py"
    source.write_text(
        source.read_text().replace('"REQ-SVC-01"', '"REQ-SVC-01", "REQ-SVC-01", "REQ-SVC-02"')
    )
    view = Workspace.open(root).results(
        report(root, [(KEY + "[a]", "pass"), (KEY + "[b]", "skip")])
    )
    assert view.matched_cases == 1 and view.matched_runs == 2
    assert verdicts(view)["REQ-SVC-01"] == "skip"
    target = view.requirements[0]
    assert len(target.tests) == 1 and target.runs == 2
    assert target.tests[0].verifies == ("REQ-SVC-01", "REQ-SVC-02")


@pytest.mark.parametrize("method", ["inspection", "analysis"])
def test_other_methods_and_untested_requirements(project: Path, method: str) -> None:
    root = project / "service"
    srs = root / "docs/req/service-srs.md"
    srs.write_text(
        srs.read_text().replace("Verify-by: inspection", f"Verify-by: {method}")
        + "\n## REQ-SVC-04 — Untested\nCategory: security\nOrigin: AGR-1\nVerify-by: test\n"
    )
    source = root / "tests/unit/test_keys.py"
    source.write_text(source.read_text().replace('"REQ-SVC-01"', '"REQ-SVC-03"'))
    view = Workspace.open(root).results(report(root, [(KEY, "fail")]))
    assert verdicts(view)["REQ-SVC-01"] == "untested"
    assert verdicts(view)["REQ-SVC-04"] == "untested"
    assert "REQ-SVC-03" not in verdicts(view)
    assert view.other_methods[0].method == method
    assert view.other_methods[0].verdict == "fail"
    assert "linked tests only: fail" in text.results(view)


@pytest.mark.verifies("REQ-QMT-10")
def test_design_results_do_not_flow_to_requirements(project: Path) -> None:
    root = project / "service"
    node = "tests/unit/test_keys.py::TestTheKeyCheck::test_it_runs_before_any_handler"
    view = Workspace.open(root).results(report(root, [(node, "fail")]))
    assert verdicts(view)["REQ-SVC-01"] == "no-result"
    assert view.other_tests[0].verdict == "fail"


@pytest.mark.parametrize("available", [True, False])
def test_sibling_and_unknown_targets(
    project: Path,
    alone: Callable[[str], Path],
    golden: Callable[[Path, str], None],
    available: bool,
) -> None:
    root = project / "client" if available else alone("client")
    path = report(
        root, [("tests/unit/test_api.py::test_the_service_refuses_a_call_without_a_key", "pass")]
    )
    view = Workspace.open(root).results(path)
    output = text.results(view)
    if available:
        assert verdicts(view)["REQ-SVC-01"] == "pass"
        assert "REQ-SVC-02" not in verdicts(view)
        assert "sibling service — not pinned" in output
    else:
        assert "REQ-SVC-01" not in verdicts(view)
        assert view.unverified_targets[0].node.id == "REQ-SVC-01"
        assert "type unknown, not requirement verdicts" in output
        assert "NOT REACHABLE" in output
    golden(GOLDEN / f"results-{'sibling' if available else 'in-a-pipeline'}.txt", output + "\n")


def test_sibling_inspection_method_is_preserved(project: Path) -> None:
    root = project / "client"
    source = root / "tests/unit/test_api.py"
    source.write_text(source.read_text().replace("REQ-SVC-01", "REQ-SVC-03"))
    view = Workspace.open(root).results(
        report(
            root,
            [("tests/unit/test_api.py::test_the_service_refuses_a_call_without_a_key", "pass")],
        )
    )
    assert "REQ-SVC-03" not in verdicts(view)
    assert view.other_methods[0].method == "inspection"
    assert "sibling service — not pinned" in text.results(view)


def test_refused_links_are_not_used(project: Path) -> None:
    root = project / "service"
    source = root / "tests/unit/test_keys.py"
    source.write_text(source.read_text().replace("REQ-SVC-01", "REQ-SVC-99"))
    view = Workspace.open(root).results(report(root, [(KEY, "pass")]))
    assert verdicts(view)["REQ-SVC-01"] == "untested"
    assert "REQ-SVC-99" not in verdicts(view)
    assert "1 violation" in text.results(view)


def test_ambiguous_and_missing_identities_are_not_guessed(project: Path) -> None:
    root = project / "service"
    (root / "tests/unit/test_dot.name.py").write_text("def test_same(): pass\n")
    (root / "tests/unit/test_dot").mkdir()
    (root / "tests/unit/test_dot/name.py").write_text("def test_same(): pass\n")
    config = root / "qmstrace.toml"
    config.write_text(config.read_text().replace('"tests/**/test_*.py"', '"tests/**/*.py"'))
    path = report(root, [(KEY, "pass"), ("tests/unit/test_dot.name.py::test_same", "fail")])
    path.write_text(
        path.read_text().replace("</testsuite>", '<testcase name="test_nameless"/></testsuite>')
    )
    view = Workspace.open(root).results(path)
    assert view.matched_cases == 1
    assert len(view.unmatched) == 2
    assert "ambiguous identity" in view.unmatched[1].reason
    assert "missing classname" in view.unmatched[0].reason


@pytest.mark.parametrize(
    "payload",
    [
        b"<bad/>",
        b"<testsuite/>",
        b"not xml",
        b"<!DOCTYPE x><testsuite/>",
        b'<?xml version="1.0" encoding="bogus"?><testsuite/>',
    ],
)
@pytest.mark.verifies("REQ-QMT-10")
def test_unusable_reports_exit_two(project: Path, payload: bytes) -> None:
    root = project / "service"
    (root / "report.xml").write_bytes(payload)
    result = runner.invoke(app, ["-C", str(root), "results", "report.xml"])
    assert result.exit_code == 2, result.output
    assert "Fix:" in result.output and "exit 0" not in result.output


def test_missing_and_zero_match_reports_exit_two(project: Path) -> None:
    root = project / "service"
    result = runner.invoke(app, ["-C", str(root), "results", "absent.xml"])
    assert result.exit_code == 2 and "Cannot read report" in result.output
    report(root, [("tests/elsewhere.py::test_missing", "pass")])
    result = runner.invoke(app, ["-C", str(root), "results", "report.xml"])
    assert result.exit_code == 2 and "no report entries match" in result.output
    assert "test_missing" in result.output and "No requirement verdicts" in result.output


def test_report_path_uses_effective_directory_even_when_ignored(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project / "service"
    subdir = root / "tests"
    report(subdir, [(KEY, "pass")])
    (root / ".gitignore").write_text("report.xml\n")
    # A different report at repo root must not be read after repo discovery.
    (root / "report.xml").write_text("not xml")
    before = runner.invoke(app, ["-C", str(subdir), "results", "report.xml"])
    after = runner.invoke(app, ["results", "report.xml", "-C", str(subdir)])
    monkeypatch.chdir(subdir)
    implicit = runner.invoke(app, ["results", "report.xml"])
    assert before.exit_code == after.exit_code == implicit.exit_code == 0
    assert before.output == after.output == implicit.output
    outside = report(project, [(KEY, "pass")])
    assert runner.invoke(app, ["results", str(outside)]).exit_code == 0


def test_argument_errors_and_internal_fault(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = str(project / "service")
    assert runner.invoke(app, ["-C", root, "results"]).exit_code == 2
    several = runner.invoke(app, ["-C", root, "results", "a", "b"])  # several are accepted
    assert several.exit_code == 2 and "Cannot read report a" in several.output
    assert runner.invoke(app, ["-C", root, "results", "a", "-C", root]).exit_code == 2

    def broken(*args):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(Workspace, "results", broken)
    assert runner.invoke(app, ["-C", root, "results", "a"]).exit_code == 3


def test_assessment_runs_once(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = Workspace.assessment
    calls = 0

    def counted(workspace):
        nonlocal calls
        calls += 1
        return original(workspace)

    monkeypatch.setattr(Workspace, "assessment", counted)
    root = project / "service"
    Workspace.open(root).results(report(root, [(KEY, "pass")]))
    assert calls == 1
