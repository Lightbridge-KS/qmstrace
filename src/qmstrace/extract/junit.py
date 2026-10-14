"""Read pytest JUnit XML entries, without trusting suite summary counts.

Implements: DSN-QMT-09
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qmstrace.core.results import Report, ReportEntry, Verdict

if TYPE_CHECKING:  # parsing happens in reports.py, through defusedxml only
    from xml.etree.ElementTree import Element


def entries(root: Element) -> Report:
    """Return the entries under a `testsuite` or `testsuites` root, or a diagnostic."""
    found = []
    for case in root.iter():
        if _tag(case.tag) != "testcase":
            continue
        kinds = tuple(sorted({_tag(child.tag) for child in case} & {"failure", "error", "skipped"}))
        verdict: Verdict = (
            "fail"
            if {"failure", "error"} & set(kinds)
            else "skip"
            if "skipped" in kinds
            else "pass"
        )
        details = tuple(
            sorted(
                {
                    f"{_tag(child.tag)}: "
                    + " ".join((child.get("message") or child.text or "").strip().splitlines()[:1])
                    for child in case
                    if _tag(child.tag) in kinds
                    and (child.get("message") or child.text or "").strip()
                }
            )
        )
        name = case.get("name", "")
        # pytest's test name precedes the first '['; parameter IDs can contain more brackets.
        found.append(
            ReportEntry(
                case.get("classname", ""), name, verdict, kinds, details, name.partition("[")[0]
            )
        )
    if not found:
        return Report(problem="the report contains no testcase entries", format="junit")
    return Report(tuple(found), format="junit")


def _tag(name: str) -> str:
    return name.rsplit("}", 1)[-1]
