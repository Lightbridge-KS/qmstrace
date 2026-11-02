"""The trace graph's vocabulary as values: items, links, findings, notices.

An **item** is declared where its content is written; a **link** is declared at its downstream
end and points upstream. A **finding** is what is wrong in the user's repo — always data, never
an exception. A **notice** is what a run could not verify or did not pin: it fails nothing, and
no form of output may hide it.

Implements: DSN-QMT-05, DSN-QMT-14
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Literal

from qmstrace.core.locations import joined
from qmstrace.plugin_api.v1 import (
    ID_IN_TEXT as ID_IN_TEXT,
)
from qmstrace.plugin_api.v1 import (
    ID_TOKEN as ID_TOKEN,
)
from qmstrace.plugin_api.v1 import (
    id_order as id_order,
)
from qmstrace.plugin_api.v1 import (
    id_tokens as id_tokens,
)
from qmstrace.plugin_api.v1 import (
    text_digest as text_digest,
)

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
    kind: str = "docstring"
    item: str | None = None
    guidance: str | None = None


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
