"""The trace graph's vocabulary as values: items, links, findings, notices.

An **item** is declared where its content is written; a **link** is declared at its downstream
end and points upstream. A **finding** is what is wrong in the user's repo — always data, never
an exception. A **notice** is what a run could not verify or did not pin: it fails nothing, and
no form of output may hide it.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

# What an item ID looks like, whatever the project's own patterns: capitals and digits in
# hyphenated parts, ending in a number — REQ-SVC-01, DSN-BCN-08, AGR-3, CR-001. A project's
# patterns decide which of these are *its* items; this decides what reads as an ID at all.
ID_TOKEN: Final = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+")


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


@dataclass(frozen=True, slots=True)
class Item:
    """One traceable unit, as declared in one file.

    `fields` holds the `Key: value` lines under a document-declared item — the first line of
    each key; `level` is a test case's level, read from where it sits.
    """

    id: str
    type: str
    file: str
    line: int
    title: str
    digest: str
    fields: Mapping[str, str] = field(default_factory=dict)
    level: str | None = None


@dataclass(frozen=True, slots=True)
class Link:
    """A typed, directed relationship, declared at `src` — the downstream end."""

    src: str
    dst: str
    marker: str
    file: str
    line: int


@dataclass(frozen=True, slots=True)
class Lead:
    """A heading that starts with an ID but declares no item of the type being read.

    The graph decides what it is: a sibling's item declared again, a malformed ID of this
    repo's own, or prose.
    """

    token: str
    item_type: str
    file: str
    line: int


@dataclass(frozen=True, slots=True)
class Stray:
    """A marker written where it is not read — an `Implements:` in a comment, say. It links
    nothing; a gap it leaves open can say why."""

    marker: str
    targets: tuple[str, ...]
    file: str
    line: int


@dataclass(frozen=True, slots=True)
class Finding:
    """Something wrong in the user's repo: where, what, and the next move.

    Codes are classed by their first letter — `V` a violation, `G` a gap, `S` a suspect.
    """

    code: str
    file: str
    line: int
    what: str
    next_move: str
    item: str | None = None
    marker: str | None = None  # the link a violation refused, if it concerns one
    target: str | None = None


@dataclass(frozen=True, slots=True)
class Notice:
    """What a run could not verify or did not pin. Never a failure, never hidden."""

    text: str


@dataclass(frozen=True, slots=True)
class Extracted:
    """What one extractor found in one file."""

    items: tuple[Item, ...] = ()
    links: tuple[Link, ...] = ()
    findings: tuple[Finding, ...] = ()
    leads: tuple[Lead, ...] = ()
    strays: tuple[Stray, ...] = ()
