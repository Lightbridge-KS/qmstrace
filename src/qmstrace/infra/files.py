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
    paths = {name: contained(root, name) for name in edits}
    if len(set(paths.values())) != len(paths):
        raise CouldNotJudge(
            "Setup targets resolve to the same file.", "Fix: give each managed file its own path."
        )
    try:
        original = {
            name: path.read_bytes() if path.exists() else None for name, path in paths.items()
        }
    except OSError as exc:
        raise CouldNotJudge(
            f"Cannot inspect setup destinations: {exc}", "Fix: restore readable regular files."
        ) from exc
    changed = [name for name in edits if original[name] != edits[name].encode("utf-8")]
    applied: list[str] = []
    try:
        for name in changed:
            _replace(paths[name], edits[name].encode("utf-8"))
            applied.append(name)
    except OSError as exc:
        failed = []
        for name in reversed(applied):
            try:
                old = original[name]
                if old is None:
                    paths[name].unlink()
                else:
                    _replace(paths[name], old)
            except OSError:
                failed.append(name)
        raise CouldNotJudge(
            f"Setup could not write files: {exc}",
            "Fix: restore these files from version control: " + ", ".join(failed)
            if failed
            else "Fix: check destination permissions; previous files were restored.",
        ) from exc
    return tuple(f"{'updated' if name in changed else 'unchanged'}: {name}" for name in edits)


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
