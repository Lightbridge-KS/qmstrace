"""The one glob matcher, for every tree.

The stand-in had two matchers that disagreed about `src/**/*.py`. This one is the standard
library's: `**` matches zero or more whole segments, `*` never crosses a `/`, and case counts.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath


def matches(path: str, patterns: Iterable[str]) -> bool:
    """Whether a repo-relative POSIX path matches any of the patterns.

    Examples
    --------
    ```python
    matches("src/app.py", ["src/**/*.py"])            # True — ** may match nothing
    matches("docs/req/sub/x-srs.md", ["docs/req/*-srs.md"])   # False — * stays in one folder
    ```
    """
    pure = PurePosixPath(path)
    return any(pure.full_match(pattern) for pattern in patterns)
