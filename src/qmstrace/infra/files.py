"""Explicit outputs and reversible setup edits, separate from Git-filtered source reads.

Implements: DSN-QMT-11, DSN-QMT-13
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from qmstrace.core.errors import CouldNotJudge


@dataclass(frozen=True)
class Link:
    """A symbolic link setup creates and never replaces. `target` is relative to the link's
    folder; an existing link with exactly this target is left alone, anything else there is
    refused."""

    target: str


def read_optional(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else None
    except (OSError, UnicodeError) as exc:
        raise CouldNotJudge(
            f"Cannot read {path}: {exc}", "Fix: restore readable UTF-8 content."
        ) from exc


def contained(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or ".git" in path.relative_to(root.resolve()).parts:
        raise CouldNotJudge(
            f"Setup target {relative} leaves the product directory.",
            "Fix: use a guide and setup files within this repo.",
        )
    return path


def update_files(root: Path, edits: Mapping[str, str | Link]) -> tuple[str, ...]:
    """Validate every destination first; restore earlier files if a write fails."""
    return update_in({root: edits})[root]


def update_in(changes: Mapping[Path, Mapping[str, str | Link]]) -> dict[Path, tuple[str, ...]]:
    """Several repos' files as one change: every destination in every root is validated
    first, and a failed write restores every file already written — in any root. A link is
    created after the files and removed first on failure."""
    texts = {
        (root, name): value
        for root, edits in changes.items()
        for name, value in edits.items()
        if isinstance(value, str)
    }
    links = {
        (root, name): value
        for root, edits in changes.items()
        for name, value in edits.items()
        if isinstance(value, Link)
    }
    paths = {key: contained(*key) for key in texts}
    places = {key: _link_place(*key, link) for key, link in links.items()}
    if len(set(paths.values())) != len(paths) or any(
        path == location or path.is_relative_to(location)
        for path in paths.values()
        for location, _ in places.values()
    ):
        raise CouldNotJudge(
            "Setup targets resolve to the same file.", "Fix: give each managed file its own path."
        )
    try:
        original = {
            key: path.read_bytes() if path.exists() else None for key, path in paths.items()
        }
    except OSError as exc:
        raise CouldNotJudge(
            f"Cannot inspect setup destinations: {exc}", "Fix: restore readable regular files."
        ) from exc
    wanted = {key: value.encode("utf-8") for key, value in texts.items()}
    changed = [key for key in paths if original[key] != wanted[key]]
    created = [key for key, (_, present) in places.items() if not present]
    applied: list[tuple[Path, str]] = []
    linked: list[tuple[Path, str]] = []
    try:
        for key in changed:
            _replace(paths[key], wanted[key])
            applied.append(key)
        for key in created:
            location = places[key][0]
            location.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(links[key].target, location)
            linked.append(key)
    except OSError as exc:
        failed = []
        for key in reversed(linked):
            try:
                places[key][0].unlink()
            except OSError:
                failed.append(str(places[key][0]))
        for key in reversed(applied):
            try:
                old = original[key]
                if old is None:
                    paths[key].unlink()
                else:
                    _replace(paths[key], old)
            except OSError:
                failed.append(str(paths[key]))
        raise CouldNotJudge(
            f"Setup could not write files: {exc}",
            "Fix: restore these files from version control: " + ", ".join(failed)
            if failed
            else "Fix: check destination permissions; previous files were restored.",
        ) from exc
    written = {*changed, *created}
    return {
        root: tuple(
            f"{'updated' if (root, name) in written else 'unchanged'}: {name}" for name in edits
        )
        for root, edits in changes.items()
    }


def write_new(path: Path, content: str) -> None:
    """Never overwrite an existing artifact, including a dangling symlink."""
    try:
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
    except OSError as exc:
        raise CouldNotJudge(
            f"Cannot create {path.name}: {exc.strerror}.",
            "Fix: choose a new output path in an existing writable directory.",
        ) from exc


def _replace(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(content)
        if path.exists():
            os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def _link_place(root: Path, name: str, link: Link) -> tuple[Path, bool]:
    """Where a link goes — its folder resolved, the link itself never followed — and whether
    it is already there."""
    folder_name, _, base = name.rpartition("/")
    folder = contained(root, folder_name) if folder_name else root.resolve()
    if folder.exists() and not folder.is_dir():
        raise _occupied(folder_name)
    if not (folder / link.target).resolve().is_relative_to(root.resolve()):
        raise CouldNotJudge(
            f"Setup link {name} would lead out of the product directory.",
            "Fix: link only to files within this repo.",
        )
    location = folder / base
    if not os.path.lexists(location):
        return location, False
    if location.is_symlink() and os.readlink(location) == link.target:
        return location, True
    raise _occupied(name)


def _occupied(name: str) -> CouldNotJudge:
    return CouldNotJudge(
        f"{name} holds something setup did not write.",
        "Fix: move it aside, then run init again.",
    )
