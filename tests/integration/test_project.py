"""The ledger's check of the whole project (M10, ADR-0001) on real repos.

The load-bearing claims, each pinned by a test:

1. In the layout where the ledger holds the documents, every repo is read and judged as one
   graph: the rules the ledger alone cannot meet are met by the product repos, and the same
   test path in two repos gives two items, never a V01.
2. Each repo's own violations are still its own — the same ones its own check reports when
   every sibling is read — located from the ledger; an ID nothing declares is a V03 in any
   repo of the project.
3. A repo that cannot be read, or holds other rules than the ledger's, stops the check, and
   every problem is named at once: a repo left unread would make a clean result a false one.
4. The ledger's baselines guard its documents; a change makes what hangs off it suspect in
   every repo — in another repo than the root's, by today's links only, labelled so.
5. The old layout, documents beside the code, is judged the same way, and two runs give the
   same result.
6. A walk from the ledger crosses every repo: forward from a requirement to the tests of each
   repo that verifies it, backward from a module to its origin clause.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.render import text
from qmstrace.workspace import Workspace


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def rewrite(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    assert old in content, f"{old!r} not in {path}"
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


SERVICE_TEST = "service:tests/unit/test_api.py::test_a_call_without_a_key_is_refused"
CLIENT_TEST = "client:tests/unit/test_api.py::test_a_call_without_a_key_is_refused"


# ── 1. one graph ───────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-14")
def test_every_repo_is_read_and_judged_as_one_graph(split: Path) -> None:
    project = Workspace.project(split / "ledger")
    assert [(r.name, r.location) for r in project.repos] == [
        ("client", "../client"),
        ("ledger", "."),
        ("service", "../service"),
    ]
    assert project.violations == () and project.gaps == ()
    assert len(project.graph.items()) == 13
    assert {SERVICE_TEST, CLIENT_TEST} <= {i.id for i in project.graph.items()}
    tests = {k.src for k in project.graph.incoming("REQ-SVC-01", "verifies")}
    assert tests == {SERVICE_TEST, CLIENT_TEST}


@pytest.mark.verifies("DSN-QMT-14")
def test_the_ledger_alone_fails_on_what_only_the_product_repos_meet(split: Path) -> None:
    alone = Workspace.open(split / "ledger").assessment()
    assert alone.violations == ()
    assert {g.code for g in alone.gaps} == {"G02", "G03", "G04"}
    assert all("qmstrace ledger check, run in the ledger" in g.next_move for g in alone.gaps)
    assert Workspace.project(split / "ledger").gaps == ()


def test_it_is_found_from_inside_the_ledger(split: Path) -> None:
    inside = split / "ledger" / "docs" / "req"
    assert len(Workspace.project(inside).graph.items()) == 13


# ── 2. each repo's own violations ──────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-14")
def test_an_id_nothing_declares_is_v03_located_from_the_ledger(split: Path) -> None:
    rewrite(split / "client" / "tests" / "unit" / "test_api.py", '"REQ-SVC-01"', '"REQ-SVC-09"')
    project = Workspace.project(split / "ledger")
    (found,) = project.violations
    assert (found.code, found.file) == ("V03", "../client/tests/unit/test_api.py")
    assert "no such item in any repo of the project" in found.what


@pytest.mark.verifies("DSN-QMT-14")
def test_each_repos_violations_are_the_ones_its_own_check_reports(split: Path) -> None:
    rewrite(split / "client" / "tests" / "unit" / "test_api.py", '"REQ-SVC-01"', '"REQ-SVC-09"')
    rewrite(split / "ledger" / "docs" / "req" / "client-srs.md", "- Category: security\n", "")
    rewrite(split / "service" / "src" / "service" / "store.py", "DSN-SVC-02", "REQ-SVC-02")
    project = Workspace.project(split / "ledger")
    whole = {(f.code, f.file, f.line) for f in project.violations}
    each = set()
    for repo, location in (("client", "../client"), ("ledger", "."), ("service", "../service")):
        own = Workspace.open(split / repo).assessment()
        each |= {
            (f.code, str(Path(location, f.file)).removeprefix("./"), f.line) for f in own.violations
        }
    assert whole == each
    assert {code for code, _, _ in whole} == {"V03", "V04", "V05"}


# ── 3. refused ─────────────────────────────────────────────────────────────────────────────


def refusal(split: Path) -> str:
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.project(split / "ledger")
    return caught.value.what


@pytest.mark.verifies("DSN-QMT-14")
def test_a_missing_repo_and_a_stale_copy_are_named_together(split: Path) -> None:
    Workspace.copy_schema(split / "ledger", ["service"])
    rewrite(split / "ledger" / "qmstrace.schema.toml", "verifies nothing.", "verifies nothing yet.")
    shutil.rmtree(split / "client")
    said = refusal(split)
    assert "client: there is no ../client/qmstrace.toml" in said
    assert "service: ../service/qmstrace.toml holds other rules than this ledger's" in said
    assert "run qmstrace ledger copy-schema service" in said


def test_a_ledger_holding_documents_must_list_itself(split: Path) -> None:
    rewrite(split / "ledger" / "qmstrace.schema.toml", 'ledger  = "."\n', "")
    assert 'add ledger = "." under [repos]' in refusal(split)


def test_two_names_for_one_folder_are_refused(split: Path) -> None:
    rewrite(
        split / "ledger" / "qmstrace.schema.toml",
        'client  = "../client"\n',
        'client  = "../client"\nagain   = "../client/"\n',
    )
    assert "client and again name the same folder, ../client" in refusal(split)


def test_a_repo_whose_configuration_cannot_be_read_is_named(split: Path) -> None:
    (split / "service" / "qmstrace.toml").write_text("version = 1\n[schema\n", encoding="utf-8")
    assert "service: its configuration could not be read" in refusal(split)


def test_reasons_that_end_their_own_sentence_are_not_given_a_second_stop(split: Path) -> None:
    for repo in ("client", "service"):
        (split / repo / "qmstrace.toml").write_text("version = 1\n", encoding="utf-8")
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.project(split / "ledger")
    said = f"{caught.value.what} {caught.value.next_move}"  # as the command prints it
    assert "the [schema] table is missing; service:" in said
    assert "the [schema] table is missing. Fix: deal with each repo named above" in said
    assert ".. " not in said and ".;" not in said


def test_run_in_a_product_repo_it_names_the_ledger(split: Path) -> None:
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.project(split / "service")
    assert "is a product repo — its ledger is at ../ledger" in caught.value.what


# ── 4. baselines and suspects ──────────────────────────────────────────────────────────────

TAG = "baseline/requirements/1"


def reword_after_the_baseline(split: Path, *, cite: bool) -> None:
    ledger = split / "ledger"
    git(ledger, "tag", "-a", TAG, "-m", "requirements approved")
    srs = ledger / "docs" / "req" / "service-srs.md"
    rewrite(srs, "with status 401", "with status 403")
    if cite:
        rewrite(srs, "- Verify-by: test\n", "- Verify-by: test\n- Change: CR-001\n")


@pytest.mark.verifies("DSN-QMT-14")
def test_a_change_to_a_frozen_document_without_a_request_is_v10(split: Path) -> None:
    reword_after_the_baseline(split, cite=False)
    project = Workspace.project(split / "ledger")
    assert [(f.code, f.item) for f in project.violations] == [("V10", "REQ-SVC-01")]


@pytest.mark.verifies("DSN-QMT-08", "DSN-QMT-14")
def test_what_hangs_off_a_change_is_suspect_in_every_repo(split: Path) -> None:
    reword_after_the_baseline(split, cite=True)
    project = Workspace.project(split / "ledger")
    assert project.violations == ()
    reasons = {s.item.id: s.reasons[0] for s in project.suspects}
    assert reasons["DSN-SVC-01"].unpinned_repo is None
    assert reasons["DSN-SVC-01"].edited is False
    for dependant, repo in ((SERVICE_TEST, "service"), (CLIENT_TEST, "client")):
        assert (reasons[dependant].unpinned_repo, reasons[dependant].edited) == (repo, None)
        assert reasons[dependant].current_distance == 1


# ── 5. the old layout; the same result twice ───────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-14")
def test_the_old_layout_is_judged_the_same_way(project: Path) -> None:
    Workspace.copy_schema(project / "ledger", ["service"])
    service = project / "service"
    git(service, "add", "-A")
    git(service, "commit", "-qm", "carry the project's schema")
    git(service, "tag", "-a", "baseline/service/requirements/1", "-m", "requirements approved")
    rewrite(service / "docs" / "req" / "service-srs.md", "status 401", "status 403")
    whole = Workspace.project(project / "ledger")
    assert [r.name for r in whole.repos] == ["client", "service"]
    assert [(f.code, f.item) for f in whole.violations] == [("V10", "REQ-SVC-01")]
    client_test = "client:tests/unit/test_api.py::test_the_service_refuses_a_call_without_a_key"
    across = {s.item.id: s.reasons[0] for s in whole.suspects}[client_test]
    assert (across.unpinned_repo, across.edited) == ("client", None)


def test_two_runs_give_the_same_bytes(split: Path) -> None:
    reword_after_the_baseline(split, cite=True)
    once = text.ledger_check(Workspace.project(split / "ledger"), strict=True, quiet=False)
    again = text.ledger_check(Workspace.project(split / "ledger"), strict=True, quiet=False)
    assert once == again
    assert str(split) not in once


# ── 6. walks across repos ──────────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-14")
def test_a_walk_from_the_ledger_crosses_every_repo(split: Path) -> None:
    project = Workspace.project_thread(split / "ledger", "REQ-SVC-01")
    forward = project.graph.forward(["REQ-SVC-01"]).steps
    assert {SERVICE_TEST, CLIENT_TEST, "service:src/service/keys.py"} <= forward.keys()
    backward = project.graph.backward(["client:src/client/api.py"]).steps
    assert {"DSN-CLT-01", "REQ-CLT-01", "AGR-3"} <= backward.keys()


def test_an_unseen_start_refuses_the_whole_impact(split: Path) -> None:
    with pytest.raises(CouldNotJudge) as caught:
        Workspace.project_impact(split / "ledger", ["REQ-SVC-01", "REQ-SVC-09"])
    assert "REQ-SVC-09 is not an item of the project" in caught.value.what
