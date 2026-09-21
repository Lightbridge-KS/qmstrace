"""`qmstrace status` — the first command an agent runs in a product repo, pinned byte for byte.

The load-bearing claims, each pinned by a test:

1. Its output is a golden file: with everything beside the repo, and as a pipeline sees it.
2. Two runs give the same bytes, and no absolute path of this machine leaks into them.
3. The root is found from a folder inside the repo, and `-C` runs it elsewhere.
4. `status` is not a check: violations are counted by code, and it still exits 0.
5. In a ledger repo it cannot judge — exit 2, with where to run instead.

Regenerate a golden after an intended change: `QMSTRACE_REGOLD=1 uv run pytest tests/cli`, then
read the diff before committing it.
"""

import os
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
runner = CliRunner()


def status(root: Path) -> tuple[int, str]:
    result = runner.invoke(app, ["-C", str(root), "status"])
    return result.exit_code, result.output


def matches_golden(name: str, output: str) -> None:
    golden = GOLDEN / f"{name}.txt"
    if os.environ.get("QMSTRACE_REGOLD"):
        golden.parent.mkdir(exist_ok=True)
        golden.write_text(output, encoding="utf-8")
    assert output == golden.read_text(encoding="utf-8")


# ── 1. goldens ─────────────────────────────────────────────────────────────────────────────


def test_status_with_everything_beside_the_repo(project: Path) -> None:
    code, output = status(project / "service")
    assert code == 0
    matches_golden("status-service", output)


def test_status_as_a_pipeline_sees_it(alone: Callable[[str], Path]) -> None:
    code, output = status(alone("client"))
    assert code == 0
    matches_golden("status-client-in-a-pipeline", output)


def test_status_in_a_repo_on_its_own(project: Path) -> None:
    code, output = status(project / "solo")
    assert code == 0
    matches_golden("status-solo", output)


def test_what_cannot_be_found_or_read_is_said_in_the_header(
    project: Path, alone: Callable[[str], Path]
) -> None:
    checkout = alone("client")
    config = checkout / "qmstrace.toml"
    config.write_text(config.read_text().replace('ledger  = "../ledger"\n', ""), encoding="utf-8")
    output = status(checkout)[1]
    assert "external AGR-*: NOT VERIFIED — no ledger beside this repo" in output
    assert "siblings: NOT LOCATED — no ledger beside this repo" in output

    (project / "service" / "qmstrace.toml").write_text("version = = 1\n", encoding="utf-8")
    output = status(project / "client")[1]
    assert "sibling service: at ../service, its configuration could not be read" in output


# ── 2. determinism ─────────────────────────────────────────────────────────────────────────


def test_two_runs_give_the_same_bytes_and_no_machine_path(project: Path) -> None:
    first, second = status(project / "client")[1], status(project / "client")[1]
    assert first == second
    assert str(project) not in first
    assert "/private/" not in first and "/var/" not in first


# ── 3. where it runs ───────────────────────────────────────────────────────────────────────


def test_the_root_is_found_from_inside_the_repo(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project / "service" / "src")
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert result.output == status(project / "service")[1]


# ── 4. not a check ─────────────────────────────────────────────────────────────────────────


def test_violations_are_counted_by_code_and_status_still_exits_0(project: Path) -> None:
    notes = project / "service" / "docs" / "notes.md"
    notes.write_text("### REQ-SVC-05 — Stray\n\n### REQ-SVC-06 — Stray\n", encoding="utf-8")
    code, output = status(project / "service")
    assert code == 0
    assert output.rstrip().endswith("2 violations (V07 \N{MULTIPLICATION SIGN}2)")


# ── 5. the wrong kind of repo ──────────────────────────────────────────────────────────────


def test_in_a_ledger_repo_it_cannot_judge_and_says_where_to_run(project: Path) -> None:
    code, output = status(project / "ledger")
    assert code == 2
    assert "ledger repo" in output and "-C <path>" in output
