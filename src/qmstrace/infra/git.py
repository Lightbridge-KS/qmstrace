"""Git, asked in its own terms — the one place qmstrace runs the `git` command.

Every call runs in the directory it asks about, with the variables that would point Git at
some other repository removed: inside a hook, `GIT_INDEX_FILE` or `GIT_DIR` would otherwise make
a sibling's listing read this repo's index.
"""

from __future__ import annotations

import os
import posixpath
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Final, Never, Protocol

from qmstrace.core.baselines import Tag
from qmstrace.core.errors import CouldNotJudge

_REDIRECTS: Final = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
    }
)


def working_files(root: Path) -> tuple[str, ...] | None:
    """The files a commit here could carry — tracked, or untracked and not ignored.

    Paths are relative to `root`, even when `root` is a folder inside a larger repository.
    `None` when `root` is not inside a Git work tree, or Git is not installed.
    """
    probe = _git(root, "rev-parse", "--is-inside-work-tree")
    if probe is None or probe.returncode != 0 or probe.stdout.strip() != b"true":
        return None
    listed = _git(
        root, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--deduplicate"
    )
    if listed is None or listed.returncode != 0:
        detail = listed.stderr.decode("utf-8", "replace").strip() if listed else "git vanished"
        raise CouldNotJudge(
            f"Git could not list the files in {root}: {detail}.",
            "Fix: run 'git status' there and repair what it reports, then run again.",
        )
    names = listed.stdout.decode("utf-8", "surrogateescape").split("\0")
    return tuple(name for name in names if name)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    env = {key: value for key, value in os.environ.items() if key not in _REDIRECTS}
    env["GIT_NO_LAZY_FETCH"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        return subprocess.run(
            ["git", "-c", "protocol.allow=never", *args],
            cwd=root,
            env=env,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return None


class IGit(Protocol):
    """Git facts needed by a historical tree and the workspace."""

    def state(self) -> str: ...
    def tags_reachable_from_head(self) -> tuple[Tag, ...]: ...
    def is_ancestor(self, older: str, newer: str) -> bool: ...
    def list_files(self, rev: str) -> tuple[str, ...]: ...
    def read_files(self, rev: str, paths: Iterable[str]) -> dict[str, bytes]: ...


class GitCli:
    """Read local Git objects without checkout, fetch, or user configuration redirects."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.prefix = self._run("rev-parse", "--show-prefix").decode().strip()

    def state(self) -> str:
        """Require usable history, returning HEAD's immutable commit ID."""
        if self._run("rev-parse", "--is-shallow-repository").strip() == b"true":
            raise CouldNotJudge(
                "Baselines cannot be judged in a shallow repository.",
                "Fix: obtain full history and tags, then run again; qmstrace never fetches.",
            )
        options = self._run("config", "--get-regexp", r"^remote\..*\.(tagopt|fetch)$", empty=1)
        if any(
            line.endswith(" --no-tags") or " ^refs/tags/" in line
            for line in options.decode().splitlines()
        ):
            raise CouldNotJudge(
                "Git configuration explicitly excludes tags; baseline evidence is incomplete.",
                "Fix: remove the tag exclusion and obtain the required tags, then run again.",
            )
        return self._run("rev-parse", "--verify", "HEAD^{commit}").decode().strip()

    def tags_reachable_from_head(self) -> tuple[Tag, ...]:
        raw = self._run(
            "for-each-ref",
            "--merged=HEAD",
            "--sort=refname",
            "--format=%(refname:lstrip=2)%00%(objecttype)%00%(taggername)%00%(taggerdate:iso-strict)",
            "refs/tags/",
        )
        found: list[Tag] = []
        for line in raw.decode("utf-8").splitlines():
            name, kind, tagger, date = line.split("\0")
            commit = self._run("rev-parse", "--verify", f"refs/tags/{name}^{{commit}}")
            found.append(
                Tag(name, commit.decode().strip(), kind == "tag", tagger or None, date or None)
            )
        return tuple(found)

    def is_ancestor(self, older: str, newer: str) -> bool:
        result = _git(self.root, "merge-base", "--is-ancestor", older, newer)
        if result is not None and result.returncode in (0, 1):
            return result.returncode == 0
        self._failed("establish ancestry")

    def list_files(self, rev: str) -> tuple[str, ...]:
        raw = self._run("ls-tree", "--full-tree", "-r", "--name-only", "-z", rev)
        paths = raw.decode("utf-8", "surrogateescape").split("\0")
        return tuple(
            sorted(p[len(self.prefix) :] for p in paths if p and p.startswith(self.prefix))
        )

    def read_files(self, rev: str, paths: Iterable[str]) -> dict[str, bytes]:
        found = {}
        for path in paths:
            full = posixpath.normpath(self.prefix + path)
            if path.startswith("/") or full == ".." or full.startswith("../"):
                raise CouldNotJudge(
                    f"Historical schema '{path}' is outside the tagged Git tree.",
                    "Fix: future baselines must contain an embedded schema or a schema file "
                    "in the same Git tree. Do not substitute today's ledger or rewrite old tags.",
                )
            found[path] = self._run("show", f"{rev}:{full}")
        return found

    def _run(self, *args: str, empty: int | None = None) -> bytes:
        result = _git(self.root, *args)
        if result is not None and result.returncode == 0:
            return result.stdout
        if result is not None and result.returncode == empty:
            return b""
        self._failed("read " + " ".join(args))

    @staticmethod
    def _failed(action: str) -> Never:
        raise CouldNotJudge(
            f"Git could not {action}; local baseline evidence is unavailable.",
            "Fix: run git status, check repository history and required objects/tags, then "
            "run again. qmstrace does not fetch missing objects.",
        )
