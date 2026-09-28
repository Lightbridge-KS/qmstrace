"""`qmstrace ledger copy-schema` — the project side's first verb, pinned byte for byte.

The load-bearing claims, each pinned by a test:

1. Its output is a golden file: the first copy, a second run that changes nothing, a copy
   after the project's rules changed, and a copy from a ledger that lists itself — skipped.
2. `-C` before or after the command gives the same bytes.
3. Run in a product repo it cannot judge and names the ledger; a product verb run in the ledger
   names the product repos and the `ledger` group. `qmstrace ledger` alone prints its verbs.

Regenerate a golden after an intended change: `QMSTRACE_REGOLD=1 uv run pytest tests/cli`, then
read the diff before committing it.
"""

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
Golden = Callable[[Path, str], None]
runner = CliRunner()


def copy_schema(*words: str) -> tuple[int, str]:
    result = runner.invoke(app, list(words))
    return result.exit_code, result.output


# ── 1. goldens ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-13")
def test_the_first_copy(project: Path, golden: Golden) -> None:
    code, output = copy_schema("-C", str(project / "ledger"), "ledger", "copy-schema")
    assert code == 0
    golden(GOLDEN / "ledger-copy-schema-first.txt", output)


@pytest.mark.verifies("REQ-QMT-13")
def test_a_second_run_changes_nothing(project: Path, golden: Golden) -> None:
    ledger = str(project / "ledger")
    copy_schema("-C", ledger, "ledger", "copy-schema")
    before = (project / "service" / "qmstrace.toml").read_bytes()
    code, output = copy_schema("-C", ledger, "ledger", "copy-schema")
    assert code == 0
    assert (project / "service" / "qmstrace.toml").read_bytes() == before
    golden(GOLDEN / "ledger-copy-schema-again.txt", output)


@pytest.mark.verifies("REQ-QMT-13")
def test_a_copy_from_a_ledger_that_lists_itself(split: Path, golden: Golden) -> None:
    code, output = copy_schema("-C", str(split / "ledger"), "ledger", "copy-schema")
    assert code == 0
    golden(GOLDEN / "ledger-copy-schema-split.txt", output)


def test_a_copy_after_the_rules_changed(project: Path, golden: Golden) -> None:
    ledger = project / "ledger"
    copy_schema("-C", str(ledger), "ledger", "copy-schema")
    schema = ledger / "qmstrace.schema.toml"
    schema.write_text(
        schema.read_text().replace("no test verifies it yet.", "no test verifies this yet."),
        encoding="utf-8",
    )
    code, output = copy_schema("-C", str(ledger), "ledger", "copy-schema", "service")
    assert code == 0
    golden(GOLDEN / "ledger-copy-schema-refresh.txt", output)


# ── 2. -C on either side ───────────────────────────────────────────────────────────────────


def test_minus_c_before_or_after_gives_the_same_bytes(project: Path) -> None:
    ledger = str(project / "ledger")
    before = copy_schema("-C", ledger, "ledger", "copy-schema")
    for repo in ("service", "client"):  # back to reading the schema by path
        subprocess.run(["git", "checkout", "-q", "--", "qmstrace.toml"], cwd=project / repo)
    after = copy_schema("ledger", "copy-schema", "-C", ledger)
    assert before == after and before[0] == 0


# ── 3. the wrong kind of repo ──────────────────────────────────────────────────────────────


def test_run_in_a_product_repo_it_names_the_ledger(project: Path) -> None:
    code, output = copy_schema("-C", str(project / "service"), "ledger", "copy-schema")
    assert code == 2
    assert "is a product repo — its ledger is at ../ledger" in output
    assert (project / "service" / "qmstrace.toml").read_text().count("qmstrace:begin") == 0


def test_a_product_verb_in_the_ledger_names_the_ledger_group(project: Path) -> None:
    code, output = copy_schema("-C", str(project / "ledger"), "status")
    assert code == 2
    assert "the ledger's own verbs are under qmstrace ledger" in output


def test_the_group_alone_lists_its_verbs() -> None:
    code, output = copy_schema("ledger")
    assert code == 2
    assert "copy-schema" in output
