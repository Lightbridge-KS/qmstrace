"""Suspects against real tagged trees, including historical validation and source evidence."""

import re
import subprocess

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.render import text
from qmstrace.workspace import Workspace

TAG = "baseline/service/requirements/1"
REQ = "docs/req/service-srs.md"
DESIGN = "docs/design/service-design.md"
TEST = "tests/unit/test_keys.py"


def git(root, *args):
    return (
        subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE).decode().strip()
    )


def pin(root, tag=TAG):
    git(root, "add", "-A")
    git(root, "commit", "-qm", "snapshot")
    git(root, "tag", "-a", tag, "-m", "approved")


@pytest.fixture
def suspect_repo(project, embed):
    root = project / "service"
    config = root / "qmstrace.toml"
    config.write_text(
        embed(config.read_text(), (project / "ledger/qmstrace.schema.toml").read_text())
    )
    pin(root)
    return root


def change(root):
    file = root / REQ
    file.write_text(file.read_text().replace("A call carries a key", "A call requires a fresh key"))


def values(root):
    return {s.item.id: s for s in Workspace.open(root).assessment().suspects}


def test_item_digests_comments_new_tests_and_passing_reports_do_not_clear(suspect_repo):
    root = suspect_repo
    change(root)
    first = values(root)
    assert len(first) == 7  # both designs/components, and three existing tests
    test = root / TEST
    test.write_text(test.read_text() + "\n# unrelated comment\ndef test_unrelated(): pass\n")
    second = values(root)
    assert first.keys() == second.keys()
    assert all(not r.edited for s in second.values() for r in s.reasons)
    test.write_text(test.read_text().replace("assert", "assert True or", 1))
    third = values(root)
    assert first.keys() == third.keys()
    assert any(r.edited for s in third.values() for r in s.reasons)
    report = root / "report.xml"
    report.write_text(
        '<testsuite><testcase classname="tests.unit.test_keys" '
        'name="test_a_call_without_a_valid_key_is_refused"/></testsuite>'
    )
    view = Workspace.open(root).results(report)
    assert {s.item.id for s in view.assessment.suspects} == first.keys()


def test_removed_links_deleted_roots_and_missing_dependants(suspect_repo):
    root = suspect_repo
    change(root)
    before = values(root)
    file = root / DESIGN
    file.write_text(file.read_text().replace("Satisfies: REQ-SVC-01", ""))
    after = values(root)
    assert after.keys() == before.keys()
    assert after["DSN-SVC-01"].reasons[0].current_distance is None
    srs = root / REQ
    source = srs.read_text()
    start, end = source.index("### REQ-SVC-01"), source.index("### REQ-SVC-02")
    srs.write_text(source[:start] + source[end:])
    (root / TEST).unlink()
    assessment = Workspace.open(root).assessment()
    assert "V13" in {v.code for v in assessment.violations}
    assert all(s.item.file != TEST for s in assessment.suspects)
    assert all(r.root_state == "removed" for s in assessment.suspects for r in s.reasons)


def test_withdrawal_and_reactivation_preserve_review(suspect_repo):
    root = suspect_repo
    change(root)
    file = root / DESIGN
    file.write_text(
        file.read_text().replace(
            "## DSN-SVC-01 — Key check", "## DSN-SVC-01 — Key check\nStatus: withdrawn"
        )
    )
    view = Workspace.open(root).assessment()
    assert "[withdrawn]" in text.check(view, strict=False, quiet=True)
    assert len(view.suspects) == 7
    file.write_text(file.read_text().replace("Status: withdrawn", "Status: active"))
    assert len(values(root)) == 7


def test_new_baseline_clears_its_chain(suspect_repo):
    change(suspect_repo)
    assert values(suspect_repo)
    pin(suspect_repo, "baseline/service/requirements/2")
    assert not values(suspect_repo)


def test_config_pattern_change_does_not_hide_surviving_historical_dependency(suspect_repo):
    root = suspect_repo
    change(root)
    config = root / "qmstrace.toml"
    config.write_text(config.read_text().replace("docs/design/*.md", "architecture/*.md"))
    (root / "architecture").mkdir()
    (root / DESIGN).rename(root / "architecture/design.md")
    found = values(root)
    assert found["DSN-SVC-01"].item.file == "architecture/design.md"
    assert not found["DSN-SVC-01"].reasons[0].edited


