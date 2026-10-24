"""The workspace — a run end to end over real Git repositories, short of the text it prints.

The load-bearing claims, each pinned by a test:

1. The root is found by walking up to the trace configuration; a ledger repo, or a folder with
   no configuration above it, cannot be judged — and the refusal names the right place.
2. With the ledger and the siblings beside it, externals are verified and a sibling's items
   are cited like local ones.
3. In a pipeline — one repo checked out, no ledger — every external and every sibling is *not
   verified here*, a citation of a sibling's item passes as such, and nothing fails for it.
4. A sibling that is missing, or whose configuration cannot be read, is said so; the run goes
   on. A repo the schema does not list is told so.
5. A repo on its own resolves its external sources against its own root.
6. What the user's repo gets wrong is a finding: an item where its type is not read (V07), a
   file that is not UTF-8 (V08) — never a crash. An ignored note is never read.
7. Item type names are data: a schema that still calls its pytest functions `test_case`, as
   schemas did before ADR-0003, reads the same tests with the same links and the same gaps.
"""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.core.assessment import Assessment
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Home
from qmstrace.workspace import Workspace


def assess(root: Path) -> Assessment:
    return Workspace.open(root).assessment()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ── 1. finding the root ────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-02")
def test_the_root_is_found_from_a_folder_inside_the_repo(project: Path) -> None:
    workspace = Workspace.open(project / "service" / "src" / "service")
    assert workspace.root == project / "service"


def test_a_ledger_repo_is_not_a_product_repo(project: Path) -> None:
    with pytest.raises(CouldNotJudge) as stopped:
        Workspace.open(project / "ledger")
    assert "ledger repo" in stopped.value.what
    assert "-C <path>" in stopped.value.next_move


def test_a_folder_with_no_configuration_above_it_cannot_be_judged(tmp_path: Path) -> None:
    with pytest.raises(CouldNotJudge) as stopped:
        Workspace.open(tmp_path)
    assert "no qmstrace.toml" in stopped.value.what


def test_a_configuration_that_is_not_utf8_cannot_be_judged(project: Path) -> None:
    (project / "service" / "qmstrace.toml").write_bytes(b"version = 1 # caf\xe9\n")
    with pytest.raises(CouldNotJudge) as stopped:
        Workspace.open(project / "service")
    assert "not UTF-8" in stopped.value.what


# ── 2. everything beside it ────────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-02")
def test_with_everything_beside_it_the_repo_is_judged_in_full(project: Path) -> None:
    found = assess(project / "client")
    assert found.violations == ()
    assert [(e.prefix, e.location, e.declared) for e in found.externals] == [
        ("AGR-", "../ledger/agreement.md", 3)
    ]
    (sibling,) = found.siblings
    assert (sibling.name, sibling.location, sibling.declares) == (
        "service",
        "service:.",
        {"requirement": 3, "design_element": 2},
    )
    node = found.graph.node("REQ-SVC-01")
    assert node is not None and (node.home, node.repo) == (Home.SIBLING, "service")
    assert found.graph.unverified() == []
    assert [n.text for n in found.notices if "not among" in n.text] == []


def test_a_repo_scans_what_its_configuration_names(project: Path) -> None:
    found = assess(project / "service")
    scanned = {s.item_type: (s.items, s.files, s.ignored) for s in found.scanned}
    assert scanned == {
        "requirement": (3, 1, 0),
        "design_element": (2, 1, 0),
        "component": (2, 2, 1),
        "automated_test": (4, 2, 0),
    }
    assert found.violations == ()
    assert len(found.graph.links) == 14


# ── 3. a pipeline ──────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-02")
def test_in_a_pipeline_what_cannot_be_read_is_not_verified_and_fails_nothing(
    alone: Callable[[str], Path],
) -> None:
    found = assess(alone("client"))
    assert found.violations == ()
    assert [(e.location, e.declared) for e in found.externals] == [("../ledger/agreement.md", None)]
    assert [(s.name, s.problem) for s in found.siblings] == [("service", "not reachable")]
    assert found.graph.unverified() == ["REQ-SVC-01"]
    assert [n.text for n in found.notices if "not among" in n.text] == []  # client is listed


def test_without_a_ledger_pointer_the_siblings_cannot_be_located(
    alone: Callable[[str], Path],
) -> None:
    checkout = alone("client")
    config = checkout / "qmstrace.toml"
    config.write_text(config.read_text().replace('ledger  = "../ledger"\n', ""), encoding="utf-8")
    found = assess(checkout)
    assert found.violations == ()
    assert [e.location for e in found.externals] == [None]
    assert found.siblings == () and found.siblings_located is False
    assert found.graph.unverified() == ["REQ-SVC-01"]


def test_an_own_id_that_does_not_exist_fails_even_in_a_pipeline(
    alone: Callable[[str], Path],
) -> None:
    checkout = alone("client")
    test = checkout / "tests" / "unit" / "test_api.py"
    test.write_text(test.read_text().replace('"REQ-CLT-01"', '"REQ-CLT-07"'), encoding="utf-8")
    found = assess(checkout)
    assert [f.code for f in found.violations] == ["V03"]


