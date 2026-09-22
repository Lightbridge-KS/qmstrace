"""The baseline contract as printed, including informational versus gate exits."""

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
runner = CliRunner()


@pytest.fixture
def baseline(project, embed):
    root = project / "service"
    file = root / "qmstrace.toml"
    file.write_text(embed(file.read_text(), (project / "ledger/qmstrace.schema.toml").read_text()))
    for args in [
        ("add", "qmstrace.toml"),
        ("commit", "-qm", "embed schema"),
        ("tag", "-a", "baseline/service/requirements/1", "-m", "Approved"),
    ]:
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    (project / "ledger/change-requests").mkdir()
    return root


@pytest.mark.parametrize(
    "case,command,exit_code",
    [
        ("frozen", ["status"], 0),
        ("unauthorized", ["check"], 1),
        ("authorized", ["check"], 0),
        ("unavailable", ["check", "--quiet"], 0),
        ("withdrawn", ["status"], 0),
        ("shallow", ["status"], 2),
    ],
)
def test_baseline_goldens(baseline, golden, case, command, exit_code):
    if case not in {"frozen", "shallow"}:
        srs = baseline / "docs/req/service-srs.md"
        extra = " revised\n"
        if case in {"authorized", "unavailable", "withdrawn"}:
            extra += "- Change: CR-001\n"
        if case == "withdrawn":
            extra += "- Status: withdrawn\n"
        srs.write_text(
            srs.read_text().replace(
                "### REQ-SVC-01 — A call carries a key\n",
                "### REQ-SVC-01 — A call carries a key" + extra,
            )
        )
        register = baseline.parent / "ledger/change-requests"
        if case == "unavailable":
            register.rmdir()
        else:
            (register / "CR-001.md").write_text(
                "# CR-001 — Revise key policy\n- State: accepted\n- Impacts: REQ-SVC-01\n"
            )
    if case == "shallow":
        # Git's real shallow state; no network or clone is needed for this CLI fixture.
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=baseline)
        (baseline / ".git/shallow").write_bytes(head)
    args = ["-C", str(baseline), *command]
    result = runner.invoke(app, args)
    assert result.exit_code == exit_code, result.output
    assert result.output == runner.invoke(app, args).output
    assert result.output == runner.invoke(app, [*command, "-C", str(baseline)]).output
    golden(GOLDEN / f"{command[0]}-baseline-{case}.txt", result.output)
