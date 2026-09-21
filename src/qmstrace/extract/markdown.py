"""Items declared as Markdown headings — requirements, design elements.

`### REQ-SVC-01 — A call carries a key` declares an item when the ID matches the type's
pattern; the item's body runs to the next heading of any level. Under it, `Key: value` lines
are fields, and a field named after a link marker is a link. A heading inside a code fence
declares nothing; frontmatter is skipped. A heading that starts with some other ID is handed
back as a lead for the graph to judge.

An item's text — what its digest covers — is its title and body, the `Change:` line left out,
so citing a change request is not itself a change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import ID_TOKEN, Extracted, Finding, Item, Lead, Link, text_digest
from qmstrace.extract.fields import FIELD, link_line

CHANGE: Final = "Change"
_HEADING: Final = re.compile(r"^#{1,6}\s+(.*?)\s*$")
_LEADING_ID: Final = re.compile(rf"({ID_TOKEN.pattern})(?![A-Za-z0-9-])\s*(.*)$")
_SEPARATOR: Final = re.compile(r"^[\s\u2014\u2013:-]+")  # em dash, en dash, colon, hyphen
_FENCES: Final = ("```", "~~~")


@dataclass
class _Open:
    """The item being read: its heading, and the lines under it so far."""

    id: str
    line: int
    title: str
    body: list[str] = field(default_factory=list)
    fields: dict[str, str] = field(default_factory=dict)


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one Markdown file for items of one type."""
    pattern = item_type.id_pattern
    known = set(config.links) | item_type.fields | {CHANGE}
    items: list[Item] = []
    links: list[Link] = []
    wrong: list[Finding] = []
    leads: list[Lead] = []
    current: _Open | None = None

    def close() -> None:
        if current is not None:
            digest = text_digest(" ".join([current.title, *current.body]))
            fields = dict(current.fields)
            items.append(
                Item(current.id, item_type.name, path, current.line, current.title, digest, fields)
            )

    fence: str | None = None
    for number, raw in _lines(text):
        stripped = raw.lstrip()
        if fence is None:
            fence = next((mark for mark in _FENCES if stripped.startswith(mark)), None)
            is_fence = fence is not None
        else:  # inside a fence nothing is a heading or a field; the lines are still text
            is_fence = True
            if stripped.startswith(fence):
                fence = None
        if is_fence:
            if current is not None:
                current.body.append(raw)
            continue
        if heading := _HEADING.match(raw):
            close()
            current = None
            lead = _LEADING_ID.match(heading.group(1))
            if lead is None:
                continue
            token, title = lead.group(1), _SEPARATOR.sub("", lead.group(2))
            if pattern is not None and pattern.fullmatch(token):
                current = _Open(token, number, title)
            else:
                leads.append(Lead(token, item_type.name, path, number))
            continue
        if current is None:
            continue
        found = FIELD.match(raw)
        key = found.group(1) if found else None
        if found is None or key not in known:
            current.body.append(raw)
            continue
        value = found.group(2)
        if key == CHANGE:
            current.fields.setdefault(key, value)
            continue  # citing a change request is not a change
        current.body.append(raw)
        current.fields.setdefault(key, value)
        if key in config.links:
            made, bad = link_line(current.id, key, value, path, number)
            links += made
            wrong += bad
    close()
    return Extracted(tuple(items), tuple(links), tuple(wrong), tuple(leads))


def _lines(text: str) -> list[tuple[int, str]]:
    """Numbered lines, with a leading frontmatter block left out."""
    lines = list(enumerate(text.splitlines(), start=1))
    if lines and lines[0][1].strip() == "---":
        for index, (_, raw) in enumerate(lines[1:], start=1):
            if raw.strip() in {"---", "..."}:
                return lines[index + 1 :]
    return lines
