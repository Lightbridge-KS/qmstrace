"""Inventory and check projections of already judged assessments.

Implements: DSN-QMT-12
"""

from collections import Counter

from qmstrace.core.assessment import Assessment
from qmstrace.core.judge import test_backed_requirement
from qmstrace.render.json._common import (
    View,
    baselines,
    counts,
    finding,
    location,
    node,
    scanned,
    suspect,
)


def check(value: View, *, strict: bool) -> dict[str, object]:
    result: dict[str, object] = {
        "project": value.config.project,
        "counts": counts(value),
        "strict": strict,
        "violations": [finding(f, value.config.repo) for f in value.violations],
        "gaps": [finding(f, value.config.repo) for f in value.gaps],
        "suspects": [suspect(s, value.config.repo) for s in value.suspects],
    }
    if isinstance(value, Assessment):
        result["baselines"] = baselines(value.baseline_state)
    else:
        result["repos"] = [
            {
                "name": r.name,
                "location": location(r.location),
                "baselines": baselines(r.baseline_state),
            }
            for r in value.repos
        ]
    return result


def status(value: Assessment) -> dict[str, object]:
    graph = value.graph
    requirements = []
    for item in graph.items("requirement"):
        requirements.append(
            {
                **node(graph.nodes[item.id]),
                "method": item.fields.get("Verify-by") or "unspecified",
                "test_backed": test_backed_requirement(value.config, item.fields),
                "incoming": [
                    {"source": k.src, "marker": k.marker} for k in graph.incoming(item.id)
                ],
                "outgoing": [
                    {"target": k.dst, "marker": k.marker} for k in graph.outgoing(item.id)
                ],
            }
        )
    return {
        "project": value.config.project,
        "tree": value.tree_label,
        "counts": counts(value),
        "scanned": scanned(value.scanned),
        "requirements": requirements,
        "sources": {
            "externals": [
                {
                    "name": s.name,
                    "prefix": s.prefix,
                    "location": location(s.location),
                    "declared": s.declared,
                }
                for s in value.externals
            ],
            "siblings": [
                {
                    "name": s.name,
                    "location": location(s.location),
                    "declares": dict(s.declares) if s.declares is not None else None,
                    "problem": s.problem,
                }
                for s in value.siblings
            ],
            "siblings_located": value.siblings_located,
        },
        "baselines": baselines(value.baseline_state),
        "suspects": {
            "total": len(value.suspects),
            "distance_one": [
                suspect(s, value.config.repo) for s in value.suspects if s.distance == 1
            ],
            "farther": [
                {"distance": distance, "count": number}
                for distance, number in sorted(
                    Counter(s.distance for s in value.suspects if s.distance > 1).items()
                )
            ],
        },
    }
