"""Workspace maps supply locations only; validation never reads the filesystem."""

from pathlib import Path

import pytest

from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.locations import WorkspaceMap

MAP = """version = 1
project = "MINI"
ledger_repo = "ledger"
[repos]
ledger = "../ledger"
service = "."
"""


@pytest.fixture(autouse=True)
def isolated_locations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("QMSTRACE_WORKSPACE", raising=False)


@pytest.mark.verifies("DSN-QMT-02")
def test_map_preserves_native_paths_and_does_not_expose_mutable_repos() -> None:
    spec = WorkspaceMap.parse(MAP, "workspace.toml")
    assert (spec.project, spec.ledger_repo, dict(spec.repos)) == (
        "MINI",
        "ledger",
        {"ledger": "../ledger", "service": "."},
    )
    with pytest.raises(TypeError):
        spec.repos["client"] = "../client"  # type: ignore[index]


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        ("version = 1", "version = true", "version"),
        ("version = 1", "version = 1.0", "version"),
        ("version = 1", 'version = "1"', "version"),
        ("version = 1", "version = 2", "version"),
        ("version = 1", "", "version"),
        ('project = "MINI"', "", "project"),
        ('project = "MINI"', 'project = " "', "project"),
        ('project = "MINI"', "project = 42", "project"),
        ('ledger_repo = "ledger"', "", "ledger_repo"),
        ('ledger_repo = "ledger"', 'ledger_repo = ""', "ledger_repo"),
        ('ledger_repo = "ledger"', "ledger_repo = []", "ledger_repo"),
        ('ledger_repo = "ledger"', 'ledger_repo = "missing"', "ledger_repo"),
        ('ledger = "../ledger"', 'ledger = ""', "repos.ledger"),
        ('ledger = "../ledger"', 'ledger = "  "', "repos.ledger"),
        ('ledger = "../ledger"', "ledger = false", "repos.ledger"),
        ('ledger = "../ledger"', 'ledger = { path = "../ledger" }', "repos.ledger"),
        ('service = "."', '" " = "."', "repos."),
        (MAP, MAP.split("[repos]")[0], "repos"),
        (MAP, MAP.split("[repos]")[0] + "[repos]\n", "repos"),
        ("version = 1", "version = = 1", "TOML"),
        ("version = 1", "version = 1\nversion = 1", "TOML"),
    ],
)
@pytest.mark.verifies("DSN-QMT-02")
def test_map_refuses_malformed_or_wrongly_typed_fields(old: str, new: str, problem: str) -> None:
    with pytest.raises(CouldNotJudge) as stopped:
        WorkspaceMap.parse(MAP.replace(old, new), "chosen.toml")
    assert "chosen.toml" in stopped.value.what
    assert problem in stopped.value.what
    assert stopped.value.next_move.startswith("Fix:")


@pytest.mark.parametrize(
    "extra",
    [
        'ledger = "../other"',
        'schema = "rules.toml"',
        'root = "."',
        'workspace = "other.toml"',
        '[rules]\nG01 = "disabled"',
        '[schema]\npath = "other.toml"',
    ],
)
@pytest.mark.verifies("DSN-QMT-02")
def test_map_rejects_unknown_keys_and_configuration_aliases(extra: str) -> None:
    # Put scalars before [repos], and tables after it, so these are top-level keys.
    text = MAP + extra if extra.startswith("[") else extra + "\n" + MAP
    with pytest.raises(CouldNotJudge, match="unknown field"):
        WorkspaceMap.parse(text, "workspace.toml")


@pytest.mark.verifies("DSN-QMT-02")
def test_partial_map_and_untraced_ledger_are_valid_without_existing_directories(
    tmp_path: Path,
) -> None:
    spec = WorkspaceMap.parse(MAP, "workspace.toml")
    roots = {"ledger": tmp_path / "not-created-ledger", "service": tmp_path / "not-created"}
    spec.validate("MINI", {"service", "client"}, roots, roots["service"], "workspace.toml")
    spec.validate("MINI", {"service", "client"}, roots, roots["ledger"], "workspace.toml")
    assert not any(path.exists() for path in roots.values())
    assert "client" not in spec.repos


@pytest.mark.parametrize("problem", ["project", "current", "member", "alias"])
@pytest.mark.verifies("DSN-QMT-02")
def test_binding_refuses_wrong_project_current_unknown_member_and_canonical_aliases(
    tmp_path: Path, problem: str
) -> None:
    spec = WorkspaceMap.parse(MAP, "workspace.toml")
    roots = {"ledger": tmp_path / "ledger", "service": tmp_path / "service"}
    project, members, current = "MINI", {"service", "client"}, roots["service"]
    expected = {
        "project": "does not match",
        "current": "current trace root",
        "member": "unknown project member",
        "alias": "same trace root",
    }
    if problem == "project":
        project = "OTHER"
    elif problem == "current":
        current = tmp_path / "elsewhere"
    elif problem == "member":
        members = {"client"}
    else:
        roots["ledger"] = roots["service"]
    with pytest.raises(CouldNotJudge, match=expected[problem]):
        spec.validate(project, members, roots, current, "workspace.toml")
