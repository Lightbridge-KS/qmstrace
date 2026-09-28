"""Explicit outputs and reversible setup edits, separate from Git-filtered source reads."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

from qmstrace.core.errors import CouldNotJudge


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


def update_files(root: Path, edits: Mapping[str, str]) -> tuple[str, ...]:
    """Validate every destination first; restore earlier files if a write fails."""
    return update_in({root: edits})[root]


def update_in(changes: Mapping[Path, Mapping[str, str]]) -> dict[Path, tuple[str, ...]]:
    """Several repos' files as one change: every destination in every root is validated
    first, and a failed write restores every file already written — in any root."""
    paths = {
        (root, name): contained(root, name) for root, edits in changes.items() for name in edits
    }
    if len(set(paths.values())) != len(paths):
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
    wanted = {(root, name): changes[root][name].encode("utf-8") for root, name in paths}
    changed = [key for key in paths if original[key] != wanted[key]]
    applied: list[tuple[Path, str]] = []
    try:
        for key in changed:
            _replace(paths[key], wanted[key])
            applied.append(key)
    except OSError as exc:
        failed = []
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
    return {
        root: tuple(
            f"{'updated' if (root, name) in changed else 'unchanged'}: {name}" for name in edits
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
