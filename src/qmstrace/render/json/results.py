"""Public report outcomes, with references instead of repeated test/run subtrees.

Implements: DSN-QMT-12
"""

from qmstrace.core.results import CaseResult, ReportSource, Results, RunResult, TargetResult
from qmstrace.render.json._common import node


def _source(value: ReportSource) -> dict[str, object]:
    return {"label": value.label, "sha256": value.sha256, "repo": value.repo}


def _run(value: RunResult) -> dict[str, object]:
    return {
        "identity": list(value.identity),
        "verdict": value.verdict,
        "entries": value.entries,
        "kinds": list(value.kinds),
        "details": list(value.details),
        "sources": [_source(s) for s in value.sources],
    }


def _target(value: TargetResult) -> dict[str, object]:
    return {
        **node(value.node),
        "method": value.method or "unspecified",
        "verdict": value.verdict,
        "tests": [t.id for t in value.tests],
        "runs": value.runs,
        "via": [c.node.id for c in value.via],
    }


def _case(value: CaseResult) -> dict[str, object]:
    return {
        **node(value.node),
        "verdict": value.verdict,
        "tests": [t.id for t in value.tests],
        "verifies": list(value.verifies),
    }


def results(value: Results) -> dict[str, object]:
    cases = {
        c.node.id: c
        for c in (
            *value.other_cases,
            *(
                c
                for t in (*value.requirements, *value.other_methods, *value.unverified_targets)
                for c in t.via
            ),
        )
    }
    return {
        "project": value.assessment.config.project,
        "counts": {
            "entries": value.entries,
            "runs": value.runs,
            "matched_runs": value.matched_runs,
            "matched_tests": value.matched_cases,
            "scanned_tests": value.scanned_cases,
            "duplicates": value.duplicates,
            "unmatched": len(value.unmatched),
        },
        "reports": [
            {**_source(r.source), "entries": r.entries, "format": r.format} for r in value.reports
        ],
        "requirements": [_target(t) for t in value.requirements],
        "other_methods": [{**_target(t), "evidence_only": True} for t in value.other_methods],
        "unverified_targets": [_target(t) for t in value.unverified_targets],
        "tests": [
            {
                "id": t.id,
                "verdict": t.verdict,
                "verifies": list(t.verifies),
                "runs": [_run(r) for r in t.runs],
            }
            for _, t in sorted(value.tests.items())
        ],
        "cases": [_case(c) for _, c in sorted(cases.items())],
        "other_tests": [t.id for t in value.other_tests],
        "other_cases": [c.node.id for c in value.other_cases],
        "unmatched": [{"run": _run(u.run), "reason": u.reason} for u in value.unmatched],
    }
