"""Shared test machinery.

The fixture project `tests/fixtures/mini/` is plain files. Unit tests read its configurations
as text; integration tests copy it into a temporary directory and make real Git repositories.
"""

import os
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.core.config import TraceConfig, schema_digest

# The fixture project holds product repos with test files of their own. They are data for the
# engine to read, never tests for this suite to collect.
collect_ignore_glob = ["fixtures/*"]

MINI = Path(__file__).parent / "fixtures" / "mini"


def mini_text(*parts: str) -> str:
    return MINI.joinpath(*parts).read_text(encoding="utf-8")


def _embed(local: str, schema: str, *, digest: str | None = None) -> str:
    head, _, tables = schema.partition("\n[")
    tables = re.sub(r"(?m)^\[\[(.+?)\]\]", r"[[schema.\1]]", "[" + tables)
    tables = re.sub(r"(?m)^\[(?!\[)(.+?)\]", r"[schema.\1]", tables)
    stated = digest or schema_digest(tomllib.loads(schema))
    copy = f'[schema]\ndigest = "{stated}"\n{head}\n{tables}'
    # a function, not a string: the schema text holds backslashes that re.sub would read as escapes
    return re.sub(r"(?ms)^\[schema\][^\n]*\n.*?(?=^\[subjects)", lambda _: copy + "\n", local)


@pytest.fixture(scope="session")
def embed() -> Callable[..., str]:
    """Turn a by-path configuration into one that carries a copy of the schema — what the
    ledger side will generate in slice 2; this is its prototype."""
    return _embed


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


@pytest.fixture
def project(tmp_path: Path, git_env: None) -> Path:
    """The fixture project copied into a temporary folder — ledger, service, client and solo
    side by side, each a real Git repository. Returns the folder that holds them."""
    base = tmp_path / "work"
    shutil.copytree(MINI, base)
    for repo in sorted(base.iterdir()):
        _make_repo(repo)
    return base


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
