"""The trace graph's vocabulary as values: items, links, findings, notices.

An **item** is declared where its content is written; a **link** is declared at its downstream
end and points upstream. A **finding** is what is wrong in the user's repo — always data, never
an exception. A **notice** is what a run could not verify or did not pin: it fails nothing, and
no form of output may hide it.

Implements: DSN-QMT-05, DSN-QMT-14
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Final, Literal

from qmstrace.core.locations import joined

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


# One run's identity in a test report: the class and the test's name as the report gives them.
Identity = tuple[str, str]


@dataclass(frozen=True, slots=True)
class Item:
    """One traceable unit, as declared in one file.

    `fields` holds the `Key: value` lines under a document-declared item — the first line of
    each key; `level` is an automated test's level, read from where it sits; `runs_as` is the
    identities its runs carry in a test report — set by a test extractor, and what makes the
    item an automated test whose results `results` reads (ADR-0003).
    """

    id: str
    type: str
    file: str
    line: int
    title: str
    digest: str
    fields: Mapping[str, str] = field(default_factory=dict)
    level: str | None = None
    runs_as: tuple[Identity, ...] = ()


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
class Mention:
    """An ID written where it declares nothing — later in a heading, or as a table row's first
    cell. The graph decides whether it matters: one of this repo's kind that nothing declares
    was likely meant as a declaration (V16)."""

    token: str
    file: str
    line: int
    where: Literal["heading", "row"]


@dataclass(frozen=True, slots=True)
class Stray:
    """A marker written where it is not read — an `Implements:` in a comment, a `Satisfies:`
    line outside every item's section, a `Satisfies` table row. It links nothing; a gap it
    leaves open can say why.

    `item` is the item whose section holds it, when one does — only that item's own gap
    names it. Without one, any item in the file may be the one it was meant for.
    """

    marker: str
    targets: tuple[str, ...]
    file: str
    line: int
    kind: Literal["docstring", "outside", "table", "doccomment", "comment", "razor"] = "docstring"
    item: str | None = None


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
    mentions: tuple[Mention, ...] = ()

    def qualified(self, repo: str, location: str, derived: frozenset[str]) -> Extracted:
        """What this file declares, as the whole project sees it: every location written from
        the ledger (`../service/src/app.py`), and an ID derived from a path qualified by its
        repo (`service:src/app.py`), because two repos may hold the same path. An authored ID
        is the project's already and is never touched — nor is a link's target, which is
        always one.

        Examples
        --------
        ```python
        part = Extracted(items=(Item("src/app.py", "component", "src/app.py", 1, "", ""),))
        part.qualified("service", "../service", frozenset({"component"})).items[0].id
        # 'service:src/app.py'
        ```
        """
        renamed = {i.id: f"{repo}:{i.id}" for i in self.items if i.type in derived}

        def at(file: str) -> str:
            return joined(location, file)

        def named(item_id: str | None) -> str | None:
            return renamed.get(item_id, item_id) if item_id is not None else None

        return Extracted(
            tuple(replace(i, id=renamed.get(i.id, i.id), file=at(i.file)) for i in self.items),
            tuple(replace(k, src=renamed.get(k.src, k.src), file=at(k.file)) for k in self.links),
            tuple(replace(f, file=at(f.file), item=named(f.item)) for f in self.findings),
            tuple(replace(lead, file=at(lead.file)) for lead in self.leads),
            tuple(replace(s, file=at(s.file), item=named(s.item)) for s in self.strays),
            tuple(replace(m, file=at(m.file)) for m in self.mentions),
        )
