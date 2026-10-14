"""`qmstrace check` — every violation and gap, each with its next move; the gate with --strict.

The load-bearing claims, each pinned by a test:

1. Its output is a golden file: a clean repo; a repo under the gate; a repo with one of every
   violation code and several gaps — reading that file whole is the wording review; a repo in a
   pipeline, quiet.
2. Exit codes: 1 on any violation; under --strict also on any gap; else 0 — gaps are the work
   not done yet while authoring.
3. What this run could not verify survives --quiet, in the notices and in the result line, and
   the result line names the gate.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
Golden = Callable[[Path, str], None]
runner = CliRunner()


def check(root: Path, *flags: str) -> tuple[int, str]:
    result = runner.invoke(app, ["-C", str(root), "check", *flags])
    return result.exit_code, result.output


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, (path.name, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def broken(service: Path) -> Path:
    """The service repo with one of every violation code, and the gaps they leave behind."""
    srs, design = service / "docs/req/service-srs.md", service / "docs/design/service-design.md"
    edit(srs, "- Category: security\n", "")  # V05
    edit(srs, "- Origin: AGR-2, AGR-3", "- Origin: AGR-2, AGR-9")  # V09
    edit(
        srs, "- Origin: AGR-3\n- Verify-by: inspection", "- Origin: TBD\n- Verify-by: inspection"
    )  # V14
    edit(srs, "## Records\n", "## Records\n\n### REQ-SVC-7 — A short number\n")  # V02
    write(service / "docs/req/copy-srs.md", "### REQ-SVC-01 — Copied\nStatement.\n")  # V01
    edit(design, "Satisfies: REQ-SVC-02\n", "Satisfies: REQ-SVC-09\n")  # V03
    write(service / "docs/notes.md", "# Notes\n\n### REQ-SVC-05 — Stray\n")  # V07
    write(service / "tests/test_top.py", "def test_at_the_top():\n    pass\n")  # V06
    write(service / "tests/unit/test_broken.py", "def test_x(:\n")  # V08
    write(
        service / "tests/unit/test_wrong.py",
        'import pytest\n\n\n@pytest.mark.verifies("AGR-1")\ndef test_a_clause():\n    pass\n',
    )  # V04
    edit(service / "tests/integration/test_store.py", "import pytest\n",
         'import pytest\n\npytestmark = pytest.mark.verifies("REQ-SVC-02")\n')  # fmt: skip  # V15
    edit(service / "src/service/store.py", '\nImplements: DSN-SVC-02\n"""\n',
         '\n"""\n\n# Implements: DSN-SVC-02\n')  # fmt: skip  # a stray
    write(design, design.read_text(encoding="utf-8") + "\n## Record index (DSN-SVC-07)\n")  # V16
    planned = "\n| Planned | For |\n|---|---|\n| REQ-SVC-12 | export |\n"
    write(srs, srs.read_text(encoding="utf-8") + planned)  # V16
    tabled = "\n| Link | Target |\n|---|---|\n| Satisfies | REQ-SVC-03 |\n"
    edit(design, "before any handler runs.\n", "before any handler runs.\n" + tabled)  # a stray
    return service


# ── 1. goldens ─────────────────────────────────────────────────────────────────────────────


def test_a_clean_repo(project: Path, golden: Golden) -> None:
    code, output = check(project / "solo")
    assert code == 0
    golden(GOLDEN / "check-clean.txt", output)


def test_the_gate_fails_on_a_gap(project: Path, golden: Golden) -> None:
    code, output = check(project / "service", "--strict")
    assert code == 1
    golden(GOLDEN / "check-strict.txt", output)


@pytest.mark.verifies("REQ-QMT-03")
def test_every_finding(project: Path, golden: Golden) -> None:
    code, output = check(broken(project / "service"))
    assert code == 1
    golden(GOLDEN / "check-every-finding.txt", output)
    for code_ in (
        "V01",
        "V02",
        "V03",
        "V04",
        "V05",
        "V06",
        "V07",
        "V08",
        "V09",
        "V14",
        "V15",
        "V16",
    ):
        assert f"\n  {code_}  " in output, f"{code_} is missing from the wording review"


