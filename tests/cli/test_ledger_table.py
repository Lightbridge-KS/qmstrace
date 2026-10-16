"""`qmstrace ledger table` — the ledger's tables as versioned JSON (ADR-0005).

The load-bearing claims, each pinned by a test:

1. Each table is a `qmstrace.table/1` document: the project, the schema's digest, each repo's
   commit and whether its tree was clean, not pinned, the counts, every notice — then columns
   and rows. The `cases` project's three tables are goldens.
2. The same inputs give the same bytes, with no path of the machine, whichever side of the
   command `-C` is given on.
3. A repo with uncommitted work is read as it is and said to be unclean.
4. `--out` writes a new file and refuses an existing one; a product repo, and a table qmstrace
   does not emit, are refused.
"""

import itertools
import json
from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.extract.pytest_tests import report_identity

GOLDEN = Path(__file__).parent / "golden"
Golden = Callable[[Path, str], None]
runner = CliRunner()


def run(*words: str) -> tuple[int, str]:
    result = runner.invoke(app, list(words))
    return result.exit_code, result.output


def table_of(project: Path, name: str) -> dict[str, object]:
    code, output = run("-C", str(project / "ledger"), "ledger", "table", name)
    assert code == 0, output
    found = json.loads(output)
    assert isinstance(found, dict)
    return found


# ── 1. the documents ────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-23")
def test_the_cases_matrix(cases: Path, golden: Golden) -> None:
    code, output = run("-C", str(cases / "ledger"), "ledger", "table", "matrix")
    assert code == 0
    golden(GOLDEN / "ledger-table-matrix-cases.json", output)
    matrix = json.loads(output)
    assert matrix["format"] == "qmstrace.table/1" and matrix["pinned"] is False
    assert [(r["requirement"], r["test_case"]) for r in matrix["rows"]] == [
        ("REQ-SVC-01", "TC-SVC-01.1"),
        ("REQ-SVC-01", "TC-SVC-01.2"),
        ("REQ-SVC-02", "TC-SVC-02.1"),
        ("REQ-SVC-02", "TC-SVC-02.2"),
        ("REQ-SVC-02", None),  # a test that verifies with no test case between
    ]


@pytest.mark.verifies("REQ-QMT-23")
def test_the_cases_requirements_register(cases: Path, golden: Golden) -> None:
    code, output = run("-C", str(cases / "ledger"), "ledger", "table", "requirements")
    assert code == 0
    golden(GOLDEN / "ledger-table-requirements-cases.json", output)


@pytest.mark.verifies("REQ-QMT-23")
def test_the_cases_coverage_summary(cases: Path, golden: Golden) -> None:
    code, output = run("-C", str(cases / "ledger"), "ledger", "table", "coverage")
    assert code == 0
    golden(GOLDEN / "ledger-table-coverage-cases.json", output)


@pytest.mark.verifies("REQ-QMT-23")
def test_every_project_notice_reaches_every_table(cases: Path) -> None:
    for name in ("matrix", "requirements", "coverage"):
        notices = table_of(cases, name)["notices"]
        assert isinstance(notices, list)
        assert any("remote-tag completeness NOT VERIFIED" in n for n in notices), name


@pytest.mark.verifies("REQ-QMT-23")
def test_the_matrix_carries_the_fields_the_schema_lists(cases: Path) -> None:
    schema = cases / "ledger" / "qmstrace.schema.toml"
    schema.write_text(
        schema.read_text(encoding="utf-8") + '\n[tables.matrix]\nfields = ["Category"]\n',
        encoding="utf-8",
    )
    matrix = table_of(cases, "matrix")
    columns = [c["name"] for c in matrix["columns"]]  # type: ignore[union-attr]
    assert columns[:4] == ["origin_clause", "requirement", "title", "Category"]
    assert matrix["rows"][0]["Category"] == "security"  # type: ignore[index]


# ── 2. the same inputs, the same bytes ─────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-23", "REQ-QMT-15")
def test_the_same_inputs_give_the_same_bytes_with_no_machine_path(cases: Path) -> None:
    ledger = str(cases / "ledger")
    first = run("-C", ledger, "ledger", "table", "matrix")
    again = run("ledger", "table", "matrix", "-C", ledger)
    assert first == again and first[0] == 0
    assert str(cases) not in first[1] and str(Path.home()) not in first[1]


# ── 3. what was read ────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-23")
def test_a_repo_with_uncommitted_work_is_said_to_be_unclean(cases: Path) -> None:
    (cases / "service" / "notes.txt").write_text("not committed\n", encoding="utf-8")
    read = {r["repo"]: r for r in table_of(cases, "matrix")["read"]}  # type: ignore[union-attr]
    assert (read["service"]["clean"], read["agent"]["clean"]) == (False, True)
    assert len(read["service"]["commit"]) == 40


