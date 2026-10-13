"""The records describing the trace schema and local declarations.

Implements: DSN-QMT-03
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Final

# The extractors this qmstrace ships, and whether each reads IDs someone wrote — so an ID
# pattern is required — or derives them from a path or a test function, so one is refused.
# `extract/` registers exactly these names; a test keeps the two in step.
EXTRACTORS: Final[Mapping[str, bool]] = {"markdown": True, "python-module": False, "pytest": False}


class SchemaForm(Enum):
    """How a product repo holds the project's trace schema."""

    BY_PATH = "by path"
    VERIFIED_COPY = "a generated, verified copy"
    OWN = "the repo's own"


@dataclass(frozen=True, slots=True)
class ItemType:
    """One kind of item: what the project requires of it, and where this repo declares it."""

    name: str
    required: tuple[str, ...]
    values: Mapping[str, tuple[str, ...]]
    levels: tuple[str, ...]
    extractor: str | None
    id_pattern: re.Pattern[str] | None
    id_prefix: str | None
    files: tuple[str, ...]
    ignore: tuple[str, ...]

    @property
    def declared_here(self) -> bool:
        """Whether this repo scans for items of this type at all."""
        return bool(self.files)

    @property
    def derives_ids(self) -> bool:
        """Whether this repo's extractor derives each ID from where the item is — a module's
        path, a test's node ID — rather than reading one someone wrote."""
        return self.extractor is not None and not EXTRACTORS[self.extractor]

    @property
    def fields(self) -> frozenset[str]:
        """Every field name the project declares for this type."""
        return frozenset(self.required) | frozenset(self.values)


@dataclass(frozen=True, slots=True)
class LinkType:
    """A marker, who may carry it, and what it may point at."""

    marker: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    counts_for_coverage: bool


@dataclass(frozen=True, slots=True)
class CoverageRule:
    """Which link an item type must have; an unmet rule is a gap."""

    code: str
    item_type: str
    direction: str  # "incoming" | "outgoing"
    marker: str
    where: Mapping[str, str]
    text: str


@dataclass(frozen=True, slots=True)
class ExternalSource:
    """Items declared outside any product repo — cited there, declared in the ledger."""

    name: str
    item_type: str
    prefix: str
    source: str
    declared_as: re.Pattern[str]

    def declared_in(self, text: str) -> frozenset[str]:
        """The IDs the source's text declares — one per line that `declared_as` matches."""
        found = (self.declared_as.search(line) for line in text.splitlines())
        return frozenset(match.group(1) for match in found if match)


@dataclass(frozen=True, slots=True)
class ChangeRequests:
    """Where the project's change requests are, and which state licenses a change."""

    prefix: str
    source: str
    accepted: str


@dataclass(frozen=True, slots=True)
class BaselineScope:
    """Which tags are baselines, and which item types each freezes.

    `subject` is `"*"` for every subject, a subject's name, or `None` when the tag pattern
    itself names the subject through a `(?P<subject>…)` group.
    """

    name: str
    tag: re.Pattern[str]
    covers: tuple[str, ...]
    subject: str | None


@dataclass(frozen=True, slots=True)
class Subject:
    """A named body of requirements, and the key inside its item IDs."""

    name: str
    key: str
