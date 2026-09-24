"""An offline presentation of one assessment; all reach comes from the shared core."""

from __future__ import annotations

import json
from html import escape
from importlib.resources import files

from qmstrace.core import findings
from qmstrace.core.assessment import Assessment
from qmstrace.render.text import evidence


def projection(assessment: Assessment, selected: str | None = None) -> dict[str, object]:
    """Project stable display values and precomputed reach; never judge in JavaScript."""
    graph = assessment.graph
    ids = sorted(graph.nodes)
    index = {key: i for i, key in enumerate(ids)}
    types = list(
        dict.fromkeys(
            [
                *(source.item_type for source in assessment.config.externals.values()),
                *assessment.config.item_types,
                *(graph.nodes[key].type or "untyped" for key in ids),
            ]
        )
    )
    comparisons = {c.id: c for c in assessment.baseline_state.comparisons}
    suspect_ids = {s.item.id for s in assessment.suspects}
    nodes = []
    for key in ids:
        node = graph.nodes[key]
        badges = []
        baseline = None
        if comparison := comparisons.get(key):
            if comparison.before is not None:
                badges.append("frozen")
            if comparison.state != "frozen":
                badges.append(comparison.state)
            baseline = comparison.baseline.label
        if node.fields.get("Status") == "withdrawn":
            badges.append("withdrawn")
        if key in suspect_ids:
            badges.append("suspect — needs review")
        nodes.append(
            {
                "id": key,
                "title": node.title or "",
                "type": node.type or "untyped",
                "column": types.index(node.type or "untyped"),
                "home": node.home.value,
                "repo": node.repo,
                "where": node.where,
                "badges": badges,
                "baseline": baseline,
                "fields": dict(sorted(node.fields.items())),
            }
        )
    # Browser selection reads these maps. It never reconstructs a historical/current path.
    reach = [
        {
            direction: [
                [index[key], step.distance]
                for key, step in sorted(walk((item_id,)).steps.items())
                if key != item_id
            ]
            for direction, walk in (("forward", graph.forward), ("backward", graph.backward))
        }
        for item_id in ids
    ]
    found = [
        *assessment.violations,
        *assessment.gaps,
        *(findings.suspect(s) for s in assessment.suspects),
    ]
    links = sorted(set(graph.links), key=lambda k: (k.src, k.dst, k.marker, k.file, k.line))
    return {
        "project": assessment.config.project,
        "selected": selected,
        "types": types,
        "nodes": nodes,
        "links": [
            {
                "src": index[k.src],
                "dst": index[k.dst],
                "marker": k.marker,
                "where": f"{k.file}:{k.line}",
                "dependency": not assessment.config.links[k.marker].counts_for_coverage,
            }
            for k in links
        ],
        "reach": reach,
        "findings": [
            {
                "code": f.code,
                "item": f.item,
                "where": f"{f.file}:{f.line}",
                "what": f.what,
                "next": f.next_move,
            }
            for f in found
        ],
        "evidence": evidence(assessment),
    }


def document(assessment: Assessment, selected: str | None = None) -> str:
    """Embed packaged assets and text-safe JSON; identical input produces identical bytes."""
    assets = files("qmstrace").joinpath("assets")
    payload = json.dumps(
        projection(assessment, selected), ensure_ascii=False, separators=(",", ":")
    )
    for char in "<>&\u2028\u2029":
        payload = payload.replace(char, f"\\u{ord(char):04x}")
    template = assets.joinpath("graph.html").read_text(encoding="utf-8")
    library = assets.joinpath("vendor/vis-network.min.js").read_text(encoding="utf-8")
    # The upstream source-map comment is not needed in a standalone document.
    library = library.split("//# sourceMappingURL=")[0]
    script = assets.joinpath("graph.js").read_text(encoding="utf-8")
    license_text = assets.joinpath("vendor/vis-network-LICENSE").read_text(encoding="utf-8")
    template = template.replace("<!--LICENSE-->", escape(license_text))
    return (
        template.replace("/*LIBRARY*/", library)
        .replace("/*VIEWER*/", script)
        .replace("/*ASSESSMENT*/", payload)
    )
