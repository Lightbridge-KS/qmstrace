"""`qmstrace thread <ID>` — one item backward to what it derives from, forward to what hangs off it.

The load-bearing claims, each pinned by a test:

1. Its output is a golden file: a requirement; a test case walked back to its clauses; a clause
   and what derives from it; a sibling's item; the same item as a pipeline sees it.
2. Each item is shown once, nearest first; the header says what this run could not read, and
   how many links it refused — never an empty result that looks like a clean one.
3. An ID nothing here can see cannot be judged: exit 2, with the closest IDs.
4. Two runs give the same bytes.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

GOLDEN = Path(__file__).parent / "golden"
Golden = Callable[[Path, str], None]
runner = CliRunner()
STORE_TEST = "tests/integration/test_store.py::test_a_record_survives_a_restart"


def thread(root: Path, item_id: str) -> tuple[int, str]:
    result = runner.invoke(app, ["-C", str(root), "thread", item_id])
    return result.exit_code, result.output


# ── 1. goldens ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("name", "repo", "item_id"),
    [
        ("thread-requirement", "service", "REQ-SVC-01"),
        ("thread-backward", "service", STORE_TEST),
        ("thread-origin", "service", "AGR-3"),
        ("thread-sibling", "client", "REQ-SVC-01"),
    ],
)
def test_thread_output(project: Path, golden: Golden, name: str, repo: str, item_id: str) -> None:
    code, output = thread(project / repo, item_id)
    assert code == 0
    golden(GOLDEN / f"{name}.txt", output)


def test_thread_as_a_pipeline_sees_it(alone: Callable[[str], Path], golden: Golden) -> None:
    code, output = thread(alone("client"), "REQ-SVC-01")
    assert code == 0
    golden(GOLDEN / "thread-in-a-pipeline.txt", output)


# ── 2. each item once; nothing hidden ──────────────────────────────────────────────────────


def test_each_item_is_shown_once(project: Path) -> None:
    output = thread(project / "service", "AGR-3")[1]
    assert output.count(f"{STORE_TEST} ") == 1
    assert "also verifies DSN-SVC-02" in output


def test_refused_links_are_counted_in_the_header(project: Path) -> None:
    notes = project / "service" / "docs" / "notes.md"
    notes.write_text("### REQ-SVC-05 — Stray\n", encoding="utf-8")
    output = thread(project / "service", "REQ-SVC-01")[1]
    assert "1 violation — the links they refuse are not shown" in output


def test_an_uncited_sibling_item_and_an_uncited_clause_can_be_threaded(project: Path) -> None:
    code, output = thread(project / "client", "REQ-SVC-02")
    assert code == 0
    assert "requirement, in sibling service — not pinned · ../service/docs/req/" in output
    assert "nothing here hangs off it" in output
    code, output = thread(project / "client", "AGR-2")
    assert code == 0 and "nothing here hangs off it" in output


# ── 3. an ID nothing here can see ──────────────────────────────────────────────────────────


def test_an_unknown_id_cannot_be_judged_and_the_closest_are_offered(project: Path) -> None:
    code, output = thread(project / "service", "REQ-SVC-1")
    assert code == 2
    assert "REQ-SVC-1 is not an item this run can see" in output
    assert "the closest here: REQ-SVC-01" in output


def test_in_a_pipeline_an_unseen_id_is_not_called_missing(alone: Callable[[str], Path]) -> None:
    code, output = thread(alone("client"), "REQ-SVC-02")
    assert code == 2
    assert "sibling service could not be read" in output


# ── 4. determinism ─────────────────────────────────────────────────────────────────────────


def test_two_runs_give_the_same_bytes(project: Path) -> None:
    assert thread(project / "service", "REQ-SVC-01") == thread(project / "service", "REQ-SVC-01")