@pytest.mark.parametrize("bad_link", ["REQ-SVC-99", "AGR-1"])
def test_historical_local_graph_defects_name_tag_and_finding(suspect_repo, bad_link):
    root = suspect_repo
    file = root / DESIGN
    file.write_text(file.read_text().replace("REQ-SVC-01", bad_link))
    pin(root, "baseline/service/requirements/2")
    with pytest.raises(CouldNotJudge, match="baseline/service/requirements/2") as error:
        Workspace.open(root).assessment()
    assert ("V03" if bad_link == "REQ-SVC-99" else "V04") in str(error.value)


def test_historical_boundaries_never_read_current_sources(suspect_repo):
    root = suspect_repo
    change(root)
    # Today's agreement invalidates citations today, but cannot invalidate the tagged graph.
    agreement = root.parent / "ledger/agreement.md"
    agreement.write_text("# No clauses remain\n")
    view = Workspace.open(root).assessment()
    assert any(f.code == "V09" for f in view.violations)
    assert len(view.suspects) == 7
    assert any("historical external/sibling citations NOT VERIFIED" in n.text for n in view.notices)
    assert all(s.item.file.startswith(("docs/", "src/", "tests/")) for s in view.suspects)


def test_same_commit_scopes_scan_once_and_keep_aliases(suspect_repo, monkeypatch):
    import qmstrace.workspace as workspace
    from qmstrace.infra.tree import GitTree

    git(suspect_repo, "tag", "baseline/service/requirements/2")
    git(suspect_repo, "tag", "v1.0.0")
    change(suspect_repo)
    scanned = []
    original = workspace._scan

    def scan(tree, *args, **kwargs):
        if isinstance(tree, GitTree):
            scanned.append(tree)
        return original(tree, *args, **kwargs)

    monkeypatch.setattr(workspace, "_scan", scan)
    view = Workspace.open(suspect_repo).assessment()
    assert len(scanned) == 1
    assert len(view.suspects) == 7
    assert all(len(s.reasons) == 1 and len(s.reasons[0].baseline.tags) == 3 for s in view.suspects)


def test_renamed_current_types_do_not_reinterpret_historical_schema(suspect_repo):
    change(suspect_repo)
    config = suspect_repo / "qmstrace.toml"
    config.write_text(
        re.sub(
            r"(?m)^(?:digest = |# qmstrace:(?:begin|end)).*\n",
            "",
            config.read_text().replace("design_element", "design"),
        )
    )
    found = values(suspect_repo)
    assert len(found) == 7
    assert found["DSN-SVC-01"].item.type == "design"
    assert (
        found["DSN-SVC-01"].reasons[0].baseline.snapshot.graph.nodes["DSN-SVC-01"].type
        == "design_element"
    )


def test_downstream_only_baseline_does_not_clear_upstream_chain(suspect_repo):
    root = suspect_repo
    change(root)
    before = values(root)
    config = root / "qmstrace.toml"
    config.write_text(
        re.sub(
            r"(?m)^(?:digest = |# qmstrace:(?:begin|end)).*\n",
            "",
            config.read_text().replace(
                'covers  = ["requirement", "design_element"]', 'covers  = ["design_element"]'
            ),
        )
    )
    # Its historical and current release scope both cover only designs.
    pin(root, "v1.0.0")
    view = Workspace.open(root).assessment()
    assert {s.item.id for s in view.suspects} == before.keys()
    assert all(r.baseline.label == TAG for s in view.suspects for r in s.reasons)


def test_unavailable_sibling_and_external_remain_snapshot_boundaries(suspect_repo):
    root = suspect_repo
    design = root / DESIGN
    design.write_text(
        design.read_text().replace("Assumes: DSN-SVC-01", "Assumes: DSN-SVC-01, REQ-CLT-01")
    )
    # Assumes accepts requirements and designs in the miniature schema.
    pin(root, "baseline/service/requirements/2")
    change(root)
    (root.parent / "client").rename(root.parent / "client-away")
    (root.parent / "ledger/agreement.md").unlink()
    view = Workspace.open(root).assessment()
    assert len(view.suspects) == 7
    historical = view.baseline_state.baselines[0].snapshot.graph
    assert historical.nodes["REQ-CLT-01"].item is None
    output = text.check(view, strict=False, quiet=True)
    assert "NOT VERIFIED" in output and "historical external/sibling citations" in output
    assert all(s.item.id != "REQ-CLT-01" for s in view.suspects)
