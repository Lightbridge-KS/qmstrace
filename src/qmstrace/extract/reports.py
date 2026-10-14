"""Read a test report's bytes, without opening files: pytest JUnit XML or a .NET TRX file.

The payload is parsed once, safely — no DTD, no entities, nothing external — and the root element
decides the format: `testsuite` or `testsuites` is JUnit, a TeamTest `TestRun` is TRX. Anything
else is refused, never guessed at. XML declarations keep their encoding semantics.

Implements: DSN-QMT-09
"""

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from qmstrace.core.results import Report
from qmstrace.extract import junit, trx


def read(payload: bytes) -> Report:
    """Return the report's entries, or a diagnostic saying why it could not be read."""
    try:
        root = ElementTree.fromstring(
            payload, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
    except (ElementTree.ParseError, DefusedXmlException, ValueError, LookupError) as error:
        return Report(problem=f"unreadable XML ({type(error).__name__}: {error})")
    if root.tag.rsplit("}", 1)[-1] in ("testsuite", "testsuites"):
        return junit.entries(root)
    if root.tag == trx.ROOT:
        return trx.entries(root)
    return Report(problem="expected a JUnit testsuite or testsuites root, or a TRX TestRun root")
