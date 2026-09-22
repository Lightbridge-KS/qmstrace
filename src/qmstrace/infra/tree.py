"""The source tree — the seam that matters: the same scan reads any tree.

Today there is one: the working tree. A tree at a baseline tag joins it when baselines are
judged; the extractors never know which one they read, because they are handed text.
"""

from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import Final, Protocol

from qmstrace.infra import git

# Folders a walk outside Git never enters: tool state, caches, installed packages.
_PRUNED: Final = frozenset({"__pycache__", "node_modules"})


class ISourceTree(Protocol):
    """A set of files, and their text."""

    @property
    def label(self) -> str:
        """What this tree is, as a reader of the output needs to know it."""
        ...

    def files(self) -> tuple[str, ...]:
        """Every file, as a sorted repo-relative POSIX path."""
        ...

    def read(self, path: str) -> str:
        """A file's text. Raises `UnicodeDecodeError` when it is not UTF-8."""
        ...


class WorkingTree:
    """The files on disk under a root, as a commit there could carry them.

    Inside a Git work tree, that is what Git lists — tracked, or untracked and not ignored — so
    an ignored note that quotes an item heading is never read. Outside Git, every file under the
    root is read, but for hidden folders, caches and installed packages; the label says so.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    @property
    def label(self) -> str:
        if self._listing is None:
            return "not a Git repository — every file under it was read, not pinned"
        return "working tree, not pinned"

    def files(self) -> tuple[str, ...]:
        found = self._listing if self._listing is not None else _walk(self.root)
        return tuple(sorted(p for p in found if (self.root / p).is_file()))

    def read(self, path: str) -> str:
        return (self.root / path).read_bytes().decode("utf-8-sig")

    @cached_property
    def _listing(self) -> tuple[str, ...] | None:
        return git.working_files(self.root)


class GitTree:
    """An immutable revision, using the same paths and decoding as WorkingTree."""

    def __init__(self, source: git.IGit, rev: str) -> None:
        self.source = source
        self.rev = rev
        self._texts: dict[str, str] = {}

    @property
    def label(self) -> str:
        return f"Git tree {self.rev}"

    def files(self) -> tuple[str, ...]:
        return self._files

    def read(self, path: str) -> str:
        if path not in self._texts:
            self._texts[path] = self.source.read_files(self.rev, (path,))[path].decode("utf-8-sig")
        return self._texts[path]

    @cached_property
    def _files(self) -> tuple[str, ...]:
        return self.source.list_files(self.rev)


def _walk(root: Path) -> list[str]:
    found: list[str] = []
    for folder, subfolders, names in os.walk(root):
        subfolders[:] = [s for s in subfolders if not s.startswith(".") and s not in _PRUNED]
        base = Path(folder).relative_to(root)
        found += [(base / name).as_posix() for name in names]
    return found
