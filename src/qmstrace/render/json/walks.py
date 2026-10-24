"""Reach projections use the same validated graph walks as text output.

Implements: DSN-QMT-12
"""

from collections.abc import Iterable

from qmstrace.core.graph import Closure
from qmstrace.render.json._common import View, link, node


def _walk(value: Closure, repo: str | None = None) -> list[dict[str, object]]:
    return [
        {
            "id": s.node.id,
            "distance": s.distance,
            "parent": value.parent(s),
            "via": link(s.via, repo),
            "also": [link(k, repo) for k in s.also],
        }
        for s in value.steps.values()
    ]


def thread(value: View, item_id: str) -> dict[str, object]:
    graph = value.graph
    forward, backward = graph.forward([item_id]), graph.backward([item_id])
    ids = {item_id, *forward.steps, *backward.steps}
    return {
        "project": value.config.project,
        "start": item_id,
        "items": [node(graph.nodes[i]) for i in sorted(ids)],
        "forward": _walk(forward, value.config.repo),
        "backward": _walk(backward, value.config.repo),
    }


def impact(value: View, item_ids: Iterable[str]) -> dict[str, object]:
    graph, config = value.graph, value.config
    starts = set(item_ids)
    forward, backward = graph.forward(starts), graph.backward(starts)
    downstream = set(forward.steps) - starts
    external_types = {s.item_type for s in config.externals.values()}
    origins = sorted(
        i
        for i, step in backward.steps.items()
        if i not in starts
        and step.node.type in external_types
        and (
            step.via.marker not in config.links or config.links[step.via.marker].counts_for_coverage
        )
    )
    covered = {kind for b in config.baselines.values() for kind in b.covers}
    candidates = sorted(i for i in starts | downstream if graph.nodes[i].type in covered)
    order = list(config.item_types)
    kinds = {graph.nodes[i].type for i in downstream}
    return {
        "project": config.project,
        "starts": sorted(starts),
        "items": [node(graph.nodes[i]) for i in sorted(starts | downstream | set(origins))],
        "downstream": [
            {"type": kind, "ids": sorted(i for i in downstream if graph.nodes[i].type == kind)}
            for kind in sorted(
                kinds, key=lambda k: (order.index(k) if k in order else len(order), k or "")
            )
        ],
        "origins": origins,
        "forward": _walk(forward, value.config.repo),
        "candidate_ids": candidates,
        "candidate_line": "Impacts: " + ", ".join(candidates) if candidates else None,
        "candidate_empty_reason": None
        if candidates
        else "no-baseline-types"
        if not covered
        else "no-covered-items",
        "unknown_types": sorted(i for i in starts | downstream if graph.nodes[i].type is None),
    }
