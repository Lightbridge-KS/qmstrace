"""Graph node ownership and the evidence visible outside a repo.

Implements: DSN-QMT-05, DSN-QMT-14
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from qmstrace.core.model import Item


class Home(Enum):
    """Where a node of the graph is declared."""

    LOCAL = "this repo"
    SIBLING = "a sibling repo, read from its working tree, not pinned"
    EXTERNAL = "outside any product repo"
    UNVERIFIED = "not verified here — judged at the ledger's import"


@dataclass(frozen=True, slots=True)
class Node:
    """One end of a link. `item` is set for the items this run judges — one repo's own, or in
    the project's graph every repo's; `repo` names a sibling or an external source, and in the
    project's graph the repo of every judged item. `title` and `where` are for display —
    `where` is a path as the reader would write it. `fields` retains authored metadata for
    judged and sibling nodes, including verification methods, without treating a sibling's
    items as judged ones."""

    id: str
    home: Home
    type: str | None
    item: Item | None = None
    repo: str | None = None
    title: str | None = None
    where: str | None = None
    fields: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Surroundings:
    """What lies outside this repo, as this run could read it.

    `siblings` maps each sibling that was read to the items it declares with authored IDs, their
    files already written as a reader of this repo would write them (`../service/…`).
    `every_sibling_read` is false when a sibling was not reachable, or when the project's other
    repos could not be located at all. `externals` maps an external source's name to the IDs it
    declares — or to `None` when the source could not be reached.
    """

    siblings: Mapping[str, Mapping[str, Item]] = field(default_factory=dict)
    every_sibling_read: bool = True
    externals: Mapping[str, frozenset[str] | None] = field(default_factory=dict)
    whole_project: bool = False  # every repo of the project is read — the ledger's check
