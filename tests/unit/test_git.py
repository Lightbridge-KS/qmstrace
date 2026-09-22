"""Git metadata stays stable across Git versions without losing timezone evidence."""

from unittest.mock import Mock

import pytest

from qmstrace.infra.git import GitCli


@pytest.mark.parametrize(
    "kind,date,expected",
    [
        ("tag", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00+00:00"),
        ("tag", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        ("tag", "2026-01-01T07:00:00+07:00", "2026-01-01T07:00:00+07:00"),
        ("commit", "", None),
    ],
)
def test_tag_date_normalization(tmp_path, monkeypatch, kind, date, expected):
    commit = "a" * 40
    raw = f"v1\0{kind}\0\0{date}\n".encode()
    monkeypatch.setattr(GitCli, "_run", Mock(side_effect=[b"", raw, commit.encode()]))
    (tag,) = GitCli(tmp_path).tags_reachable_from_head()
    assert tag.date == expected
    assert tag.commit == commit
    assert tag.annotated is (kind == "tag")
