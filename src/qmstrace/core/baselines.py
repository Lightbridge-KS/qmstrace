"""Frozen evidence used by baseline resolution and change control; no IO."""

from __future__ import annotations

from dataclasses import dataclass

from qmstrace.core.config import TraceConfig
from qmstrace.core.graph import TraceGraph
from qmstrace.core.model import Finding, Item


@dataclass(frozen=True, slots=True)
class Tag:
    name: str
    commit: str
    annotated: bool
    tagger: str | None = None
    date: str | None = None


@dataclass(frozen=True, slots=True)
class Snapshot:
    commit: str
    config: TraceConfig | None
    items: tuple[Item, ...] = ()
    graph: TraceGraph | None = None


@dataclass(frozen=True, slots=True)
class Baseline:
    scope: str
    subject: str
    covers: tuple[str, ...]
    tags: tuple[Tag, ...]
    snapshot: Snapshot

    @property
    def label(self) -> str:
        return ", ".join(t.name for t in self.tags)


@dataclass(frozen=True, slots=True)
class ChangeRequest:
    id: str
    file: str
    state: str
    impacts: frozenset[str]


@dataclass(frozen=True, slots=True)
class Register:
    location: str | None = None
    available: bool = False
    accepted: str | None = None
    requests: tuple[ChangeRequest, ...] = ()
    findings: tuple[Finding, ...] = ()


@dataclass(frozen=True, slots=True)
class Comparison:
    id: str
    baseline: Baseline
    before: Item | None
    after: Item | None
    state: str  # frozen | changed | new | removed
    fresh: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BaselineState:
    baselines: tuple[Baseline, ...] = ()
    comparisons: tuple[Comparison, ...] = ()
    register: Register = Register()


@dataclass(frozen=True, slots=True)
class SuspectReason:
    root: str
    baseline: Baseline
    root_state: str
    root_withdrawn: bool
    edited: bool
    historical_distance: int | None
    current_distance: int | None

    @property
    def distance(self) -> int:
        return min(d for d in (self.historical_distance, self.current_distance) if d is not None)


@dataclass(frozen=True, slots=True)
class Suspect:
    item: Item
    reasons: tuple[SuspectReason, ...]

    @property
    def distance(self) -> int:
        return min(reason.distance for reason in self.reasons)
