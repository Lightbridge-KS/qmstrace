"""`qmstrace ledger …` — the project side's verbs, pinned byte for byte.

The load-bearing claims, each pinned by a test:

1. Its output is a golden file: the first copy, a second run that changes nothing, a copy
   after the project's rules changed, and a copy from a ledger that lists itself — skipped.
2. `-C` before or after the command gives the same bytes.
3. Run in a product repo it cannot judge and names the ledger; a product verb run in the ledger
   names the product repos and the `ledger` group. `qmstrace ledger` alone prints its verbs.
4. `ledger check` is a golden file too — a clean project in the layout of ADR-0001, the gate
   failing on gaps the product repos leave, `--quiet`, suspects across repos after a change to
   a frozen document, a refusal, and the old layout — and `-C` on either side gives the same
   bytes.
5. `ledger thread` and `ledger impact` walk across every repo, each a golden file: a requirement
   down to the tests of two repos, a module back to its origin, several starts at once — and
   a test's ID given without its repo is refused with the qualified IDs it may mean.

Regenerate a golden after an intended change: `QMSTRACE_REGOLD=1 uv run pytest tests/cli`, then
read the diff before committing it.
"""

import shutil
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


# ── 4. ledger check ────────────────────────────────────────────────────────────────────────


def ledger_check(ledger: Path, *flags: str) -> tuple[int, str]:
    return copy_schema("-C", str(ledger), "ledger", "check", *flags)


def rewrite(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    assert old in content
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def untested_client(split: Path) -> None:
    """The client's test for its own requirement loses its marker."""
    rewrite(
        split / "client" / "tests" / "unit" / "test_api.py",
        '@pytest.mark.verifies("REQ-CLT-01", "DSN-CLT-01")\n',
        "",
    )


@pytest.mark.verifies("REQ-QMT-17")
def test_ledger_check_on_a_project_whose_ledger_holds_the_documents(
    split: Path, golden: Golden
) -> None:
    code, output = ledger_check(split / "ledger")
    assert code == 0
    golden(GOLDEN / "ledger-check-split.txt", output)


@pytest.mark.verifies("REQ-QMT-17")
def test_ledger_check_strict_fails_on_gaps_across_repos(split: Path, golden: Golden) -> None:
    untested_client(split)
    code, output = ledger_check(split / "ledger", "--strict")
    assert code == 1
    golden(GOLDEN / "ledger-check-strict.txt", output)


def test_ledger_check_quiet_keeps_what_it_could_not_verify(split: Path, golden: Golden) -> None:
    untested_client(split)
    code, output = ledger_check(split / "ledger", "--quiet")
    assert code == 0
    golden(GOLDEN / "ledger-check-quiet.txt", output)


@pytest.mark.verifies("REQ-QMT-17")
def test_ledger_check_after_a_change_to_a_frozen_document(split: Path, golden: Golden) -> None:
    ledger = split / "ledger"
    subprocess.run(["git", "tag", "-a", "baseline/requirements/1", "-m", "approved"], cwd=ledger)
    srs = ledger / "docs" / "req" / "service-srs.md"
    rewrite(srs, "with status 401", "with status 403")
    rewrite(srs, "- Verify-by: test\n", "- Verify-by: test\n- Change: CR-001\n")
    code, output = ledger_check(ledger)
    assert code == 0
    golden(GOLDEN / "ledger-check-suspects.txt", output)


@pytest.mark.verifies("REQ-QMT-17")
def test_ledger_check_refuses_a_project_it_cannot_read_whole(split: Path, golden: Golden) -> None:
    copy_schema("-C", str(split / "ledger"), "ledger", "copy-schema", "service")
    rewrite(split / "ledger" / "qmstrace.schema.toml", "verifies nothing.", "verifies nothing yet.")
    shutil.rmtree(split / "client")
    code, output = ledger_check(split / "ledger")
    assert code == 2
    golden(GOLDEN / "ledger-check-refused.txt", output)


def test_ledger_check_on_the_old_layout(project: Path, golden: Golden) -> None:
    code, output = ledger_check(project / "ledger")
    assert code == 0
    golden(GOLDEN / "ledger-check-mini.txt", output)


def test_ledger_check_minus_c_before_or_after_gives_the_same_bytes(split: Path) -> None:
    ledger = str(split / "ledger")
    before = copy_schema("-C", ledger, "ledger", "check")
    after = copy_schema("ledger", "check", "-C", ledger)
    assert before == after and before[0] == 0


# ── 5. ledger thread and ledger impact ─────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-18")
def test_ledger_thread_from_a_requirement_reaches_both_repos_tests(
    split: Path, golden: Golden
) -> None:
    code, output = copy_schema("-C", str(split / "ledger"), "ledger", "thread", "REQ-SVC-01")
    assert code == 0
    golden(GOLDEN / "ledger-thread-requirement.txt", output)


@pytest.mark.verifies("REQ-QMT-18")
def test_ledger_thread_from_a_module_reaches_its_origin(split: Path, golden: Golden) -> None:
    code, output = copy_schema(
        "-C", str(split / "ledger"), "ledger", "thread", "service:src/service/keys.py"
    )
    assert code == 0
    golden(GOLDEN / "ledger-thread-module.txt", output)


@pytest.mark.verifies("REQ-QMT-18")
def test_ledger_impact_of_several_items(split: Path, golden: Golden) -> None:
    ledger = str(split / "ledger")
    code, output = copy_schema("-C", ledger, "ledger", "impact", "REQ-CLT-01", "DSN-SVC-02")
    assert code == 0
    golden(GOLDEN / "ledger-impact-multiple.txt", output)
    again = copy_schema("-C", ledger, "ledger", "impact", "DSN-SVC-02", "REQ-CLT-01", "DSN-SVC-02")
    assert again == (code, output)


@pytest.mark.verifies("REQ-QMT-18")
def test_a_tests_id_without_its_repo_is_shown_the_qualified_ones(split: Path) -> None:
    unqualified = "tests/unit/test_api.py::test_a_call_without_a_key_is_refused"
    code, output = copy_schema("-C", str(split / "ledger"), "ledger", "thread", unqualified)
    assert code == 2
    assert f"client:{unqualified}, service:{unqualified}" in output
    code, output = copy_schema("-C", str(split / "ledger"), "ledger", "impact", "REQ-SVC-09")
    assert code == 2 and "No impact list was produced" in output
