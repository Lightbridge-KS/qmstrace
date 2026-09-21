"""`qmstrace rules` — what `check` holds a repo to, and whose each part is.

The load-bearing claims, each pinned by a test:

1. Its output is a golden file: a repo that reads the project's schema by path, a repo with its
   own schema, and a repo in a pipeline that carries a verified copy.
2. It reads the configuration alone — nothing is scanned — so it answers even where the rest of
   the project cannot be read.
3. A rule this repo cannot meet, or that applies to no item here, says so.
"""

from collections.abc import Callable
from pathlib import Path

from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
Golden = Callable[[Path, str], None]
runner = CliRunner()


def rules(root: Path) -> tuple[int, str]:
    result = runner.invoke(app, ["-C", str(root), "rules"])
    return result.exit_code, result.output


def test_rules_for_a_repo_that_reads_the_schema_by_path(project: Path, golden: Golden) -> None:
    code, output = rules(project / "service")
    assert code == 0
    golden(GOLDEN / "rules-service.txt", output)


def test_rules_for_a_repo_with_its_own_schema(project: Path, golden: Golden) -> None:
    code, output = rules(project / "solo")
    assert code == 0
    golden(GOLDEN / "rules-solo.txt", output)


def test_rules_in_a_pipeline_need_nothing_beside_the_repo(
    alone: Callable[[str], Path], golden: Golden
) -> None:
    code, output = rules(alone("client"))
    assert code == 0
    golden(GOLDEN / "rules-client-in-a-pipeline.txt", output)


def test_a_rule_that_cannot_be_met_here_says_so(project: Path) -> None:
    output = rules(project / "client")[1]
    g01 = next(line for line in output.splitlines() if line.strip().startswith("G01"))
    g03 = next(line for line in output.splitlines() if line.strip().startswith("G03"))
    assert "cannot be met with the item types this repo scans" in g01
    assert "applies to no item here" in g03


def test_rules_read_nothing_but_the_configuration(project: Path) -> None:
    broken = project / "service" / "docs" / "req" / "service-srs.md"
    broken.write_bytes(b"\xff\xfe not text")  # a scan would report V08; rules never scans
    assert rules(project / "service")[0] == 0
