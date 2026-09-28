"""The working tree — what a scan may read, against real Git in a scrubbed environment.

The load-bearing claims, each pinned by a test:

1. Inside Git, the files are what a commit could carry: tracked, and untracked but not
   ignored. An ignored note is never read; a file deleted but still in the index is not listed.
2. Paths are relative to the root, even when the root is a folder inside a repository.
3. A variable that points Git elsewhere — as inside a hook — does not change what is listed.
4. Outside Git, or without Git installed, every file under the root is read, but for hidden
   folders, caches and installed packages — and the label says so.
5. Text is UTF-8, a byte-order mark dropped; anything else is an error for the caller.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.infra.tree import WorkingTree

MakeRepo = Callable[[Path], Path]


def write(path: Path, text: str = "x\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path: Path, make_repo: MakeRepo) -> Path:
    root = tmp_path / "repo"
    write(root / "docs" / "req" / "a-srs.md")
    write(root / "src" / "app.py")
    write(root / ".gitignore", "_playground/\n*.log\n")
    write(root / "_playground" / "2026-09-21_x" / "NOTES.md", "### REQ-SVC-01 — quoted\n")
    return make_repo(root)


@pytest.mark.verifies("REQ-QMT-11")
def test_inside_git_the_files_are_what_a_commit_could_carry(repo: Path) -> None:
    write(repo / "docs" / "new.md")  # untracked, not ignored
    write(repo / "debug.log")  # ignored
    tree = WorkingTree(repo)
    assert tree.files() == (".gitignore", "docs/new.md", "docs/req/a-srs.md", "src/app.py")
    assert tree.label == "working tree, not pinned"


@pytest.mark.verifies("DSN-QMT-10")
def test_a_file_deleted_but_still_in_the_index_is_not_listed(repo: Path) -> None:
    (repo / "src" / "app.py").unlink()
    assert "src/app.py" not in WorkingTree(repo).files()


def test_paths_are_relative_to_a_root_inside_a_repository(repo: Path) -> None:
    assert WorkingTree(repo / "docs").files() == ("req/a-srs.md",)


@pytest.mark.verifies("DSN-QMT-10", "REQ-QMT-11")
def test_a_variable_pointing_git_elsewhere_changes_nothing(
    repo: Path, tmp_path: Path, make_repo: MakeRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = make_repo(write(tmp_path / "other" / "only.md").parent)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(other / ".git" / "index"))
    tree = WorkingTree(repo)
    assert tree.files() == (".gitignore", "docs/req/a-srs.md", "src/app.py")
    assert tree.label == "working tree, not pinned"


@pytest.mark.verifies("DSN-QMT-10")
def test_outside_git_every_file_is_read_but_hidden_folders_and_caches(tmp_path: Path) -> None:
    root = tmp_path / "plain"
    for name in ["docs/a.md", ".venv/lib/x.py", "src/__pycache__/x.pyc", "node_modules/p/i.js"]:
        write(root / name)
    tree = WorkingTree(root)
    assert tree.files() == ("docs/a.md",)
    assert tree.label.startswith("not a Git repository")


def test_without_git_installed_the_tree_is_walked(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "")
    tree = WorkingTree(repo)
    assert "_playground/2026-09-21_x/NOTES.md" in tree.files()  # nothing says it is ignored
    assert tree.label.startswith("not a Git repository")


def test_text_is_utf8_with_a_byte_order_mark_dropped(tmp_path: Path) -> None:
    (tmp_path / "bom.md").write_bytes("﻿# Title\n".encode())
    (tmp_path / "latin.md").write_bytes("caf\xe9\n".encode("latin-1"))
    tree = WorkingTree(tmp_path)
    assert tree.read("bom.md") == "# Title\n"
    with pytest.raises(UnicodeDecodeError):
        tree.read("latin.md")
