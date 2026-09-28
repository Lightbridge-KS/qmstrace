from pathlib import Path

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.infra import files


def test_failed_setup_rolls_back(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "first").write_text("old")
    replace = files._replace

    def fail(path, content):
        if path.name == "second":
            raise PermissionError("denied")
        replace(path, content)

    monkeypatch.setattr(files, "_replace", fail)
    with pytest.raises(CouldNotJudge, match="could not write"):
        files.update_files(tmp_path, {"first": "new", "second": "new"})
    assert (tmp_path / "first").read_text() == "old"
    assert not (tmp_path / "second").exists()


def test_setup_aliases_and_unreadable_destinations_fail_before_writes(tmp_path: Path) -> None:
    (tmp_path / "a").write_text("old")
    (tmp_path / "b").symlink_to("a")
    with pytest.raises(CouldNotJudge, match="same file"):
        files.update_files(tmp_path, {"a": "one", "b": "two"})
    (tmp_path / "dir").mkdir()
    with pytest.raises(CouldNotJudge, match="inspect"):
        files.update_files(tmp_path, {"a": "new", "dir": "new"})
    assert (tmp_path / "a").read_text() == "old"


def test_a_failure_in_the_second_repo_restores_the_first(tmp_path: Path, monkeypatch) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    one.mkdir()
    two.mkdir()
    (one / "qmstrace.toml").write_text("old one")
    (two / "qmstrace.toml").write_text("old two")
    replace = files._replace

    def fail(path, content):
        if path.parent == two:
            raise PermissionError("denied")
        replace(path, content)

    monkeypatch.setattr(files, "_replace", fail)
    with pytest.raises(CouldNotJudge, match="could not write"):
        files.update_in({one: {"qmstrace.toml": "new"}, two: {"qmstrace.toml": "new"}})
    assert (one / "qmstrace.toml").read_text() == "old one"
    assert (two / "qmstrace.toml").read_text() == "old two"


def test_several_repos_report_each_file(tmp_path: Path) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    one.mkdir()
    two.mkdir()
    (one / "f").write_text("same")
    done = files.update_in({one: {"f": "same"}, two: {"f": "new"}})
    assert done == {one: ("unchanged: f",), two: ("updated: f",)}
    assert (two / "f").read_text() == "new"
