"""Change control against real Git: ancestry, historical configuration and fresh citations."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.infra.git import GitCli
from qmstrace.infra.tree import GitTree, WorkingTree
from qmstrace.render import text
from qmstrace.workspace import Workspace

REQ = "docs/req/service-srs.md"
TAG = "baseline/service/requirements/1"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def commit(root: Path, message: str = "fixture") -> str:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def controlled(project, embed, monkeypatch):
    monkeypatch.setenv("GIT_AUTHOR_DATE", "2026-01-01T00:00:00+00:00")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-01-01T00:00:00+00:00")
    root = project / "service"
    config = root / "qmstrace.toml"
    config.write_text(
        embed(config.read_text(), (project / "ledger/qmstrace.schema.toml").read_text())
    )
    commit(root, "embed historical schema")
    git(root, "tag", "-a", TAG, "-m", "requirements approved")
    (project / "ledger/change-requests").mkdir()
    return root


def edit(root: Path, *, citation: str = "") -> None:
    path = root / REQ
    source = path.read_text()
    # Change exactly one item title, keeping its identity and every marker intact.
    lines = source.splitlines(keepends=True)
    index = next(n for n, line in enumerate(lines) if "### REQ-SVC-01" in line)
    lines[index] = lines[index].rstrip() + " revised\n" + citation
    path.write_text("".join(lines))


def request(root: Path, state="accepted", impacts="REQ-SVC-01", name="CR-001") -> None:
    path = root.parent / "ledger/change-requests" / f"{name}.md"
    path.write_text(f"# {name} — Change\n\n- State: {state}\n- Impacts: {impacts}\n")


def codes(root: Path) -> set[str]:
    return {f.code for f in Workspace.open(root).assessment().violations}


def test_frozen_and_tree_contract(controlled):
    source = GitCli(controlled)
    revision = source.state()
    tree = GitTree(source, revision)
    working = WorkingTree(controlled)
    assert tree.files() == working.files()
    assert {p: tree.read(p) for p in tree.files()} == {p: working.read(p) for p in working.files()}
    view = Workspace.open(controlled).assessment()
    assert [c.state for c in view.baseline_state.comparisons] == ["frozen"] * 3
    assert view.baseline_state.baselines[0].tags[0].tagger == "Fixture"
    assert "3 frozen · 0 changed · 0 new · 0 removed" in text.status(view)
    assert "[frozen; baseline/service/requirements/1]" in text.status(view)
    assert "remote-tag completeness NOT VERIFIED" in text.check(view, strict=True, quiet=True)


@pytest.mark.parametrize(
    "state,impacts,expected",
    [
        (None, "REQ-SVC-01", "V11"),
        ("proposed", "REQ-SVC-01", "V11"),
        ("Accepted", "REQ-SVC-01", "V11"),
        ("accepted", "REQ-SVC-02", "V12"),
        ("accepted", "REQ-SVC-01", None),
    ],
)
def test_request_judgment(controlled, state, impacts, expected):
    if state:
        request(controlled, state, impacts)
    edit(controlled, citation="- Change: CR-001\n")
    assert codes(controlled) == ({expected} if expected else set())


def test_missing_stale_and_multiple_citations(controlled):
    edit(controlled)
    assert codes(controlled) == {"V10"}
    path = controlled / REQ
    path.write_text(path.read_text().replace(" revised\n", " revised\n- Change: CR-001\n", 1))
    request(controlled)
    assert not codes(controlled)
    commit(controlled)
    git(controlled, "tag", "baseline/service/requirements/2")
    edit(controlled)
    assert codes(controlled) == {"V10"}
    path.write_text(path.read_text().replace("Change: CR-001", "Change: CR-001, CR-002, CR-003"))
    request(controlled, name="CR-002")
    assert codes(controlled) == {"V11"}  # CR-003 is missing, even though CR-002 is valid


def test_layout_and_citation_only_changes_do_not_change_digest(controlled):
    path = controlled / REQ
    path.write_text(path.read_text().replace(" ", "  ") + "\n")
    assert all(
        c.state == "frozen"
        for c in Workspace.open(controlled).assessment().baseline_state.comparisons
    )
    source = git(controlled, "show", f"{TAG}:{REQ}")
    path.write_text(source.replace("### REQ-SVC-01", "### REQ-SVC-01", 1))
    lines = path.read_text().splitlines()
    index = next(i for i, line in enumerate(lines) if "### REQ-SVC-01" in line)
    lines.insert(index + 1, "- Change: CR-001")
    path.write_text("\n".join(lines))
    assert not codes(controlled)
    assert all(
        c.state == "frozen"
        for c in Workspace.open(controlled).assessment().baseline_state.comparisons
    )


def test_added_removed_and_changed_link(controlled):
    path = controlled / REQ
    source = path.read_text()
    path.write_text(source.replace("REQ-SVC-01", "REQ-SVC-04"))
    assert {"V10", "V13"} <= codes(controlled)
    comparisons = Workspace.open(controlled).assessment().baseline_state.comparisons
    assert {(c.id, c.state) for c in comparisons} == {
        ("REQ-SVC-01", "removed"),
        ("REQ-SVC-02", "frozen"),
        ("REQ-SVC-03", "frozen"),
        ("REQ-SVC-04", "new"),
    }
    path.write_text(source.replace("Origin: AGR-1", "Origin: AGR-2", 1))
    assert "V10" in codes(controlled)


def test_unavailable_register_passes_fresh_citation_with_notice(controlled):
    edit(controlled, citation="- Change: CR-001\n")
    shutil.rmtree(controlled.parent / "ledger/change-requests")
    assessment = Workspace.open(controlled).assessment()
    assert not assessment.violations
    assert (
        "change requests NOT VERIFIED"
        in text.check(assessment, strict=True, quiet=True).splitlines()[-1]
    )


def test_malformed_register_is_not_unavailable(controlled):
    request(controlled)
    path = controlled.parent / "ledger/change-requests/CR-001.md"
    path.write_text(path.read_text() + "- State: accepted\n")
    edit(controlled, citation="- Change: CR-001\n")
    assert codes(controlled) == {"V08", "V11"}
    path.write_bytes(b"\xff")
    assert codes(controlled) == {"V08", "V11"}


def test_reserved_unseen_start_still_rejects_entire_impact(controlled):
    request(controlled, impacts="REQ-SVC-99")
    with pytest.raises(CouldNotJudge, match="reserved, but not declared") as caught:
        Workspace.open(controlled).impact(["REQ-SVC-01", "REQ-SVC-99"])
    assert "No impact list" in caught.value.next_move


def test_withdrawal_preserves_graph_and_requires_authorization(controlled):
    design = controlled / "docs/design/service-design.md"
    source = design.read_text()
    design.write_text(
        source.replace("### DSN-SVC-01", "### DSN-SVC-01", 1).replace(
            "Satisfies: REQ-SVC-01", "Status: withdrawn\nSatisfies: REQ-SVC-01", 1
        )
    )
    view = Workspace.open(controlled).assessment()
    assert any(g.item == "REQ-SVC-01" and g.code == "G01" for g in view.gaps)
    assert not any(g.item == "DSN-SVC-01" for g in view.gaps)
    assert "DSN-SVC-01" in view.graph.forward(["REQ-SVC-01"]).steps
    path = controlled / REQ
    source = path.read_text()
    path.write_text(source.replace("- Origin: AGR-1", "- Status: withdrawn\n- Origin: AGR-1", 1))
    assert "V10" in codes(controlled)
    path.write_text(
        path.read_text().replace("- Status: withdrawn", "- Status: withdrawn\n- Change: CR-001")
    )
    request(controlled)
    assert "V10" not in codes(controlled)
    commit(controlled)
    git(controlled, "tag", "baseline/service/requirements/2")
    path.write_text(path.read_text().replace("Status: withdrawn", "Status: active"))
    assert "V10" in codes(controlled)


def test_external_schema_at_baseline_is_not_replaced_with_current_schema(project):
    root = project / "service"
    git(root, "tag", TAG)
    with pytest.raises(CouldNotJudge, match="outside the tagged Git tree"):
        Workspace.open(root).assessment()


def test_historical_patterns_and_subjects_survive_current_config_changes(controlled):
    config = controlled / "qmstrace.toml"
    source = config.read_text()
    config.write_text(
        source.replace('files      = ["docs/req/*-srs.md"]', 'files = ["missing/*.md"]')
    )
    assert "V13" in codes(controlled)
    config.write_text(source.replace('key = "SVC"', 'key = "OTHER"'))
    assert all(
        c.state == "frozen"
        for c in Workspace.open(controlled).assessment().baseline_state.comparisons
    )


def test_pretrace_release_and_detached_head(controlled):
    parent = git(controlled, "rev-parse", "HEAD~1")
    # The initial fixture is traced by path, so create a genuinely pre-trace root separately.
    git(controlled, "checkout", "--orphan", "pretrace")
    git(controlled, "rm", "-qrf", ".")
    (controlled / "README.md").write_text("Before adoption\n")
    commit(controlled)
    git(controlled, "tag", "v0.0.1")
    git(controlled, "checkout", "--detach", parent)
    # Unreachable release is ignored; there is no reachable requirements baseline here.
    assert not Workspace.open(controlled).assessment().baseline_state.baselines
    git(controlled, "checkout", "pretrace")
    git(controlled, "checkout", "main", "--", ".")
    commit(controlled)
    assessment = Workspace.open(controlled).assessment()
    assert not assessment.baseline_state.comparisons
    assert any("before trace configuration" in n.text for n in assessment.notices)


def test_latest_is_ancestry_not_tag_number_or_date(controlled, monkeypatch):
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2020-01-01T00:00:00+00:00")
    (controlled / "note.md").write_text("later commit, older date")
    commit(controlled)
    git(controlled, "tag", "baseline/service/requirements/0")
    assessment = Workspace.open(controlled).assessment()
    assert assessment.baseline_state.baselines[0].label.endswith("/0")
    assert any("lightweight" in n.text for n in assessment.notices)


def test_same_commit_aliases_and_overlapping_scopes_are_deduplicated(controlled):
    git(controlled, "tag", "baseline/service/requirements/2")
    git(controlled, "tag", "v1.0.0")
    edit(controlled)
    view = Workspace.open(controlled).assessment()
    assert len([f for f in view.violations if f.code == "V10"]) == 1
    comparison = next(c for c in view.baseline_state.comparisons if c.id == "REQ-SVC-01")
    assert len(comparison.baseline.tags) == 3


@pytest.mark.parametrize("other_tag", ["baseline/service/requirements/3", "v2.0.0"])
def test_incomparable_tags_fail_after_merge(controlled, other_tag):
    base = git(controlled, "rev-parse", "HEAD")
    (controlled / "a.md").write_text("A")
    commit(controlled)
    git(controlled, "tag", "baseline/service/requirements/2")
    git(controlled, "checkout", "-qb", "other", base)
    (controlled / "b.md").write_text("B")
    commit(controlled)
    git(controlled, "tag", other_tag)
    git(controlled, "merge", "--no-edit", "main")
    with pytest.raises(CouldNotJudge, match="incomparable tags"):
        Workspace.open(controlled).assessment()


def test_shallow_and_excluded_tags_fail(controlled, tmp_path):
    clone = tmp_path / "shallow"
    git(tmp_path, "clone", "--depth=1", controlled.as_uri(), str(clone))
    with pytest.raises(CouldNotJudge, match="shallow"):
        Workspace.open(clone).assessment()
    for key, value in [
        ("remote.origin.tagOpt", "--no-tags"),
        ("remote.origin.fetch", "^refs/tags/baseline/*"),
    ]:
        git(controlled, "config", key, value)
        with pytest.raises(CouldNotJudge, match="excludes tags"):
            Workspace.open(controlled).assessment()
        git(controlled, "config", "--unset", key)


def test_worktree_and_missing_objects(controlled, tmp_path):
    linked = tmp_path / "linked"
    git(controlled, "worktree", "add", "--detach", str(linked))
    assert len(Workspace.open(linked).assessment().baseline_state.comparisons) == 3
    with pytest.raises(CouldNotJudge, match="baseline evidence is unavailable"):
        GitTree(GitCli(controlled), "0" * 40).files()


def test_non_git_with_configured_baselines_cannot_judge(controlled, tmp_path):
    destination = tmp_path / "plain"
    shutil.copytree(controlled, destination, ignore=shutil.ignore_patterns(".git"))
    with pytest.raises(CouldNotJudge, match="baseline evidence is unavailable"):
        Workspace.open(destination).assessment()


def test_same_tree_schema_unicode_bom_and_nested_root(project):
    root = project / "solo"
    top = root / "qmstrace.toml"
    # A nested trace root may refer to a schema elsewhere in its enclosing Git tree.
    local = top.read_text()
    prefix, schema = local.split("[schema]\n", 1)
    schema, items = schema.split("[subjects.app]", 1)
    schema = re.sub(r"(?m)^(\[\[?)schema\.", r"\1", schema)
    (root / "schema.toml").write_text(schema)
    nested = root / "nested"
    nested.mkdir()
    for folder in ("docs", "tests"):
        shutil.move(str(root / folder), nested / folder)
    top.unlink()
    (nested / "qmstrace.toml").write_text(
        prefix + '[schema]\npath = "../schema.toml"\n' + "[subjects.app]" + items
    )
    (nested / "café.md").write_text("\ufeffUnicode\n")
    revision = commit(root)
    git(root, "tag", "v1.0.0")
    tree = GitTree(GitCli(nested), revision)
    assert tree.read("café.md") == "Unicode\n"
    assert tree.files() == WorkingTree(nested).files()
    assert tree.read("../schema.toml") == schema
    view = Workspace.open(nested).assessment()
    assert len(view.baseline_state.comparisons) == 1
    (nested / "café.md").unlink()
    assert tree.read("café.md") == "Unicode\n"
    assert "café.md" in tree.files() and "café.md" not in WorkingTree(nested).files()


@pytest.mark.parametrize("kind", ["config", "source", "duplicate", "schema_encoding"])
def test_unusable_historical_snapshot_fails(controlled, kind):
    config = controlled / "qmstrace.toml"
    original = config.read_text()
    srs = controlled / REQ
    original_srs = srs.read_text()
    if kind == "config":
        config.write_text("bad = [")
    elif kind == "source":
        (controlled / "tests/unit/bad.py").write_text("def broken(:")
        # Scan patterns intentionally include this file at the tag only.
        config.write_text(original.replace("tests/**/test_*.py", "tests/**/*.py"))
    elif kind == "duplicate":
        srs.write_text(original_srs + original_srs)
    else:
        config.write_text(
            re.sub(
                r"(?ms)^\[schema\].*?(?=^\[subjects)", '[schema]\npath = "schema.toml"\n', original
            )
        )
        (controlled / "schema.toml").write_bytes(b"\xff")
    commit(controlled)
    git(controlled, "tag", "baseline/service/requirements/2")
    config.write_text(original)
    srs.write_text(original_srs)
    with pytest.raises(CouldNotJudge):
        Workspace.open(controlled).assessment()


def test_type_rename_does_not_hide_frozen_identity(controlled):
    config = controlled / "qmstrace.toml"
    source = re.sub(r"(?m)^digest = .*\n", "", config.read_text())
    config.write_text(source.replace("requirement", "need"))
    edit(controlled)
    # Scope names were renamed too; match the old tag with the renamed configured scope.
    config.write_text(config.read_text().replace("/needs/", "/requirements/"))
    assert "V10" in codes(controlled)


def test_new_subject_is_not_frozen_by_release(controlled):
    git(controlled, "tag", "v1.0.0")
    config = controlled / "qmstrace.toml"
    config.write_text(
        config.read_text().replace("^REQ-SVC-", "^REQ-(SVC|NEW)-")
        + '\n[subjects.new]\nkey = "NEW"\n'
    )
    srs = controlled / REQ
    srs.write_text(
        srs.read_text() + "\n### REQ-NEW-01 — New subject\n"
        "- Category: security\n- Origin: AGR-1\n- Verify-by: test\n"
    )
    view = Workspace.open(controlled).assessment()
    assert not any(c.id == "REQ-NEW-01" for c in view.baseline_state.comparisons)
    assert "V10" not in {f.code for f in view.violations}


def test_ambiguous_subject_key_fails_for_new_item(controlled):
    config = controlled / "qmstrace.toml"
    config.write_text(config.read_text() + '\n[subjects.duplicate]\nkey = "SVC"\n')
    srs = controlled / REQ
    srs.write_text(srs.read_text() + "\n### REQ-SVC-04 — Added\n")
    with pytest.raises(CouldNotJudge, match="ambiguous"):
        Workspace.open(controlled).assessment()


def test_malformed_change_and_duplicate_metadata_are_findings(controlled):
    edit(controlled, citation="- Change: TBD, ZZ-001\n- Change: CR-001\n")
    assert {"V08", "V14"} <= codes(controlled)


def test_withdrawn_sibling_is_not_coverage_but_remains_in_results(controlled):
    srs = controlled / REQ
    srs.write_text(
        srs.read_text().replace("- Origin: AGR-1", "- Status: withdrawn\n- Origin: AGR-1", 1)
    )
    client = controlled.parent / "client"
    test = client / "tests/unit/test_api.py"
    test.write_text(
        'import pytest\n@pytest.mark.verifies("REQ-SVC-01")\ndef test_retired(): pass\n'
    )
    view = Workspace.open(client).assessment()
    assert any(g.code == "G07" and g.item.endswith("test_retired") for g in view.gaps)
    report = client / "results.xml"
    report.write_text(
        '<testsuite><testcase classname="tests.unit.test_api" name="test_retired"/></testsuite>'
    )
    result = Workspace.open(client).results(report)
    assert result.matched_cases == 1
    assert "withdrawn — excluded from coverage" in text.results(result)


def test_no_baselines_does_not_require_git(project, tmp_path):
    root = project / "solo"
    config = root / "qmstrace.toml"
    config.write_text(
        re.sub(r"(?ms)^\[schema.baselines.release\].*?(?=^\[subjects)", "", config.read_text())
    )
    shutil.rmtree(root / ".git")
    assert not Workspace.open(root).assessment().baseline_state.baselines


def test_tag_with_same_named_branch_and_other_subject(controlled):
    git(controlled, "branch", TAG)
    git(controlled, "tag", "baseline/other/requirements/1")
    assessment = Workspace.open(controlled).assessment()
    assert len(assessment.baseline_state.comparisons) == 3
    assert all(c.baseline.label == TAG for c in assessment.baseline_state.comparisons)


def test_unconfigured_register_stays_unverified_in_result_line(controlled):
    config = controlled / "qmstrace.toml"
    source = re.sub(r"(?m)^digest = .*\n", "", config.read_text())
    config.write_text(
        re.sub(r"(?ms)^\[schema.change_requests\].*?(?=^\[schema.baselines)", "", source)
    )
    edit(controlled, citation="- Change: CR-001\n")
    view = Workspace.open(controlled).assessment()
    assert not view.violations
    assert (
        "change requests NOT VERIFIED"
        in text.check(view, strict=False, quiet=True).splitlines()[-1]
    )


def test_an_edit_under_a_sub_heading_of_a_frozen_item_needs_a_request(controlled):
    """Found in user acceptance: `#### Acceptance criteria` once ended the item, so an edit
    under it escaped change control."""
    path = controlled / REQ
    lines = path.read_text().splitlines(keepends=True)
    index = next(n for n, line in enumerate(lines) if "### REQ-SVC-01" in line)
    end = next(n for n in range(index + 1, len(lines)) if lines[n].startswith("#"))
    lines.insert(end, "#### Acceptance criteria\n- A call with no key gets 401.\n\n")
    path.write_text("".join(lines))
    commit(controlled, "criteria")
    git(controlled, "tag", "-a", "baseline/service/requirements/2", "-m", "criteria approved")
    assert not codes(controlled)
    path.write_text(path.read_text().replace("gets 401", "gets 403"))
    assert codes(controlled) == {"V10"}
