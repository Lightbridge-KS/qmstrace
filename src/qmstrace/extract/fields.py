"""The field line — `- Key: value` — shared by every extractor that reads fields.

A field whose name is a link marker *is* the link: its value is a comma-separated list of IDs,
and anything else in it is reported, never dropped.

Implements: DSN-QMT-04
"""

from __future__ import annotations

import re
from typing import Final

from qmstrace.core import findings
from qmstrace.core.model import ID_TOKEN, Finding, Link

# An optional list bullet, a key (bold tolerated, the colon inside or outside), then the value.
FIELD: Final = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*|__)?([A-Za-z][A-Za-z-]*)(?:\*\*|__)?\s*:(?:\*\*|__)?\s*(.*?)\s*$"
)


def link_line(
    src: str, marker: str, value: str, path: str, line: int
) -> tuple[list[Link], list[Finding]]:
    """The links one field line declares, and a finding for every part that is not an ID."""
    links: list[Link] = []
    wrong: list[Finding] = []
    for part in (p.strip() for p in value.split(",")):
        if ID_TOKEN.fullmatch(part):
            links.append(Link(src, part, marker, path, line))
        else:
            wrong.append(findings.not_an_id(src, marker, part, path, line))
    return links, wrong