# ── 4. siblings missing or unreadable; a repo the schema does not list ─────────────────────


def test_a_missing_sibling_is_not_reachable(project: Path) -> None:
    shutil.rmtree(project / "service")
    found = assess(project / "client")
    assert [(s.name, s.problem) for s in found.siblings] == [("service", "not reachable")]
    assert found.graph.unverified() == ["REQ-SVC-01"] and found.violations == ()


def test_a_sibling_whose_configuration_cannot_be_read_is_said_so(project: Path) -> None:
    (project / "service" / "qmstrace.toml").write_text("version = = 1\n", encoding="utf-8")
    found = assess(project / "client")
    (sibling,) = found.siblings
    assert sibling.declares is None
    assert sibling.problem is not None and "not valid TOML" in sibling.problem
    assert found.violations == ()


def test_a_repo_the_schema_does_not_list_is_told_so(project: Path) -> None:
    schema = project / "ledger" / "qmstrace.schema.toml"
    schema.write_text(schema.read_text().replace('client  = "../client"\n', ""), encoding="utf-8")
    found = assess(project / "client")
    assert any("not among the project's repos" in n.text for n in found.notices)


def test_a_siblings_findings_are_its_own(project: Path) -> None:
    srs = project / "service" / "docs" / "req" / "service-srs.md"
    srs.write_text(srs.read_text().replace("- Verify-by: test\n", "", 1), encoding="utf-8")
    assert assess(project / "client").violations == ()
    assert [f.code for f in assess(project / "service").violations] == ["V05"]


# ── 5. a repo on its own ───────────────────────────────────────────────────────────────────


def test_a_repo_on_its_own_resolves_its_sources_against_itself(project: Path) -> None:
    found = assess(project / "solo")
    assert [(e.location, e.declared) for e in found.externals] == [("docs/brief.md", 2)]
    assert found.siblings == () and found.siblings_located is True
    assert found.violations == ()


# ── 6. findings, never crashes ─────────────────────────────────────────────────────────────


def test_an_item_where_its_type_is_not_read_is_v07(project: Path) -> None:
    write(project / "service" / "docs" / "notes.md", "# Notes\n\n### REQ-SVC-05 — Stray\n")
    (finding,) = assess(project / "service").violations
    assert (finding.code, finding.file, finding.line) == ("V07", "docs/notes.md", 3)


def test_a_decorated_heading_where_its_type_is_not_read_is_v07(project: Path) -> None:
    write(project / "service" / "docs" / "notes.md", "# Notes\n\n## 4.2 **REQ-SVC-05** — X\n")
    (finding,) = assess(project / "service").violations
    assert (finding.code, finding.file, finding.line) == ("V07", "docs/notes.md", 3)
    assert "move it there" in finding.next_move


def test_a_recap_of_a_declared_item_says_not_to_start_a_heading_with_it(project: Path) -> None:
    write(project / "service" / "docs" / "notes.md", "# Notes\n\n### 4.1 REQ-SVC-01 — recap\n")
    (finding,) = assess(project / "service").violations
    assert (finding.code, finding.file) == ("V07", "docs/notes.md")
    assert "REQ-SVC-01 is declared at docs/req/service-srs.md:12" in finding.next_move
    assert "do not start a heading with its ID" in finding.next_move


def test_a_file_that_is_not_utf8_is_v08(project: Path) -> None:
    (project / "service" / "docs" / "notes.md").write_bytes(b"# Caf\xe9\n")
    (finding,) = assess(project / "service").violations
    assert (finding.code, finding.file) == ("V08", "docs/notes.md")


@pytest.mark.verifies("REQ-QMT-11")
def test_an_ignored_note_is_never_read(project: Path) -> None:
    write(project / "service" / ".gitignore", "_playground/\n")
    write(project / "service" / "_playground" / "NOTES.md", "### REQ-SVC-01 — quoted\n")
    assert assess(project / "service").violations == ()


# ── 7. item type names are data ────────────────────────────────────────────────────────────


def test_a_schema_that_calls_its_tests_test_case_reads_them_the_same(project: Path) -> None:
    unlinked = "tests/unit/test_extra.py::test_unlinked"  # so that G07 has something to find
    write(project / "service" / unlinked.split("::")[0], "def test_unlinked():\n    pass\n")
    renamed = assess(project / "service")
    for name in ("ledger/qmstrace.schema.toml", "service/qmstrace.toml", "client/qmstrace.toml"):
        path = project / name
        write(path, path.read_text(encoding="utf-8").replace("automated_test", "test_case"))
    found = assess(project / "service")

    def gaps(assessment: Assessment) -> set[tuple[str, str | None]]:
        return {(g.code, g.item) for g in assessment.gaps}

    assert [i.id for i in found.graph.items("test_case")] == [
        i.id for i in renamed.graph.items("automated_test")
    ]
    assert found.graph.items("automated_test") == []
    assert set(found.graph.links) == set(renamed.graph.links)  # in another order: by type name
    assert found.violations == renamed.violations == ()
    assert gaps(found) == gaps(renamed) and ("G07", unlinked) in gaps(found)
