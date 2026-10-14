"""Report verdicts and run details; matching and aggregation stay in the core.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from qmstrace.core.results import CaseResult, Results, TargetResult, TestResult
from qmstrace.render._evidence import _problems
from qmstrace.render._presentation import _heading, _what


def results(view: Results) -> str:
    """Render collected verdicts without making freshness or verification claims."""
    assessment = view.assessment
    lines = [
        f"report: {view.report_name}",
        f"  {view.entries} XML entries · {view.runs} reported runs (distinct full identities)",
        f"  matched: {view.matched_runs} runs of {view.matched_cases} automated tests · "
        f"scanned: {view.scanned_cases} automated tests · "
        f"unmatched: {len(view.unmatched)} run identities",
        "  matched against the current working tree — report commit NOT VERIFIED",
        "  a partial parameter set does not prove every possible variant ran",
    ]
    lines += _problems(assessment)
    lines += [f"  {notice.text}" for notice in assessment.notices]
    if view.duplicates:
        lines.append(
            f"  {view.duplicates} duplicate XML entries combined by full identity; "
            "retry attempts are not inferred"
        )
    through = view.through_cases
    lines += [
        "",
        "requirements — verdicts along verifies links, from automated tests directly or through "
        "test cases:"
        if through
        else "requirements — direct verifies links only:",
    ]
    for target in view.requirements:
        lines += _result_target(target)
    if not view.requirements:
        lines.append("  no test-method requirements visible here")
    if view.other_methods:
        lines += [
            "",
            "inspection / analysis — no verification or approval is established by this report:",
        ]
        for target in view.other_methods:
            lines.append(
                f"  {_heading(target.node)} · Verify-by: {target.method} · {_what(target.node)}"
            )
            if target.tests:
                lines.append(
                    f"    linked tests only: {target.verdict} · {len(target.tests)} automated "
                    f"tests · {target.runs} runs"
                )
                for test in target.tests:
                    lines += _result_test(test, target.node.id, show_pass=True)
            else:
                lines.append("    no linked automated tests")
    if view.unverified_targets:
        lines += ["", "unverified targets — type unknown, not requirement verdicts:"]
        for target in view.unverified_targets:
            lines += _result_target(target)
    if view.other_cases:
        lines += ["", "test cases that reach no requirement — no requirement verdict inferred:"]
        for case in view.other_cases:
            lines += _result_case(case, show_pass=True)
    if view.other_tests:
        lines += [
            "",
            "automated tests that reach no requirement — no requirement verdict inferred:"
            if through
            else "tests without a direct requirement target — no requirement verdict inferred:",
        ]
        for test in view.other_tests:
            lines += _result_test(test, show_pass=True)
    if view.unmatched:
        lines += ["", "unmatched report entries:"]
        for entry in view.unmatched:
            lines.append(
                f"  {entry.run.verdict:<9} {entry.run.identity!r} · "
                f"{entry.run.entries} XML entries · {entry.reason}"
            )
        lines.append(
            "  Fix: check report provenance and scan patterns; use default pytest JUnit names."
        )
    lines += [
        "",
        f"result: {view.matched_cases} matched automated tests · "
        f"{view.matched_runs} matched runs · "
        f"{len(view.unmatched)} unmatched run identities · exit 0 (informational) — "
        "report commit NOT VERIFIED; this repo's tests only",
    ]
    return "\n".join(lines)


def _result_target(target: TargetResult) -> list[str]:
    via = f"via {', '.join(c.node.id for c in target.via)} · " if target.via else ""
    lines = [
        f"  {target.node.id}  {target.verdict:<9} {via}{len(target.tests)} automated tests · "
        f"{target.runs} runs — {target.node.title or target.node.id} · {_what(target.node)}"
    ]
    through = {test.id for case in target.via for test in case.tests}
    for test in target.tests:
        if test.id not in through:  # a test through a case is listed under that case
            lines += _result_test(test, target.node.id)
    for case in target.via:
        lines += _result_case(case)
    return lines


def _result_case(case: CaseResult, *, show_pass: bool = False) -> list[str]:
    """A test case on a verdict's path — its verdict, and the automated tests that ran it."""
    if case.verdict == "pass" and not show_pass:
        return [f"    via {case.node.id}  pass · {len(case.tests)} automated tests"]
    verifies = f" · verifies {', '.join(case.verifies)}" if case.verifies else ""
    title = f" — {case.node.title}" if case.node.title else ""
    # In its own section a case is a row like any other; on a requirement's path, a step under it.
    lead, indent = ("  ", "") if show_pass else ("    via ", "  ")
    lines = [
        f"{lead}{case.node.id}  {case.verdict} · {len(case.tests)} automated tests{verifies}{title}"
    ]
    for test in case.tests:
        lines += [
            f"{indent}{line}" for line in _result_test(test, case.node.id, show_pass=show_pass)
        ]
    return lines


def _result_test(
    test: TestResult, target: str | None = None, *, show_pass: bool = False
) -> list[str]:
    others = tuple(i for i in test.verifies if i != target)
    if test.verdict == "pass" and not show_pass and len(test.verifies) < 2:
        return []
    shared = (
        f" · shared: also verifies {', '.join(others)}"
        if target is not None and len(test.verifies) > 1
        else ""
    )
    targets = f" · verifies {', '.join(test.verifies)}" if target is None and test.verifies else ""
    lines = [f"    {test.verdict:<9} {test.id} · {len(test.runs)} runs{shared}{targets}"]
    for run in test.runs:
        if run.verdict != "pass":
            lines.append(f"      {run.verdict}: {run.identity[1]} ({', '.join(run.kinds)})")
            lines += [f"        {detail}" for detail in run.details]
    return lines
