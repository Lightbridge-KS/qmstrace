"""Read a TRX report — the file `dotnet test --logger trx` writes — without trusting its counts.

A run is one `UnitTestResult` under `Results`. Its identity is the class and method of the
`UnitTest` its `testId` names — the class namespace-qualified, nested classes joined with `+`,
as the test framework reports them — and its name is the result's `testName`, so a Theory's rows
stay separate runs of one automated test. The outcome `Passed` is a pass and `NotExecuted` a
skip; any other outcome, or none, is a failure that keeps the raw outcome.

Only those fields and the first line of a result's error message are read. A TRX file also
carries absolute build paths, the machine and user names, standard output and stack traces;
none of it is touched, so none of it can reach what qmstrace prints (ADR-0004).

Implements: DSN-QMT-09
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from qmstrace.core.results import Report, ReportEntry, Verdict

if TYPE_CHECKING:  # parsing happens in reports.py, through defusedxml only
    from xml.etree.ElementTree import Element

NAMESPACE: Final = "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"
ROOT: Final = f"{{{NAMESPACE}}}TestRun"
_NS: Final = f"{{{NAMESPACE}}}"
_VERDICTS: Final[dict[str, Verdict]] = {"Passed": "pass", "NotExecuted": "skip"}


def entries(root: Element) -> Report:
    """Return one entry per test result under a TRX `TestRun` root, or a diagnostic."""
    definitions: dict[str, tuple[str, str]] = {}
    for unit in root.iterfind(f"{_NS}TestDefinitions/{_NS}UnitTest"):
        named = unit.find(f"{_NS}TestMethod")
        if named is not None:
            definitions[unit.get("id", "")] = (named.get("className", ""), named.get("name", ""))
    found = []
    for result in root.iterfind(f"{_NS}Results/{_NS}UnitTestResult"):
        classname, method = definitions.get(result.get("testId", ""), ("", ""))
        outcome = result.get("outcome", "")
        verdict = _VERDICTS.get(outcome, "fail")
        kinds = () if verdict == "pass" else (outcome or "no outcome",)
        message = result.findtext(f"{_NS}Output/{_NS}ErrorInfo/{_NS}Message") or ""
        first = " ".join(message.strip().splitlines()[:1])
        details = (f"{kinds[0]}: {first}",) if kinds and first else ()
        found.append(
            ReportEntry(classname, result.get("testName", ""), verdict, kinds, details, method)
        )
    if not found:
        return Report(problem="the TRX file contains no test results", format="trx")
    return Report(tuple(found), format="trx")
