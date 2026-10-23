"""Configuration and authoring failures must be visible before a baseline is cut.

Implements: DSN-QMT-03, DSN-QMT-07
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
runner = CliRunner()


def _v17_solo(root: Path) -> Path:
    solo = root / "solo"
    config = solo / "qmstrace.toml"
    config.write_text(config.read_text().replace(r"'^REQ-APP-\d{2}$'", r"'^REQ-(APP-)?\d{2}$'"))
    srs = solo / "docs/req/app-srs.md"
    assert srs.exists()
    srs.write_text(srs.read_text() + "\n### REQ-03 — Missing owner\n- Origin: BRF-1\n")
    return solo


@pytest.mark.verifies("DSN-QMT-03", "REQ-QMT-01")
def test_issue_25_is_a_whole_configuration_refusal(project: Path) -> None:
    service = project / "service"
    config = service / "qmstrace.toml"
    config.write_text(
        config.read_text()
        .replace(
            r"'^REQ-SVC-\d{2}$'",
            r"'^(REQ|NFR)-SVC-\d{2}$'",
        )
        .replace('files      = ["docs/req', 'id_prefix = "REQ-"\nfiles      = ["docs/req', 1)
    )
    srs = service / "docs/req/service-srs.md"
    srs.write_text(srs.read_text() + "\n### NFR-SVC-3 — A malformed second family\n")
    for args in (["-C", str(service), "check"], ["check", "-C", str(service)]):
        result = runner.invoke(app, args)
        assert result.exit_code == 2
        assert "no provable common literal start" in result.output
        assert "read:" not in result.output and "result:" not in result.output


@pytest.mark.verifies("DSN-QMT-03", "REQ-QMT-02")
def test_a_proven_grouped_family_still_reports_v02(project: Path) -> None:
    service = project / "service"
    config = service / "qmstrace.toml"
    config.write_text(config.read_text().replace(r"'^REQ-SVC-\d{2}$'", r"'^(REQ|RQ)-SVC-\d{2}$'"))
    srs = service / "docs/req/service-srs.md"
    srs.write_text(srs.read_text() + "\n### RQ-SVC-3 — Short\n")
    result = runner.invoke(app, ["-C", str(service), "check", "--quiet"])
    assert result.exit_code == 1
    assert "V02" in result.output and "RQ-SVC-3" in result.output


@pytest.mark.verifies("DSN-QMT-07", "REQ-QMT-03")
def test_v17_before_a_tag_in_status_check_and_quiet(project: Path, golden) -> None:
    solo = _v17_solo(project)
    status = runner.invoke(app, ["-C", str(solo), "status"])
    assert status.exit_code == 0
    assert "V17 \u00d71" in status.output
    golden(GOLDEN / "status-authoring-v17.txt", status.output)
    for args in (["-C", str(solo), "check", "--quiet"], ["check", "--quiet", "-C", str(solo)]):
        result = runner.invoke(app, args)
        assert result.exit_code == 1
        assert "V17" in result.output and "REQ-03" in result.output
        golden(GOLDEN / "check-authoring-v17.txt", result.output)


@pytest.mark.verifies("DSN-QMT-07", "REQ-QMT-03")
def test_v17_is_in_the_project_check(project: Path, golden) -> None:
    service = project / "service"
    config = service / "qmstrace.toml"
    config.write_text(config.read_text().replace(r"'^REQ-SVC-\d{2}$'", r"'^REQ-(SVC-)?\d{2}$'"))
    srs = service / "docs/req/service-srs.md"
    srs.write_text(
        srs.read_text() + "\n### REQ-04 — Missing owner\n- Category: security\n- Origin: AGR-1\n"
        "- Verify-by: inspection\n"
    )
    ledger = project / "ledger"
    result = runner.invoke(app, ["-C", str(ledger), "ledger", "check", "--quiet"])
    assert result.exit_code == 1
    assert "V17" in result.output and "REQ-04" in result.output
    golden(GOLDEN / "ledger-check-authoring-v17.txt", result.output)
    assert (
        runner.invoke(app, ["ledger", "check", "--quiet", "-C", str(ledger)]).output
        == result.output
    )


def test_uncovered_type_does_not_get_v17(project: Path) -> None:
    solo = project / "solo"
    config = solo / "qmstrace.toml"
    config.write_text(config.read_text().replace('covers  = ["requirement"]', "covers  = []"))
    config.write_text(config.read_text().replace(r"'^REQ-APP-\d{2}$'", r"'^REQ-(APP-)?\d{2}$'"))
    srs = solo / "docs/req/app-srs.md"
    srs.write_text(srs.read_text() + "\n### REQ-03 — Missing owner\n- Origin: BRF-1\n")
    result = runner.invoke(app, ["-C", str(solo), "check", "--quiet"])
    assert result.exit_code == 0
    assert "REQ-03" in result.output
    assert "V17" not in result.output
