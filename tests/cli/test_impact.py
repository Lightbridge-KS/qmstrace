"""Impact is a union of walks, a candidate list, and explicit limits — never a partial request."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app
from qmstrace.core.errors import CouldNotJudge
from qmstrace.render import text
from qmstrace.workspace import Workspace

GOLDEN = Path(__file__).parent / "golden"
runner = CliRunner()
STARTS = ("REQ-SVC-01", "REQ-SVC-02")


def impact(root: Path, *ids: str) -> tuple[int, str]:
    result = runner.invoke(app, ["-C", str(root), "impact", *ids])
    return result.exit_code, result.output


def candidate(output: str) -> set[str]:
    return set(
        next(
            line.removeprefix("Impacts: ").split(", ")
            for line in output.splitlines()
            if line.startswith("Impacts: ")
        )
    )


@pytest.mark.parametrize(
    ("name", "repo", "starts"),
    [
        ("impact-multiple", "service", STARTS),
        ("impact-sibling", "client", ("REQ-SVC-01",)),
    ],
)
def test_golden(
    project: Path,
    golden: Callable[[Path, str], None],
    name: str,
    repo: str,
    starts: tuple[str, ...],
) -> None:
    code, output = impact(project / repo, *starts)
    assert code == 0
    golden(GOLDEN / f"{name}.txt", output)


def test_pipeline(alone: Callable[[str], Path], golden: Callable[[Path, str], None]) -> None:
    code, output = impact(alone("client"), "REQ-SVC-01")
    assert code == 0
    assert "not verified here" in output and "unknown type, omitted" in output
    assert "Impacts:" not in output
    golden(GOLDEN / "impact-in-a-pipeline.txt", output)


def test_union_and_configured_candidate(project: Path) -> None:
    code, output = impact(project / "service", *STARTS)
    assert code == 0
    assert candidate(output) == {*STARTS, "DSN-SVC-01", "DSN-SVC-02"}
    assert "downstream: 2 design elements, 2 components, 4 test cases" in output
    assert "upstream origins: 3" in output
    assert output.count("tests/integration/test_store.py::test_a_record_survives_a_restart ·") == 1
    assert "not a claim of edits or frozen state" in output


def test_repeated_and_reordered_starts_are_byte_identical(project: Path) -> None:
    expected = impact(project / "service", *STARTS)
    assert expected == impact(project / "service", *STARTS)
    assert expected == impact(project / "service", STARTS[1], STARTS[0], STARTS[1])


def test_start_reached_again_and_cycle_are_not_redisplayed(project: Path) -> None:
    design = project / "service/docs/design/service-design.md"
    design.write_text(
        design.read_text().replace(
            "Satisfies: REQ-SVC-01", "Satisfies: REQ-SVC-01\nAssumes: DSN-SVC-02"
        )
    )
    code, output = impact(project / "service", "REQ-SVC-01", "DSN-SVC-01")
    assert code == 0
    assert output.count("DSN-SVC-01 — Key check") == 1
    assert output.count("DSN-SVC-02 — Record store") == 1
    assert candidate(output) == {"REQ-SVC-01", "DSN-SVC-01", "DSN-SVC-02"}


def test_assumptions_propagate_forward_but_do_not_add_origins(project: Path) -> None:
    code, output = impact(project / "service", "REQ-SVC-01")
    assert code == 0 and "DSN-SVC-02 — Record store" in output
    assert "src/service/store.py" in output
    assert "assumes it — counts toward no coverage" in output
    assert "AGR-1" in output and "AGR-2" not in output and "AGR-3" not in output
    code, output = impact(project / "service", "DSN-SVC-02")
    assert code == 0
    assert "AGR-2" in output and "AGR-3" in output and "AGR-1" not in output


@pytest.mark.parametrize("command", ["impact", "thread"])
def test_converging_assumption_cannot_hide_ordinary_ancestry(project: Path, command: str) -> None:
    design = project / "service/docs/design/service-design.md"
    design.write_text(
        design.read_text().replace("Assumes: DSN-SVC-01", "Assumes: REQ-SVC-01")
        + "\n## DSN-SVC-03 — Another design\nSatisfies: REQ-SVC-01\n"
    )
    tests = project / "service/tests/unit/test_join.py"
    tests.write_text(
        'import pytest\n@pytest.mark.verifies("DSN-SVC-02", "DSN-SVC-03")\ndef test_join(): pass\n'
    )
    result = runner.invoke(
        app, ["-C", str(project / "service"), command, "tests/unit/test_join.py::test_join"]
    )
    assert result.exit_code == 0
    assert "AGR-1" in result.output


def test_origin_start_and_no_dependants(project: Path) -> None:
    code, output = impact(project / "service", "AGR-1")
    assert code == 0 and "REQ-SVC-01 — A call carries a key" in output
    assert "AGR-1" not in candidate(output)
    code, output = impact(project / "service", "REQ-SVC-03")
    assert code == 0 and "nothing here hangs off" in output
    assert candidate(output) == {"REQ-SVC-03"}


@pytest.mark.parametrize("covers", [(), ("requirement",), ("component", "test_case")])
def test_candidate_types_are_configuration(project: Path, covers: tuple[str, ...]) -> None:
    assessment = Workspace.open(project / "service").assessment()
    baseline = next(iter(assessment.config.baselines.values()))
    config = replace(
        assessment.config, baselines={"chosen": replace(baseline, covers=covers)} if covers else {}
    )
    output = text.impact(replace(assessment, config=config), STARTS)
    if covers:
        expected = {
            i.id for i in assessment.graph.items() if i.type in covers and i.id != "REQ-SVC-03"
        }
        assert candidate(output) == expected
    else:
        assert "no baseline item types are configured" in output and "Impacts:" not in output


def test_no_reached_item_has_a_covered_type(project: Path) -> None:
    code, output = impact(project / "service", "src/service/keys.py")
    assert code == 0
    assert "no items with a known type covered by a baseline" in output
    assert "Impacts:" not in output


def test_origins_are_configured_not_hard_coded(project: Path) -> None:
    schema = project / "ledger/qmstrace.schema.toml"
    schema.write_text(
        schema.read_text().replace("origin_clause", "customer_need").replace("AGR-", "NEED-")
    )
    for file in [project / "ledger/agreement.md", project / "service/docs/req/service-srs.md"]:
        file.write_text(file.read_text().replace("AGR-", "NEED-"))
    code, output = impact(project / "service", *STARTS)
    assert code == 0
    assert "NEED-1 · customer need, in the agreement" in output
    assert "upstream origins: 3" in output


def test_unknown_starts_reject_the_whole_request(project: Path) -> None:
    code, output = impact(project / "service", "REQ-SVC-01", "REQ-SVC-99", "REQ-SVC-98")
    assert code == 2
    assert "REQ-SVC-98 is not an item this run can see" in output
    assert "REQ-SVC-99 is not an item this run can see" in output
    assert "the closest here:" in output
    assert "No impact list was produced" in output
    assert "starting items:" not in output and "Impacts:" not in output
    assert "reservation does not establish its type or links" in output


def test_unseen_sibling_reports_source_limits(alone: Callable[[str], Path]) -> None:
    code, output = impact(alone("client"), "REQ-SVC-02")
    assert code == 2
    assert "sibling service could not be read" in output and "Impacts:" not in output


def test_uncited_sibling_and_clause_are_visible(project: Path) -> None:
    code, output = impact(project / "client", "REQ-SVC-02")
    assert code == 0 and "nothing here hangs off" in output
    assert "not pinned" in output and "downstream links there are not scanned" in output
    assert candidate(output) == {"REQ-SVC-02"}
    assert impact(project / "client", "AGR-2")[0] == 0


def test_violations_and_notices_remain_visible(project: Path) -> None:
    srs = project / "service/docs/req/service-srs.md"
    srs.write_text(srs.read_text().replace("Origin: AGR-1", "Origin: AGR-99"))
    code, output = impact(project / "service", "REQ-SVC-01")
    assert code == 0 and "1 violation" in output
    assert "links they refuse are not shown" in output
    assert "baselines:" in output and "remote-tag completeness NOT VERIFIED" in output


def test_directory_and_missing_arguments(project: Path) -> None:
    root = str(project / "service")
    expected = impact(Path(root), *STARTS)
    after = runner.invoke(app, ["impact", *STARTS, "-C", root])
    assert (after.exit_code, after.output) == expected
    assert runner.invoke(app, ["-C", root, "impact"]).exit_code == 2
    assert runner.invoke(app, ["-C", root, "impact", *STARTS, "-C", root]).exit_code == 2


def test_workspace_scans_once_and_validates_empty_input(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    original = Workspace.assessment

    def counted(workspace: Workspace):
        nonlocal calls
        calls += 1
        return original(workspace)

    monkeypatch.setattr(Workspace, "assessment", counted)
    workspace = Workspace.open(project / "service")
    with pytest.raises(CouldNotJudge, match="No starting IDs"):
        workspace.impact([])
    workspace.impact(iter(STARTS))
    assert calls == 1
