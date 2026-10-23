"""`qmstrace status` — the first command an agent runs in a product repo, pinned byte for byte.

The load-bearing claims, each pinned by a test:

1. Its output is a golden file: with everything beside the repo, as a pipeline sees it, and in
   a product repo whose documents are in the ledger (ADR-0001).
2. Two runs give the same bytes, and no absolute path of this machine leaks into them.
3. The root is found from a folder inside the repo, and `-C` runs it elsewhere — given before the
   command, as with `git -C`, or after it; given on both sides it is a usage error.
4. `status` is not a check: violations are counted by code, and it still exits 0.
5. In a ledger repo it cannot judge — exit 2, with where to run instead.

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


def status(root: Path) -> tuple[int, str]:
    result = runner.invoke(app, ["-C", str(root), "status"])
    return result.exit_code, result.output


# ── 1. goldens ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-05")
def test_status_with_everything_beside_the_repo(project: Path, golden: Golden) -> None:
    code, output = status(project / "service")
    assert code == 0
    golden(GOLDEN / "status-service.txt", output)


@pytest.mark.verifies("REQ-QMT-05")
def test_demonstration_is_listed_apart_in_status(project: Path, golden: Golden) -> None:
    schema = project / "ledger/qmstrace.schema.toml"
    schema.write_text(
        schema.read_text().replace(
            '"test", "inspection", "analysis"', '"test", "inspection", "analysis", "demonstration"'
        )
    )
    root = project / "service"
    srs = root / "docs/req/service-srs.md"
    srs.write_text(srs.read_text().replace("Verify-by: inspection", "Verify-by: demonstration"))
    source = root / "tests/unit/test_keys.py"
    source.write_text(source.read_text().replace('"REQ-SVC-01"', '"REQ-SVC-03"'))
    code, output = status(root)
    assert code == 0
    assert "Verify-by: demonstration" in output
    golden(GOLDEN / "status-demonstration.txt", output)


@pytest.mark.parametrize("method", [None, "invalid"])
def test_missing_or_invalid_method_is_apart_with_v05(project: Path, method: str | None) -> None:
    root = project / "service"
    srs = root / "docs/req/service-srs.md"
    replacement = "" if method is None else f"- Verify-by: {method}\n"
    srs.write_text(srs.read_text().replace("- Verify-by: test\n", replacement, 1))
    code, output = status(root)
    assert code == 0
    assert f"Verify-by: {method or 'unspecified'}" in output
    assert "1 violation (V05 \N{MULTIPLICATION SIGN}1)" in output
    check = runner.invoke(app, ["-C", str(root), "check"])
    assert check.exit_code == 1
    assert "V05" in check.output


def test_status_of_a_product_repo_whose_documents_are_in_the_ledger(
    split: Path, golden: Golden
) -> None:
    code, output = status(split / "service")
    assert code == 0
    golden(GOLDEN / "status-split-service.txt", output)


def test_status_as_a_pipeline_sees_it(alone: Callable[[str], Path], golden: Golden) -> None:
    code, output = status(alone("client"))
    assert code == 0
    golden(GOLDEN / "status-client-in-a-pipeline.txt", output)


def test_status_in_a_repo_on_its_own(project: Path, golden: Golden) -> None:
    code, output = status(project / "solo")
    assert code == 0
    golden(GOLDEN / "status-solo.txt", output)


def test_status_of_docs_written_like_an_architecture_guide(project: Path, golden: Golden) -> None:
    code, output = status(project / "rich")
    assert code == 0
    golden(GOLDEN / "status-rich.txt", output)


@pytest.mark.verifies("REQ-QMT-05")
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


@pytest.mark.verifies("DSN-QMT-12", "REQ-QMT-15")
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


def test_c_after_the_command_is_the_same_as_before_it(project: Path) -> None:
    after = runner.invoke(app, ["status", "-C", str(project / "client")])
    assert after.exit_code == 0
    assert after.output == status(project / "client")[1]


def test_c_on_both_sides_is_a_usage_error(project: Path) -> None:
    result = runner.invoke(
        app, ["-C", str(project / "client"), "status", "-C", str(project / "service")]
    )
    assert result.exit_code == 2
    assert "given twice" in result.output and "give it once" in result.output


# ── 4. not a check ─────────────────────────────────────────────────────────────────────────


def test_violations_are_counted_by_code_and_status_still_exits_0(project: Path) -> None:
    notes = project / "service" / "docs" / "notes.md"
    notes.write_text("### REQ-SVC-05 — Stray\n\n### REQ-SVC-06 — Stray\n", encoding="utf-8")
    code, output = status(project / "service")
    assert code == 0
    last = output.rstrip().splitlines()[-1]
    assert last.startswith("2 violations (V07 \N{MULTIPLICATION SIGN}2) · 1 gap")
    assert last.endswith("qmstrace check lists them")


# ── 5. the wrong kind of repo ──────────────────────────────────────────────────────────────


def test_in_a_ledger_repo_it_cannot_judge_and_says_where_to_run(project: Path) -> None:
    code, output = status(project / "ledger")
    assert code == 2
    assert "ledger repo" in output and "-C <path>" in output