# ── 4. writing, and what is refused ────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-23")
def test_out_writes_a_new_file_and_refuses_an_existing_one(cases: Path, golden: Golden) -> None:
    ledger = cases / "ledger"
    # beside the repos, so writing it leaves every repo clean
    code, output = run("-C", str(ledger), "ledger", "table", "matrix", "--out", "../matrix.json")
    assert code == 0
    golden(GOLDEN / "ledger-table-out.txt", output)
    written = (cases / "matrix.json").read_text(encoding="utf-8")
    assert written == run("-C", str(ledger), "ledger", "table", "matrix")[1]
    code, output = run("-C", str(ledger), "ledger", "table", "matrix", "--out", "../matrix.json")
    assert code == 2


@pytest.mark.verifies("REQ-QMT-23")
def test_a_product_repo_and_an_unknown_table_are_refused(cases: Path) -> None:
    assert run("-C", str(cases / "service"), "ledger", "table", "matrix")[0] == 2
    assert run("-C", str(cases / "ledger"), "ledger", "table", "trace")[0] == 2


# ── 5. verdicts from reports (#49b) ────────────────────────────────────────────────────────

TRX = Path(__file__).parents[1] / "fixtures" / "trx" / "cases-agent-full.trx"
SERVICE_TESTS = [
    ("tests/unit/test_api.py::test_a_call_without_a_key_is_refused", "pass"),
    ("tests/unit/test_api.py::test_a_call_with_a_wrong_key_is_refused", "pass"),
    ("tests/unit/test_api.py::test_the_key_check_runs_before_any_handler", "fail"),
    ("tests/integration/test_store.py::test_a_restart_keeps_every_field", "pass"),
    ("tests/integration/test_store.py::test_a_record_survives_a_restart", "pass"),
]


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


def reports(cases: Path) -> list[str]:
    (cases / "agent" / "TestResults").mkdir()
    (cases / "agent" / "TestResults" / "unit.trx").write_bytes(TRX.read_bytes())
    junit(cases / "service" / "report.xml", SERVICE_TESTS)
    return [
        "--report",
        "agent=../agent/TestResults/unit.trx",
        "--report",
        "service=../service/report.xml",
    ]


@pytest.mark.verifies("REQ-QMT-23")
def test_the_cases_matrix_with_verdicts(cases: Path, golden: Golden) -> None:
    given = reports(cases)
    code, output = run("-C", str(cases / "ledger"), "ledger", "table", "matrix", *given)
    assert code == 0, output
    golden(GOLDEN / "ledger-table-matrix-reports-cases.json", output)
    matrix = json.loads(output)
    assert [(r["repo"], r["label"]) for r in matrix["reports"]] == [
        ("agent", "TestResults/unit.trx"),
        ("service", "report.xml"),
    ]
    by_case = {r["test_case"]: r for r in matrix["rows"]}
    assert by_case["TC-SVC-01.2"]["verdict_unit"]["verdict"] == "fail"  # the service's run
    assert by_case["TC-SVC-02.1"]["verdict_integration"]["verdict"] == "pass"
    assert by_case["TC-SVC-02.2"]["verdict"] == {"verdict": "untested", "reports": []}


@pytest.mark.verifies("REQ-QMT-23", "REQ-QMT-15")
def test_any_order_of_the_reports_gives_the_same_bytes(cases: Path) -> None:
    given = reports(cases)
    pairs = [given[i : i + 2] for i in range(0, len(given), 2)]
    outputs = {
        run("-C", str(cases / "ledger"), "ledger", "table", "matrix", *itertools.chain(*order))
        for order in itertools.permutations(pairs)
    }
    assert len(outputs) == 1 and next(iter(outputs))[0] == 0


@pytest.mark.verifies("REQ-QMT-23", "REQ-QMT-15")
def test_a_report_outside_every_repo_shows_its_file_name_alone(cases: Path, tmp_path: Path) -> None:
    sentinel = tmp_path / "SENTINEL-elsewhere" / "service-run.xml"
    junit(sentinel, SERVICE_TESTS)
    code, output = run(
        "-C", str(cases / "ledger"), "ledger", "table", "matrix", "--report", f"service={sentinel}"
    )
    assert code == 0, output
    assert [r["label"] for r in json.loads(output)["reports"]] == ["service-run.xml"]
    assert "SENTINEL" not in output and str(tmp_path) not in output
    assert str(Path.home()) not in output


@pytest.mark.verifies("REQ-QMT-23")
def test_reports_that_match_nothing_and_bad_reports_are_refused(cases: Path) -> None:
    given = reports(cases)
    ledger = str(cases / "ledger")
    wrong = ["--report", "agent=../service/report.xml"]  # the service's run, named as the agent's
    code, output = run("-C", ledger, "ledger", "table", "matrix", *wrong)
    assert code == 2 and "matches an automated test of the repo it names" in output
    assert run("-C", ledger, "ledger", "table", "matrix", "--report", "elsewhere=x.xml")[0] == 2
    assert run("-C", ledger, "ledger", "table", "matrix", "--report", "report.xml")[0] == 2
    assert run("-C", ledger, "ledger", "table", "requirements", *given)[0] == 2
