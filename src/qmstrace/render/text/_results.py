"""Report verdicts and run details; matching and aggregation stay in the core.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from qmstrace.core.results import Results, TargetResult, TestResult
from qmstrace.render._evidence import _problems
from qmstrace.render._presentation import _heading, _what


def results(view: Results) -> str:
    """Render collected verdicts without making freshness or verification claims."""
    assessment = view.assessment
    lines = [
        f"report: {view.report_name}",
        f"  {view.entries} XML entries · {view.runs} reported runs (distinct full identities)",
        f"  matched: {view.matched_runs} runs of {view.matched_cases} test cases · "
        f"scanned: {view.scanned_cases} test cases · "
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
    lines += ["", "requirements — direct verifies links only:"]
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
                    f"    linked tests only: {target.verdict} · {len(target.tests)} test cases · "
                    f"{target.runs} runs"
                )
                for test in target.tests:
                    lines += _result_test(test, target.node.id, show_pass=True)
            else:
                lines.append("    no directly linked test cases")
    if view.unverified_targets:
        lines += ["", "unverified targets — type unknown, not requirement verdicts:"]
        for target in view.unverified_targets:
            lines += _result_target(target)
    if view.other_tests:
        lines += [
            "",
            "tests without a direct requirement target — no requirement verdict inferred:",
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
        f"result: {view.matched_cases} matched test cases · {view.matched_runs} matched runs · "
        f"{len(view.unmatched)} unmatched run identities · exit 0 (informational) — "
        "report commit NOT VERIFIED; this repo's tests only",
    ]
    return "\n".join(lines)


def _result_target(target: TargetResult) -> list[str]:
    lines = [
        f"  {target.node.id}  {target.verdict:<9} {len(target.tests)} test cases · "
        f"{target.runs} runs — {target.node.title or target.node.id} · {_what(target.node)}"
    ]
    for test in target.tests:
        lines += _result_test(test, target.node.id)
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
