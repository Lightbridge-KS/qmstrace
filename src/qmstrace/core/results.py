"""Report facts matched to scanned automated tests, then attributed along verifies links.

No history is written. A reported run is one distinct full identity; duplicate entries are
combined, not treated as proof of additional attempts. A verdict follows `verifies` links from
the automated tests this report ran — directly, or through the test cases they run (ADR-0003):
an item's verdict is the worst of every automated test that reaches it. A design element
carries `Satisfies`, not `verifies`, so no verdict flows through one.

Implements: DSN-QMT-09
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from qmstrace.core.assessment import Assessment
from qmstrace.core.graph import Node
from qmstrace.core.model import Identity

Verdict = Literal["pass", "skip", "no-result", "fail", "untested"]
_RANK = {"untested": 0, "pass": 1, "skip": 2, "no-result": 3, "fail": 4}
_VERIFIES = "verifies"


@dataclass(frozen=True, slots=True)
class ReportEntry:
    """One test entry, retaining its full report identity and outcome kind. `test` is the name
    a scanned automated test is matched by — the report reader decides it; empty means `name`."""

    classname: str
    name: str
    verdict: Verdict
    kinds: tuple[str, ...] = ()
    details: tuple[str, ...] = ()
    test: str = ""


@dataclass(frozen=True, slots=True)
class Report:
    """The reader's entries, or an explanation of why the payload could not be read."""

    entries: tuple[ReportEntry, ...] = ()
    problem: str | None = None


@dataclass(frozen=True, slots=True)
class RunResult:
    """One full report identity, with repeated entries combined."""

    identity: Identity
    verdict: Verdict
    entries: int
    kinds: tuple[str, ...]
    details: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TestResult:
    """One scanned automated test, its observed runs, and all its explicit targets."""

    id: str
    verdict: Verdict
    runs: tuple[RunResult, ...]
    verifies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CaseResult:
    """A test case — an item that automated tests verify and that verifies in turn — with the
    worst verdict of every automated test that reaches it; `untested` when none does."""

    node: Node
    verdict: Verdict
    tests: tuple[TestResult, ...]
    verifies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TargetResult:
    """A requirement or untyped target, and every automated test that reaches it — directly,
    or through the test cases in `via`."""

    node: Node
    method: str | None
    verdict: Verdict
    tests: tuple[TestResult, ...]
    runs: int
    via: tuple[CaseResult, ...] = ()


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
    matched_cases: int  # automated tests with at least one matched run
    scanned_cases: int  # automated tests scanned
    duplicates: int
    requirements: tuple[TargetResult, ...]
    other_methods: tuple[TargetResult, ...]
    unverified_targets: tuple[TargetResult, ...]
    other_tests: tuple[TestResult, ...]
    unmatched: tuple[UnmatchedRun, ...]
    other_cases: tuple[CaseResult, ...] = ()  # test cases that reach no requirement

    @property
    def through_cases(self) -> bool:
        """Whether any verdict here passes through a test case."""
        return bool(self.other_cases) or any(t.via for t in self.requirements)


def summarize(
    assessment: Assessment,
    report: Report,
    identities: Mapping[str, tuple[Identity, ...]],
    report_name: str,
) -> Results:
    """Match report identities exactly; preserve all unmatched data and missing results.

    `identities` maps each scanned automated test to the identities its runs carry, as its
    extractor recorded them. Core does not import an extractor or guess filesystem paths from
    dotted class names.
    """
    graph = assessment.graph
    index: dict[Identity, list[str]] = defaultdict(list)
    for test_id, keys in sorted(identities.items()):
        for key in keys:
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
        matches = index.get((classname, entries[0].test or name), [])
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

    # Every verifies link in view: this repo's own, and a sibling's own (a ledger's test case).
    out: dict[str, set[str]] = defaultdict(set)
    for link in graph.links:
        if link.marker == _VERIFIES:
            out[link.src].add(link.dst)
    for node in graph.nodes.values():
        for link in node.declares:
            if link.marker == _VERIFIES:
                out[link.src].add(link.dst)
    into: dict[str, set[str]] = defaultdict(set)
    for src, targets in out.items():
        for dst in targets:
            into[dst].add(src)

    tests = {
        test_id: TestResult(
            test_id,
            _worst(tuple(r.verdict for r in matched[test_id])) if matched[test_id] else "no-result",
            tuple(matched[test_id]),
            tuple(sorted(out.get(test_id, ()))),
        )
        for test_id in sorted(identities)
    }
    reached: dict[str, set[str]] = defaultdict(set)  # an item's reaching automated tests
    for test_id in tests:
        seen: set[str] = set()
        frontier = sorted(out.get(test_id, ()))
        while frontier:
            node_id = frontier.pop()
            if node_id in seen or node_id in tests:
                continue
            seen.add(node_id)
            reached[node_id].add(test_id)
            frontier.extend(sorted(out.get(node_id, ())))

    def case(node_id: str) -> CaseResult:
        found = tuple(tests[t] for t in sorted(reached.get(node_id, ())))
        return CaseResult(
            graph.nodes[node_id],
            _worst(tuple(t.verdict for t in found)) if found else "untested",
            found,
            tuple(sorted(out.get(node_id, ()))),
        )

    requirements: list[TargetResult] = []
    other_methods: list[TargetResult] = []
    unverified: list[TargetResult] = []
    shown_tests: set[str] = set()
    shown_cases: set[str] = set()
    for node in sorted(graph.nodes.values(), key=lambda n: n.id):
        is_requirement = node.type == "requirement"
        if not (is_requirement and (node.item is not None or node.id in reached)) and not (
            node.type is None and node.id in reached
        ):
            continue
        linked = tuple(tests[t] for t in sorted(reached.get(node.id, ())))
        via = tuple(
            case(m)
            for m in sorted(into.get(node.id, ()))
            if m not in tests and m in graph.nodes and (m in reached or graph.nodes[m].item)
        )
        method = node.fields.get("Verify-by")
        target = TargetResult(
            node,
            method,
            _worst(tuple(t.verdict for t in linked)) if linked else "untested",
            linked,
            sum(len(t.runs) for t in linked),
            via,
        )
        if not is_requirement:
            unverified.append(target)
        elif method in ("inspection", "analysis"):
            other_methods.append(target)
        else:
            requirements.append(target)
        shown_tests.update(t.id for t in linked)
        shown_cases.update(c.node.id for c in via)
    shown = {t.node.id for group in (requirements, other_methods, unverified) for t in group}

    def reaches_shown(start: str) -> bool:
        seen: set[str] = set()
        frontier = [start]
        while frontier:
            node_id = frontier.pop()
            if node_id in seen:
                continue
            seen.add(node_id)
            if node_id in shown:
                return True
            frontier.extend(out.get(node_id, ()))
        return False

    passing = {  # test cases this report's tests reach that reach no requirement shown above
        m
        for m in out
        if m in reached and m in graph.nodes and graph.nodes[m].type != "requirement"
        if m not in shown_cases and not reaches_shown(m)
    }
    other_cases = tuple(case(m) for m in sorted(passing))
    shown_tests.update(test.id for found in other_cases for test in found.tests)
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
        other_cases=other_cases,
    )


def _worst(verdicts: tuple[Verdict, ...]) -> Verdict:
    return max(verdicts, key=lambda verdict: _RANK[verdict])
