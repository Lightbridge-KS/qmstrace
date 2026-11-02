"""Stable, text-only language extraction API, major version 1.

No filesystem, configuration, graph or workspace objects cross this boundary.
Fields are immutable key/value pairs. Locations use the request's POSIX path label.

Implements: DSN-QMT-17
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Final, Literal

# What an item ID looks like, whatever the project's own patterns: capitals and digits in
# hyphenated parts, ending in a number, where a number may carry dotted parts — REQ-SVC-01,
# DSN-BCN-08, AGR-3, CR-001, TC-SVC-04.1-01. A project's patterns decide which of these are
# *its* items; this decides what reads as an ID at all (ADR-0002).
ID_TOKEN: Final = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.\d+)*)*-\d+(?:\.\d+)*")
# An ID in running text, bounded on both sides: `TC-SVC-03.1a` is no ID at all — never
# `TC-SVC-03` — and the full stop that ends a sentence is not part of the ID before it.
ID_IN_TEXT: Final = re.compile(rf"(?<![A-Za-z0-9-])({ID_TOKEN.pattern})(?![A-Za-z0-9-]|\.\d)")


def id_tokens(text: str) -> tuple[str, ...]:
    """Every whole ID in running text, in order — an ID is read whole or not at all."""
    return tuple(found.group(1) for found in ID_IN_TEXT.finditer(text))


def id_order(item_id: str) -> tuple[tuple[str | int, ...], str]:
    """Sort key for any ID, a repo-qualified one included: each run of digits compares as a
    number, so AGR-2 comes before AGR-10, TC-4.2 before TC-4.10 and REQ-SVC-02 before
    REQ-SVC-10. The ID itself breaks ties."""
    parts = re.split(r"(\d+)", item_id)
    return tuple(int(p) if i % 2 else p for i, p in enumerate(parts)), item_id


def text_digest(text: str) -> str:
    """The digest of an item's text, with layout ignored.

    Every run of whitespace — line breaks included — counts as one space, and the text is
    normalised to NFC first, so re-wrapping a paragraph or saving it with other line endings is
    not a change. The algorithm is part of the value: it becomes a format once a trace lock
    records it.

    Examples
    --------
    ```python
    text_digest("one\\ntwo") == text_digest("one   two")    # True
    text_digest("one two").startswith("sha256:")           # True
    ```
    """
    normal = " ".join(unicodedata.normalize("NFC", text).split())
    return "sha256:" + hashlib.sha256(normal.encode("utf-8")).hexdigest()


Identity = tuple[str, str]


@dataclass(frozen=True, slots=True)
class ExtractRequest:
    """Source and the schema facts an extractor may read; never a filesystem handle."""

    text: str
    path: str
    item_type: str
    levels: tuple[str, ...] = ()
    markers: tuple[str, ...] = ()
    permitted_markers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    type: str
    file: str
    line: int
    title: str
    digest: str
    fields: tuple[tuple[str, str], ...] = ()
    level: str | None = None
    runs_as: tuple[Identity, ...] = ()


@dataclass(frozen=True, slots=True)
class Link:
    src: str
    dst: str
    marker: str
    file: str
    line: int


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """Source problems, mapped to host finding codes; never plugin execution failures."""

    kind: Literal["parse", "missing-level", "invalid-id", "unread-marker"]
    file: str
    line: int
    what: str
    next_move: str
    item: str | None = None
    marker: str | None = None
    target: str | None = None


@dataclass(frozen=True, slots=True)
class Stray:
    """Unread marker and language-owned correction.

    Guidance uses {location} as a literal placeholder. The host replaces it after
    qualifying paths for a project assessment. No other interpolation is performed.
    """

    marker: str
    targets: tuple[str, ...]
    file: str
    line: int
    guidance: str
    item: str | None = None
    kind: str = "plugin"


@dataclass(frozen=True, slots=True)
class Extraction:
    items: tuple[Item, ...] = ()
    links: tuple[Link, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    strays: tuple[Stray, ...] = ()
