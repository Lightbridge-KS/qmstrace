"""Read request files without interpreting their metadata.

Implements: DSN-QMT-07
"""

from pathlib import Path


def request_files(directory: Path, prefix: str) -> dict[str, str | None] | None:
    """None means the directory is unavailable; a None value means one file is unreadable."""
    try:
        paths = sorted(directory.iterdir())
    except OSError:
        return None
    result: dict[str, str | None] = {}
    for path in paths:
        if path.name.startswith(prefix) and path.suffix == ".md":
            try:
                result[path.name] = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError):
                result[path.name] = None
    return result
