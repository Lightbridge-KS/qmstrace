"""Shared test machinery.

The fixture project `tests/fixtures/mini/` is plain files. Unit tests read its configurations
as text; integration tests copy it into a temporary directory and make real Git repositories.
"""

import os
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.core import setup
from qmstrace.core.config import TraceConfig

# The fixture project holds product repos with test files of their own. They are data for the
# engine to read, never tests for this suite to collect.
collect_ignore_glob = ["fixtures/*"]

MINI = Path(__file__).parent / "fixtures" / "mini"
SPLIT = Path(__file__).parent / "fixtures" / "split"
CASES = Path(__file__).parent / "fixtures" / "cases"


@pytest.fixture(autouse=True)
def isolated_workspace_discovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """No test borrows a developer's map or environment selector."""
    monkeypatch.delenv("QMSTRACE_WORKSPACE", raising=False)
    for key in ("NO_COLOR", "FORCE_COLOR", "PY_COLORS", "GITHUB_ACTIONS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    home = tmp_path_factory.getbasetemp() / "workspace-home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))


def mini_text(*parts: str) -> str:
    return MINI.joinpath(*parts).read_text(encoding="utf-8")


def _embed(local: str, schema: str) -> str:
    """The configuration with the project's schema copied in — by the production transform,
    exactly as `qmstrace ledger copy-schema` writes it."""
    block = setup.schema_block(schema, str(tomllib.loads(schema)["project"]))
    return setup.copy_schema(local, setup.held_schema(local), block)


@pytest.fixture(scope="session")
def embed() -> Callable[..., str]:
    """Turn a by-path configuration into one that carries a generated, verified copy of the
    project's schema."""
    return _embed


@pytest.fixture(scope="session")
def commands() -> list[str]:
    """Every registered command, by the name a user types — groups included."""
    from typer.main import get_command

    from qmstrace.cli import app

    group = get_command(app)
    return sorted(getattr(group, "commands", {}))


@pytest.fixture(scope="session")
def subcommands() -> dict[str, list[str]]:
    """Every group's verbs, by the words a user types — `ledger` → `copy-schema`."""
    from typer.main import get_command

    from qmstrace.cli import app

    group = get_command(app)
    return {
        name: sorted(getattr(command, "commands", {}))
        for name, command in sorted(getattr(group, "commands", {}).items())
        if getattr(command, "commands", None)
    }


@pytest.fixture(scope="session")
def golden() -> Callable[[Path, str], None]:
    """Compare text with a committed golden file. `QMSTRACE_REGOLD=1` rewrites the file instead —
    read the diff before committing it."""

    def check(path: Path, text: str) -> None:
        if os.environ.get("QMSTRACE_REGOLD"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        assert text == path.read_text(encoding="utf-8"), f"{path.name} differs from its golden"

    return check


@pytest.fixture(scope="session")
def service() -> TraceConfig:
    """The `service` repo's configuration, merged with the project's trace schema."""
    return TraceConfig.parse(
        mini_text("service", "qmstrace.toml"), mini_text("ledger", "qmstrace.schema.toml")
    )


# ── real Git repositories, in a scrubbed environment ───────────────────────────────────────


@pytest.fixture
def git_env(monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory) -> None:
    """Git that reads no one's configuration and signs every commit with a fixed identity."""
    home = tmp_path_factory.mktemp("home")
    for key, value in {
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
    }.items():
        monkeypatch.setenv(key, value)


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return done.stdout


def _make_repo(path: Path) -> Path:
    _git(path, "init", "-q", "-b", "main")
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "fixture")
    return path


@pytest.fixture
def make_repo(git_env: None) -> Callable[[Path], Path]:
    """Make a folder a Git repository with everything in it committed."""
    return _make_repo


def _copied(source: Path, base: Path) -> Path:
    """A fixture project copied into `base`, every top-level folder a real Git repository —
    hidden folders, such as an editor's or an agent harness's state, and the `bin/` and `obj/`
    a .NET build or an editor leaves in the C# fixture, left out."""
    shutil.copytree(source, base, ignore=shutil.ignore_patterns(".*", "bin", "obj"))
    for repo in sorted(base.iterdir()):
        _make_repo(repo)
    return base


@pytest.fixture
def project(tmp_path: Path, git_env: None) -> Path:
    """The fixture project copied into a temporary folder — ledger, service, client and solo
    side by side, each a real Git repository. Returns the folder that holds them."""
    return _copied(MINI, tmp_path / "work")


@pytest.fixture
def split(tmp_path: Path, git_env: None) -> Path:
    """The fixture project in the layout of ADR-0001 — a traced ledger holding the documents,
    and product repos holding code and tests — copied and made Git repositories. Returns the
    folder that holds them."""
    return _copied(SPLIT, tmp_path / "split")


@pytest.fixture
def cases(tmp_path: Path, git_env: None) -> Path:
    """A project with a Test Specification (ADR-0003): a traced ledger holding the documents and
    the test cases, dotted `TC-SVC-NN.m`, and a service whose automated tests name the test case
    they run — or a requirement directly. Copied and made Git repositories; returns the folder."""
    return _copied(CASES, tmp_path / "cases")


@pytest.fixture
def alone(project: Path, embed: Callable[..., str]) -> Callable[[str], Path]:
    """One repo as a pipeline checks it out: alone, carrying a verified copy of the schema — no
    ledger and no sibling beside it."""

    def checkout(repo: str) -> Path:
        local = (project / repo / "qmstrace.toml").read_text(encoding="utf-8")
        schema = (project / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")
        copy = project.parent / "checkout" / repo
        shutil.copytree(project / repo, copy)
        (copy / "qmstrace.toml").write_text(embed(local, schema), encoding="utf-8")
        return copy

    return checkout
