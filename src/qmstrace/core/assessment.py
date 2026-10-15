"""What one run found — the whole of it, as data, for a command to render.

A command is: open the workspace → take its assessment → render → exit. Nothing here is
computed on the way out; the renderer only arranges it. A product repo's run gives an
`Assessment`; the ledger's check of the whole project gives a `ProjectAssessment`.

Implements: DSN-QMT-02, DSN-QMT-14
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from qmstrace.core.baselines import BaselineState, Register, Suspect
from qmstrace.core.config import TraceConfig
from qmstrace.core.graph import TraceGraph
from qmstrace.core.model import Finding, Notice


@dataclass(frozen=True, slots=True)
class Scanned:
    """What was read for one item type — so an empty result never looks like a
    misconfiguration."""

    item_type: str
    patterns: tuple[str, ...]
    ignore: tuple[str, ...]
    files: int
    items: int
    ignored: int


@dataclass(frozen=True, slots=True)
class ExternalState:
    """An external source as this run saw it. `declared` is `None` when it was not reached;
    `location` is `None` when there is no ledger to look in."""

    name: str
    prefix: str
    location: str | None
    declared: int | None


@dataclass(frozen=True, slots=True)
class SiblingState:
    """A sibling repo as this run saw it: what it declares, or why it could not be read."""

    name: str
    location: str
    declares: Mapping[str, int] | None
    problem: str | None = None


@dataclass(frozen=True, slots=True)
class Assessment:
    """Everything a product repo's command can say about it."""

    config: TraceConfig
    tree_label: str
    schema_location: str | None
    scanned: tuple[Scanned, ...]
    graph: TraceGraph
    violations: tuple[Finding, ...]
    gaps: tuple[Finding, ...]
    externals: tuple[ExternalState, ...]
    siblings: tuple[SiblingState, ...]
    siblings_located: bool
    notices: tuple[Notice, ...]
    baseline_state: BaselineState = field(default_factory=BaselineState)
    suspects: tuple[Suspect, ...] = ()

    def fails(self, *, strict: bool) -> bool:
        """Whether the check fails: on any violation, and — under the gate — on any gap too."""
        return bool(self.violations) or (strict and bool(self.gaps))


@dataclass(frozen=True, slots=True)
class Checkout:
    """What a repo had checked out when it was read: its commit, and whether its working tree
    was clean. A table records it, so a reader knows which inputs it came from (ADR-0005)."""

    commit: str
    clean: bool


@dataclass(frozen=True, slots=True)
class RepoState:
    """One repo of the project as the ledger's check read it: where it is, from the ledger;
    what was scanned in it; its baselines."""

    name: str
    location: str
    tree_label: str
    scanned: tuple[Scanned, ...]
    baseline_state: BaselineState = field(default_factory=BaselineState)
    checkout: Checkout | None = None  # None outside Git


@dataclass(frozen=True, slots=True)
class ProjectAssessment:
    """Everything `qmstrace ledger check` can say about the project: every repo in [repos]
    read from its working tree, and judged as one graph. `config` is the ledger's schema — the
    rules every repo holds."""

    config: TraceConfig
    repos: tuple[RepoState, ...]
    graph: TraceGraph
    violations: tuple[Finding, ...]
    gaps: tuple[Finding, ...]
    externals: tuple[ExternalState, ...]
    register: Register
    notices: tuple[Notice, ...]
    suspects: tuple[Suspect, ...] = ()
    ledger: Checkout | None = None  # the ledger's own checkout, whether or not it is in [repos]

    def fails(self, *, strict: bool) -> bool:
        """Whether the check fails: on any violation, and — under the gate — on any gap too."""
        return bool(self.violations) or (strict and bool(self.gaps))
