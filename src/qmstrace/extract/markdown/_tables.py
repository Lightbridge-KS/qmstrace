"""Table cells and misplaced link markers; rows never declare items or links.

Implements: DSN-QMT-04
"""

from __future__ import annotations

import re
from typing import Final

from qmstrace.core.model import ID_TOKEN
from qmstrace.extract.fields import FIELD

_DELIMITER: Final = re.compile(r":?-+:?")  # a table's header rule, `|---|:--:|`
_CELL_MARKS: Final = re.compile(r"[*_`\[\]]")  # emphasis, code and link marks in a cell


def _cells(raw: str) -> list[str] | None:
    """A table row's cells — none for a header rule — or `None` when the line is no row."""
    line = raw.strip()
    if not line.startswith("|"):
        return None
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    return [] if all(_DELIMITER.fullmatch(cell) for cell in cells) else cells


def _table_marker(cells: list[str], carried: set[str]) -> tuple[str, tuple[str, ...]] | None:
    """A link marker written as a table row — `| Satisfies | IDs |` or `| Satisfies: IDs |` —
    with the IDs it names; `None` when the row names no marker this type carries, or no ID."""
    if not cells:
        return None
    first = _CELL_MARKS.sub("", cells[0]).strip()
    rest = " ".join(cells[1:])
    written = FIELD.match(first)
    if written is not None and written.group(1) in carried and written.group(2):
        marker, rest = written.group(1), written.group(2) + " " + rest
    elif first.rstrip(":").strip() in carried:
        marker = first.rstrip(":").strip()
    else:
        return None
    targets = tuple(ID_TOKEN.findall(rest))
    return (marker, targets) if targets else None
