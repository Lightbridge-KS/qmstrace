"""What a repo had checked out when a table read it — the commit, and whether its tree was clean.

A tree is clean when nothing under its root is modified, staged, deleted, or new and not
ignored; a change elsewhere in a larger repository does not count. Outside Git, or before the
first commit, there is no commit to name.
"""

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.infra.git import checkout

MakeRepo = Callable[[Path], Path]


@pytest.fixture
def repo(tmp_path: Path, make_repo: MakeRepo) -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text("a\n", encoding="utf-8")
    (root / ".gitignore").write_text("build/\n", encoding="utf-8")
    return make_repo(root)


def test_a_committed_tree_is_clean_and_names_its_commit(repo: Path) -> None:
    found = checkout(repo)
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert found == (head, True)


@pytest.mark.parametrize(
    "change",
    [
        lambda root: (root / "docs" / "a.md").write_text("changed\n", encoding="utf-8"),
        lambda root: (root / "docs" / "new.md").write_text("new\n", encoding="utf-8"),
        lambda root: (root / "docs" / "a.md").unlink(),
    ],
    ids=["modified", "untracked", "deleted"],
)
def test_uncommitted_work_makes_the_tree_unclean(
    repo: Path, change: Callable[[Path], object]
) -> None:
    change(repo)
    found = checkout(repo)
    assert found is not None and found[1] is False


def test_an_ignored_file_leaves_the_tree_clean(repo: Path) -> None:
    (repo / "build").mkdir()
    (repo / "build" / "out.bin").write_bytes(b"x")
    assert checkout(repo) is not None and checkout(repo)[1] is True  # type: ignore[index]


def test_a_root_inside_a_larger_repo_counts_only_its_own_changes(repo: Path) -> None:
    (repo / "elsewhere.md").write_text("outside docs/\n", encoding="utf-8")
    found = checkout(repo / "docs")
    assert found is not None and found[1] is True
    assert checkout(repo) is not None and checkout(repo)[1] is False  # type: ignore[index]


def test_outside_git_or_before_a_commit_there_is_none(tmp_path: Path, git_env: None) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    probe = subprocess.run(["git", "-C", str(plain), "rev-parse"], capture_output=True)
    assert probe.returncode != 0, "the temporary folder is inside a Git work tree"
    assert checkout(plain) is None
    subprocess.run(["git", "-C", str(plain), "init", "-q"], check=True)
    assert checkout(plain) is None
