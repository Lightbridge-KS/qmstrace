"""Git, asked in its own terms — the one place qmstrace runs the `git` command.

Every call runs in the directory it asks about, with the variables that would point Git at
some other repository removed: inside a hook, `GIT_INDEX_FILE` or `GIT_DIR` would otherwise make
a sibling's listing read this repo's index.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Final

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
    try:
        return subprocess.run(["git", *args], cwd=root, env=env, capture_output=True, check=False)
    except FileNotFoundError:
        return None
