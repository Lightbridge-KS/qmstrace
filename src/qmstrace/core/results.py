"""Report facts matched to scanned tests, then attributed through explicit verifies links.

No history is written. A reported run is one distinct full JUnit identity; duplicate entries
are combined, not treated as proof of additional attempts. Requirement verdicts say only what
this report says about its directly linked tests.

Implements: DSN-QMT-09
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from qmstrace.core.assessment import Assessment
from qmstrace.core.graph import Node

Identity = tuple[str, str]  # classname, name (including parameters for a reported run)
Verdict = Literal["pass", "skip", "no-result", "fail", "untested"]
_RANK = {"untested": 0, "pass": 1, "skip": 2, "no-result": 3, "fail": 4}


@dataclass(frozen=True, slots=True)
class ReportEntry:
    """One testcase element, retaining its full report identity and outcome kind."""

    classname: str
    name: str
    verdict: Verdict
    kinds: tuple[str, ...] = ()
    details: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Report:
    """The reader's entries, or an explanation of why the payload could not be read."""

    entries: tuple[ReportEntry, ...] = ()
    problem: str | None = None


@dataclass(frozen=True, slots=True)
class RunResult:
    """One full report identity, with repeated XML entries combined."""

    identity: Identity
    verdict: Verdict
    entries: int
    kinds: tuple[str, ...]
    details: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TestResult:
    """One scanned test function, its observed runs, and all its explicit targets."""

    id: str
    verdict: Verdict
    runs: tuple[RunResult, ...]
    verifies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TargetResult:
    """A requirement or untyped target and the tests that directly verify it."""

    node: Node
    method: str | None
    verdict: Verdict
    tests: tuple[TestResult, ...]
    runs: int


@dataclass(frozen=True, slots=True)
class UnmatchedRun:
    """An entry identity that cannot be assigned to exactly one scanned test."""

    run: RunResult
    reason: str


@dataclass(frozen=True, slots=True)
class Results:
    """A complete informational view; all judgments are computed before rendering."""

    assessment: Assessment
    report_name: str
    entries: int
    runs: int
    matched_runs: int
    matched_cases: int
    scanned_cases: int
    duplicates: int
    requirements: tuple[TargetResult, ...]
    other_methods: tuple[TargetResult, ...]
    unverified_targets: tuple[TargetResult, ...]
    other_tests: tuple[TestResult, ...]
    unmatched: tuple[UnmatchedRun, ...]


def summarize(
    assessment: Assessment,
    report: Report,
    identities: Mapping[str, Identity],
    report_name: str,
) -> Results:
    """Match report identities exactly; preserve all unmatched data and missing results.

    `identities` is supplied by the pytest extractor's identity convention. Core does not
    import an extractor or guess filesystem paths from dotted class names.
    """
    graph = assessment.graph
    index: dict[Identity, list[str]] = defaultdict(list)
    for test_id, key in sorted(identities.items()):
        index[key].append(test_id)
    grouped: dict[Identity, list[ReportEntry]] = defaultdict(list)
    for entry in report.entries:
        grouped[(entry.classname, entry.name)].append(entry)

    matched: dict[str, list[RunResult]] = defaultdict(list)
    unmatched: list[UnmatchedRun] = []
    for identity, entries in sorted(grouped.items()):
        run = RunResult(
            identity,
            _worst(tuple(e.verdict for e in entries)),
            len(entries),
            tuple(sorted({kind for e in entries for kind in e.kinds})),
            tuple(sorted({detail for e in entries for detail in e.details})),
        )
        classname, name = identity
        # The function name precedes the first '['; parameter IDs can contain more brackets.
        matches = index.get((classname, name.partition("[")[0]), [])
        if not classname or not name:
            reason = "missing classname or name"
        elif not matches:
            reason = "no scanned pytest test matches this identity"
        elif len(matches) > 1:
            reason = f"ambiguous identity: {', '.join(matches)}"
        else:
            matched[matches[0]].append(run)
            continue
        unmatched.append(UnmatchedRun(run, reason))

    tests = {
        test_id: TestResult(
            test_id,
            _worst(tuple(r.verdict for r in matched[test_id])) if matched[test_id] else "no-result",
            tuple(matched[test_id]),
            tuple(sorted({link.dst for link in graph.outgoing(test_id, "verifies")})),
        )
        for test_id in sorted(identities)
    }
    targets: dict[str, list[TestResult]] = defaultdict(list)
    for test in tests.values():
        for target_id in test.verifies:
            targets[target_id].append(test)
    requirements: list[TargetResult] = []
    other_methods: list[TargetResult] = []
    unverified: list[TargetResult] = []
    shown_tests: set[str] = set()
    for node in sorted(graph.nodes.values(), key=lambda n: n.id):
        is_requirement = node.type == "requirement"
        if not (is_requirement and (node.item is not None or node.id in targets)) and not (
            node.type is None and node.id in targets
        ):
            continue
        linked = tuple(targets[node.id])
        method = node.fields.get("Verify-by")
        target = TargetResult(
            node,
            method,
            _worst(tuple(t.verdict for t in linked)) if linked else "untested",
            linked,
            sum(len(t.runs) for t in linked),
        )
        if not is_requirement:
            unverified.append(target)
        elif method in ("inspection", "analysis"):
            other_methods.append(target)
        else:
            requirements.append(target)
        shown_tests.update(t.id for t in linked)
    return Results(
        assessment=assessment,
        report_name=report_name,
        entries=len(report.entries),
        runs=len(grouped),
        matched_runs=sum(len(t.runs) for t in tests.values()),
        matched_cases=sum(bool(t.runs) for t in tests.values()),
        scanned_cases=len(tests),
        duplicates=len(report.entries) - len(grouped),
        requirements=tuple(requirements),
        other_methods=tuple(other_methods),
        unverified_targets=tuple(unverified),
        other_tests=tuple(t for t in tests.values() if t.id not in shown_tests),
        unmatched=tuple(unmatched),
    )


def _worst(verdicts: tuple[Verdict, ...]) -> Verdict:
    return max(verdicts, key=lambda verdict: _RANK[verdict])
