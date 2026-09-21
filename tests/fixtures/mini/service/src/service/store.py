"""Keeps records on disk.

Implements: DSN-SVC-02
"""

from pathlib import Path


def keep(folder: Path, name: str, record: str) -> None:
    (folder / name).write_text(record, encoding="utf-8")
