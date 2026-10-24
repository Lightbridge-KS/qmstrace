"""Workspace package compatibility and sequencing at the public seam."""

from pathlib import Path

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.infra.git import GitCli
from qmstrace.infra.tree import WorkingTree
from qmstrace.workspace import (
    CONFIG_FILE,
    SCHEMA_FILE,
    TreeFactory,
    Workspace,
    _discovery,
    _workspace,
)


def test_workspace_exports_forward_the_original_objects() -> None:
    assert Workspace is _workspace.Workspace
    assert TreeFactory is _discovery.TreeFactory
    assert CONFIG_FILE is _discovery.CONFIG_FILE
    assert SCHEMA_FILE is _discovery.SCHEMA_FILE


def test_open_keeps_subclass_construction_and_injected_dependencies(project: Path) -> None:
    opened = []

    def trees(root):
        opened.append(root)
        return WorkingTree(root)

    class CustomWorkspace(Workspace):
        pass

    root = project / "service"
    git = GitCli(root)
    workspace = CustomWorkspace.open(root / "src", trees=trees, git=git)
    assert type(workspace) is CustomWorkspace
    assert workspace.trees is trees and workspace.git is git
    assert opened == [root]
    assert workspace.root == root
    assert Workspace.__slots__ == ("root", "tree", "config", "trees", "git", "locations")
    with pytest.raises(AttributeError):
        workspace.root = root / "other"


def test_initialize_dispatches_through_subclass_open(project: Path) -> None:
    opened = []

    class CustomWorkspace(Workspace):
        @classmethod
        def open(cls, start, **kwargs):
            opened.append(start)
            return super().open(start, **kwargs)

    root = project / "service"
    CustomWorkspace.initialize(root / "src")
    assert opened == [root]
    assert (root / "AGENTS.md").is_file()


@pytest.mark.parametrize("command", ["project_thread", "project_impact"])
def test_project_walks_dispatch_once_with_injected_factories(project: Path, command: str) -> None:
    assessment = Workspace.project(project / "ledger")
    calls = []

    class CustomWorkspace(Workspace):
        @classmethod
        def project(cls, start, *, trees=WorkingTree, gits=GitCli):
            calls.append((start, trees, gits))
            return assessment

    def trees(root):
        raise AssertionError("the overridden project owns reads")

    def gits(root):
        raise AssertionError("the overridden project owns Git")

    root = project / "ledger"
    argument = "REQ-SVC-01" if command == "project_thread" else iter(["REQ-SVC-01"])
    assert getattr(CustomWorkspace, command)(root, argument, trees=trees, gits=gits) is assessment
    assert calls == [(root, trees, gits)]
    calls.clear()
    with pytest.raises(CouldNotJudge, match="No starting IDs"):
        CustomWorkspace.project_impact(root, iter(()), trees=trees, gits=gits)
    assert calls == []


@pytest.mark.parametrize("payload", [None, b"<broken>", b"<testsuite/>"])
def test_unusable_reports_are_rejected_before_assessment(project: Path, payload: bytes | None):
    class CustomWorkspace(Workspace):
        def assessment(self):
            raise AssertionError("an unusable report must not assess the tree")

    root = project / "service"
    report = root / "report.xml"
    if payload is not None:
        report.write_bytes(payload)
    with pytest.raises(CouldNotJudge):
        CustomWorkspace.open(root).results(report)


def test_report_bytes_are_read_before_assessment(project: Path) -> None:
    root = project / "service"
    report = root / "report.xml"
    report.write_bytes((Path(__file__).parents[1] / "fixtures/junit/service.xml").read_bytes())
    expected = Workspace.open(root).results(report)
    calls = []

    class CustomWorkspace(Workspace):
        def assessment(self):
            calls.append(self.root)
            report.unlink()
            return super().assessment()

    assert CustomWorkspace.open(root).results(report) == expected
    assert calls == [root]
