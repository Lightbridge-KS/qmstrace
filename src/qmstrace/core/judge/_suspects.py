"""Suspect judgment over separate historical and current graph walks.

Implements: DSN-QMT-08, DSN-QMT-14
"""

from __future__ import annotations

from collections.abc import Iterable

from qmstrace.core.baselines import Comparison, Suspect, SuspectReason
from qmstrace.core.graph import TraceGraph


def suspects(graph: TraceGraph, comparisons: Iterable[Comparison]) -> tuple[Suspect, ...]:
    """Existing local dependants reached independently in each root's two graph versions.

    A reason always uses its upstream root's governing snapshot. A new dependant is
    traversed but not reported; a different root may have an older snapshot, so existence
    and edited state are evaluated per reason, never globally.
    """
    current = {item.id: item for item in graph.items()}
    repo_of = {node.id: node.repo for node in graph.nodes.values() if node.item is not None}
    reasons: dict[str, list[SuspectReason]] = {}
    for comparison in sorted(comparisons, key=lambda c: (c.id, c.baseline.snapshot.commit)):
        if comparison.state not in {"changed", "removed"}:
            continue
        snapshot = comparison.baseline.snapshot
        assert snapshot.graph is not None, "suspect judgment requires a validated snapshot graph"
        old = {item.id: item for item in snapshot.graph.items()}
        historical = snapshot.graph.forward([comparison.id]).steps
        present = graph.forward([comparison.id]).steps if comparison.id in current else {}
        root = comparison.after or comparison.before
        assert root is not None
        withdrawn = root.fields.get("Status") == "withdrawn"
        for item_id in sorted((historical.keys() | present.keys()) & current.keys()):
            if item_id == comparison.id:
                continue  # a cycle cannot make its own root suspect
            elsewhere = repo_of.get(item_id)
            if snapshot.repo is not None and elsewhere not in (None, snapshot.repo):
                # Another repo than the root's: no version of it at that baseline was read, so
                # only today's reach counts, and whether it was edited since is not known.
                if item_id in present:
                    reasons.setdefault(item_id, []).append(
                        SuspectReason(
                            comparison.id,
                            comparison.baseline,
                            comparison.state,
                            withdrawn,
                            None,
                            None,
                            present[item_id].distance,
                            unpinned_repo=elsewhere,
                        )
                    )
                continue
            if item_id not in old:
                continue  # a new dependant is traversed but not reported
            reasons.setdefault(item_id, []).append(
                SuspectReason(
                    comparison.id,
                    comparison.baseline,
                    comparison.state,
                    withdrawn,
                    current[item_id].digest != old[item_id].digest,
                    historical[item_id].distance if item_id in historical else None,
                    present[item_id].distance if item_id in present else None,
                )
            )
    return tuple(
        sorted(
            (Suspect(current[item_id], tuple(found)) for item_id, found in reasons.items()),
            key=lambda suspect: (suspect.distance, suspect.item.id),
        )
    )
