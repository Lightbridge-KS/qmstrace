import os
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


# ── a link setup creates, never replaces ────────────────────────────────────────────────────


def test_a_link_is_created_once_and_then_left_alone(tmp_path: Path) -> None:
    (tmp_path / "skill").mkdir()
    edits = {"skill/SKILL.md": "text", "links/skill": files.Link("../skill")}
    assert files.update_files(tmp_path, edits) == (
        "updated: skill/SKILL.md",
        "updated: links/skill",
    )
    assert os.readlink(tmp_path / "links/skill") == "../skill"
    assert (tmp_path / "links/skill/SKILL.md").read_text() == "text"
    assert files.update_files(tmp_path, edits) == (
        "unchanged: skill/SKILL.md",
        "unchanged: links/skill",
    )


def test_a_failed_write_removes_the_links_it_created(tmp_path: Path, monkeypatch) -> None:
    real, calls = os.symlink, []

    def second_fails(target, location):
        calls.append(location)
        if len(calls) == 2:
            raise PermissionError("denied")
        real(target, location)

    monkeypatch.setattr(files.os, "symlink", second_fails)
    edits = {"a": "new", "one/l": files.Link("../a"), "two/l": files.Link("../a")}
    with pytest.raises(CouldNotJudge, match="could not write"):
        files.update_files(tmp_path, edits)
    assert not (tmp_path / "one/l").is_symlink()  # exists() is false for a dangling link
    assert not (tmp_path / "a").exists()


def test_a_destination_under_a_link_is_an_alias(tmp_path: Path) -> None:
    with pytest.raises(CouldNotJudge, match="same file"):
        files.update_files(tmp_path, {"l/SKILL.md": "text", "l": files.Link("skill")})
    assert not os.path.lexists(tmp_path / "l")


def test_a_link_leading_out_of_the_root_is_refused(tmp_path: Path) -> None:
    with pytest.raises(CouldNotJudge, match="lead out"):
        files.update_files(tmp_path, {"a": "text", "l": files.Link("../elsewhere")})
    assert not (tmp_path / "a").exists()
