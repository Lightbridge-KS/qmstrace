"""Workspace-map values and pure membership validation, independent of trace rules.

Implements: DSN-QMT-02
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Set
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from qmstrace.core.errors import CouldNotJudge


def _invalid(file: str, problem: str) -> CouldNotJudge:
    return CouldNotJudge(
        f"Workspace map {file}: {problem}.",
        "Fix: correct the workspace map; it supplies checkout locations, not trace rules.",
    )


@dataclass(frozen=True, slots=True)
class WorkspaceMap:
    """One complete location source; paths have not yet been anchored on disk."""

    project: str
    ledger_repo: str
    repos: Mapping[str, str]

    @classmethod
    def parse(cls, text: str, file: str) -> WorkspaceMap:
        try:
            raw = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise _invalid(file, f"invalid TOML: {exc}") from None
        extra = sorted(set(raw) - {"version", "project", "ledger_repo", "repos"})
        if extra:
            raise _invalid(file, f"unknown field '{extra[0]}'")
        if type(raw.get("version")) is not int or raw["version"] != 1:
            raise _invalid(file, "'version' must be the supported integer 1")
        for key in ("project", "ledger_repo"):
            if not isinstance(raw.get(key), str) or not raw[key].strip():
                raise _invalid(file, f"'{key}' must be a non-empty string")
        repos = raw.get("repos")
        if not isinstance(repos, dict) or not repos:
            raise _invalid(file, "'repos' must be a non-empty table")
        for name, value in repos.items():
            if not name.strip() or not isinstance(value, str) or not value.strip():
                raise _invalid(file, f"'repos.{name}' must be a non-empty path string")
        if raw["ledger_repo"] not in repos:
            raise _invalid(file, "'ledger_repo' must name an entry in [repos]")
        return cls(raw["project"], raw["ledger_repo"], MappingProxyType(repos))

    def validate(
        self, project: str, members: Set[str], roots: Mapping[str, Path], current: Path, file: str
    ) -> None:
        """Validate canonical roots supplied by infrastructure; never inspect the disk."""
        if self.project != project:
            raise _invalid(file, f"project {self.project!r} does not match {project!r}")
        unknown = sorted(set(self.repos) - members - {self.ledger_repo})
        if unknown:
            raise _invalid(file, f"unknown project member(s): {', '.join(unknown)}")
        self.validate_roots(roots, file)
        seen = {path: name for name, path in roots.items()}
        if current not in seen:
            raise _invalid(file, "the current trace root is not bound by this map")
        if seen[current] not in members and seen[current] != self.ledger_repo:
            raise _invalid(file, "the current checkout is not a project member")

    def validate_roots(self, roots: Mapping[str, Path], file: str) -> None:
        """Reject aliases independently of a project's current checkout binding."""
        seen: dict[Path, str] = {}
        for name, path in sorted(roots.items()):
            if path in seen:
                raise _invalid(file, f"{seen[path]} and {name} resolve to the same trace root")
            seen[path] = name


@dataclass(frozen=True, slots=True)
class Locations:
    """A selected map's canonical operational roots and portable provenance."""

    source: str
    filename: str
    ledger: Path
    roots: Mapping[str, Path]

    @property
    def notice(self) -> str:
        return (
            f"workspace: {self.source} map {self.filename} — mapped checkout locations; "
            "tracked ledger pointer and ledger-relative repo defaults not used"
        )


@dataclass(frozen=True, slots=True)
class LocationState:
    name: str
    location: str | None
    available: bool
    current: bool = False


@dataclass(frozen=True, slots=True)
class Paths:
    project: str
    source: str
    ledger: str | None
    repos: tuple[LocationState, ...]
    ledger_available: bool = False
    workspace_source: str | None = None
    workspace_filename: str | None = None
