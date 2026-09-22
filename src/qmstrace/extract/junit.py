"""Read pytest JUnit XML bytes, without opening files or trusting suite summary counts."""

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from qmstrace.core.results import Report, ReportEntry, Verdict


def read(payload: bytes) -> Report:
    """Return entries or a parse diagnostic; XML declarations retain their encoding semantics."""
    try:
        root = ElementTree.fromstring(
            payload, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
    except (ElementTree.ParseError, DefusedXmlException, ValueError, LookupError) as error:
        return Report(problem=f"unreadable JUnit XML ({type(error).__name__}: {error})")
    if _tag(root.tag) not in ("testsuite", "testsuites"):
        return Report(problem="expected a testsuite or testsuites root")
    entries = []
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
        entries.append(
            ReportEntry(case.get("classname", ""), case.get("name", ""), verdict, kinds, details)
        )
    if not entries:
        return Report(problem="the report contains no testcase entries")
    return Report(tuple(entries))


def _tag(name: str) -> str:
    return name.rsplit("}", 1)[-1]