@pytest.mark.verifies("REQ-QMT-02")
def test_docs_written_like_an_architecture_guide_pass_the_gate(
    project: Path, golden: Golden
) -> None:
    """Numbered sections, sub-sections, tables and diagrams — every item still declared."""
    code, output = check(project / "rich", "--strict")
    assert code == 0
    golden(GOLDEN / "check-rich.txt", output)


@pytest.mark.verifies("REQ-QMT-02")
def test_what_such_docs_slip_into_is_named(project: Path, golden: Golden) -> None:
    """A link written into a table, a planned ID in a summary table, an ID at a heading's end."""
    rich = project / "rich"
    srs, design = rich / "docs/req/gateway-srs.md", rich / "docs/design/gateway-design.md"
    in_a_line, in_the_table = "\n- Satisfies: REQ-RCH-02\n", "| Satisfies | REQ-RCH-02 |\n"
    edit(design, "| wrong | 401 |\n" + in_a_line, "| wrong | 401 |\n" + in_the_table)
    edit(srs, "| REQ-RCH-02 | P0 |\n", "| REQ-RCH-02 | P0 |\n| REQ-RCH-03 | P1 |\n")
    write(design, design.read_text(encoding="utf-8") + "\n## 3. Later: an audit log (DSN-RCH-03)\n")
    code, output = check(rich)
    assert code == 1
    golden(GOLDEN / "check-rich-slips.txt", output)


def test_quiet_in_a_pipeline(alone: Callable[[str], Path], golden: Golden) -> None:
    code, output = check(alone("client"), "--quiet")
    assert code == 0
    golden(GOLDEN / "check-quiet-in-a-pipeline.txt", output)


# ── 2. exit codes ──────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-03")
def test_gaps_do_not_fail_while_authoring_and_do_under_the_gate(project: Path) -> None:
    assert check(project / "service")[0] == 0
    assert check(project / "service", "--strict")[0] == 1


@pytest.mark.verifies("REQ-QMT-03")
def test_a_violation_fails_in_every_mode(project: Path) -> None:
    write(project / "service/docs/notes.md", "### REQ-SVC-05 — Stray\n")
    assert check(project / "service")[0] == 1
    assert check(project / "service", "--quiet")[0] == 1


# ── 3. what cannot be verified is never hidden ─────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-12")
def test_what_could_not_be_verified_survives_quiet(alone: Callable[[str], Path]) -> None:
    output = check(alone("client"), "--quiet")[1]
    last = output.rstrip().splitlines()[-1]
    assert "NOT VERIFIED — ../ledger/agreement.md is not reachable" in output
    assert "NOT VERIFIED: the agreement, sibling service, 1 cited IDs" in last
    assert "the gate is qmstrace check --strict" in last


@pytest.mark.verifies("DSN-QMT-12")
def test_an_empty_result_never_looks_clean(tmp_path: Path, project: Path) -> None:
    empty = project / "solo"
    for path in (empty / "docs/req").glob("*.md"):
        path.unlink()
    for path in (empty / "tests").rglob("*.py"):
        path.unlink()
    output = check(empty)[1]
    assert "read: no items" in output and "in 0 items" in output


@pytest.mark.verifies("REQ-QMT-20")
@pytest.mark.parametrize("word", ["REQ-SVC-04.1a", "REQ-SVC-03b"])
def test_a_heading_that_starts_with_a_malformed_id_is_v02_naming_the_whole_word(
    project: Path, word: str
) -> None:
    # ADR-0002: a malformed ID of this repo's kind is reported, never read as prose — and never
    # cut short at its first dot.
    srs = project / "service" / "docs" / "req" / "service-srs.md"
    srs.write_text(srs.read_text(encoding="utf-8") + f"\n### {word} — A slip\n", encoding="utf-8")
    code, output = check(project / "service")
    assert code == 1
    (line,) = [line for line in output.splitlines() if line.startswith("  V02  ")]
    assert f"{word} does not match this repo's ID pattern" in line
