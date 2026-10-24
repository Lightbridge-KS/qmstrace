"""Explicit public values and the versioned command envelope; no operational roots.

Implements: DSN-QMT-12
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable

from qmstrace.core import findings
from qmstrace.core.assessment import Assessment, ProjectAssessment, Scanned
from qmstrace.core.baselines import Baseline, BaselineState, Suspect
from qmstrace.core.graph import Node
from qmstrace.core.model import Finding, Link
from qmstrace.render._evidence import evidence

FORMAT = "qmstrace.cli/1"
View = Assessment | ProjectAssessment


def document(
    command: str | None,
    scope: str | None,
    code: int,
    data: dict[str, object] | None,
    notices: Iterable[str] = (),
    error: dict[str, object] | None = None,
) -> str:
    return (
        json.dumps(
            {
                "format": FORMAT,
                "command": command,
                "scope": scope,
                "exit_code": code,
                "data": data,
                "notices": list(dict.fromkeys(notices)),
                "error": error,
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def node(value: Node) -> dict[str, object]:
    return {
        "id": value.id,
        "title": value.title,
        "type": value.type,
        "ownership": value.home.name.lower(),
        "repo": value.repo,
        "location": value.where,
        "fields": dict(sorted(value.fields.items())),
        "withdrawn": value.fields.get("Status") == "withdrawn",
    }


def finding(value: Finding) -> dict[str, object]:
    return {
        "code": value.code,
        "location": {"path": value.file, "line": value.line},
        "message": value.what,
        "next_move": value.next_move,
        "item": value.item,
        "marker": value.marker,
        "target": value.target,
    }


def link(value: Link) -> dict[str, object]:
    return {
        "source": value.src,
        "target": value.dst,
        "marker": value.marker,
        "location": {"path": value.file, "line": value.line},
    }


def scanned(values: Iterable[Scanned]) -> list[dict[str, object]]:
    return [
        {
            "type": s.item_type,
            "patterns": list(s.patterns),
            "ignore": list(s.ignore),
            "files": s.files,
            "items": s.items,
            "ignored": s.ignored,
        }
        for s in values
    ]


def baseline(value: Baseline) -> dict[str, object]:
    return {
        "scope": value.scope,
        "subject": value.subject,
        "covers": list(value.covers),
        "commit": value.snapshot.commit,
        "tags": [
            {"name": t.name, "annotated": t.annotated, "tagger": t.tagger, "date": t.date}
            for t in value.tags
        ],
    }


def baseline_ref(value: Baseline) -> dict[str, object]:
    return {
        "scope": value.scope,
        "subject": value.subject,
        "commit": value.snapshot.commit,
        "tags": [t.name for t in value.tags],
    }


def baselines(value: BaselineState) -> dict[str, object]:
    counts = Counter(c.state for c in value.comparisons)
    return {
        "counts": {
            "frozen": sum(c.before is not None for c in value.comparisons),
            "changed": counts["changed"],
            "new": counts["new"],
            "removed": counts["removed"],
        },
        "governing": [baseline(b) for b in value.baselines],
        "comparisons": [
            {
                "id": c.id,
                "state": c.state,
                "baseline": baseline_ref(c.baseline),
                "fresh_citations": list(c.fresh),
            }
            for c in value.comparisons
        ],
        "register": {
            "location": value.register.location,
            "available": value.register.available,
            "accepted": value.register.accepted,
        },
    }


def suspect(value: Suspect) -> dict[str, object]:
    return {
        **finding(findings.suspect(value)),
        "id": value.item.id,
        "title": value.item.title,
        "location": {"path": value.item.file, "line": value.item.line},
        "withdrawn": value.item.fields.get("Status") == "withdrawn",
        "distance": value.distance,
        "reasons": [
            {
                "root": r.root,
                "root_state": r.root_state,
                "root_withdrawn": r.root_withdrawn,
                "baseline": baseline_ref(r.baseline),
                "edited": r.edited,
                "historical_distance": r.historical_distance,
                "current_distance": r.current_distance,
                "unpinned_repo": r.unpinned_repo,
            }
            for r in value.reasons
        ],
    }


def counts(value: View) -> dict[str, object]:
    return {
        "items": len(value.graph.items()),
        "links": len(value.graph.links),
        "violations": len(value.violations),
        "gaps": len(value.gaps),
        "suspects": len(value.suspects),
        "withdrawn": sum(
            n.fields.get("Status") == "withdrawn"
            for n in value.graph.nodes.values()
            if n.item is not None
        ),
    }


def notices(value: View) -> list[str]:
    if isinstance(value, Assessment):
        result = list(evidence(value))
    else:
        result = [n.text for n in value.notices]
        result += [
            f"external {s.prefix}*: NOT VERIFIED — source unavailable"
            for s in value.externals
            if s.declared is None
        ]
        result += [
            "Project assessment reads working trees, not pins.",
            "Suspects need review; edits and passing tests do not record review.",
        ]
        if value.config.baselines:
            result.append("Remote-tag completeness NOT VERIFIED; reachable local tags only.")
        if value.config.change_requests and not value.register.available:
            result.append("Change requests NOT VERIFIED — register unavailable.")
    if value.violations:
        result.append("Violations are present; refused links are excluded from graph reach.")
    return list(dict.fromkeys(result))
