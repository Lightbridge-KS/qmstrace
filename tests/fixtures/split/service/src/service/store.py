"""Keeps accepted records on disk.

Implements: DSN-SVC-02
"""


def keep(record: bytes, path: str) -> None:
    with open(path, "ab") as file:
        file.write(record)
