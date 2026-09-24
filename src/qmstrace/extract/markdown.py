"""Items declared as Markdown headings — requirements, design elements.

`### REQ-SVC-01 — A call carries a key` declares an item when the ID matches the type's
pattern. The item is a section: its heading and everything down to the next heading at the
same or a higher level, sub-sections, tables and diagrams included. In it, `Key: value` lines
are fields, and a field named after a link marker is a link.

Only this repo's IDs end an item: a heading whose first word matches one of its item-ID
patterns, or shares their prefix, starts that item's section — or, for another type, a
section this pass does not read. Any other heading is a sub-heading when deeper, a boundary
when not; `#### IEC-62304 …` stays inside the item. A heading that starts with an ID and
declares nothing of this type is handed back as a lead for the graph to judge.

A heading inside a code fence declares nothing; frontmatter is skipped. An item's text — what
its digest covers — is its title and section, the `Change:` line left out, so citing a change
request is not itself a change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import ID_TOKEN, Extracted, Finding, Item, Lead, Link, text_digest
from qmstrace.extract.fields import FIELD, link_line

CHANGE: Final = "Change"
_HEADING: Final = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_LEADING_ID: Final = re.compile(rf"({ID_TOKEN.pattern})(?![A-Za-z0-9-])\s*(.*)$")
_SEPARATOR: Final = re.compile(r"^[\s\u2014\u2013:-]+")  # em dash, en dash, colon, hyphen
# A fence: three or more backticks or tildes. It closes on a line of the same character, at
# least as long, with nothing after it — so a fenced example can hold a shorter fence.
_FENCE: Final = re.compile(r"(`{3,}|~{3,})(.*)$")


@dataclass(frozen=True, slots=True)
class _Heading:
    """One heading line, read: its level, its words, and the ID it starts with, if any."""

    level: int
    text: str  # the words as written, without the `#` marks
    token: str | None  # the ID the heading starts with
    title: str  # the words after that ID and its separator


@dataclass
class _Open:
    """The item being read: its heading, and the lines of its section so far."""

    id: str
    line: int
    title: str
    level: int
    body: list[str] = field(default_factory=list)
    fields: dict[str, str] = field(default_factory=dict)
    change_line: int | None = None


def extract(path: str, text: str, item_type: ItemType, config: TraceConfig) -> Extracted:
    """Read one Markdown file for items of one type."""
    pattern = item_type.id_pattern
    known = set(config.links) | item_type.fields | {CHANGE, "Status"}
    patterned = [t for t in config.item_types.values() if t.id_pattern is not None]
    items: list[Item] = []
    links: list[Link] = []
    wrong: list[Finding] = []
    leads: list[Lead] = []
    current: _Open | None = None
    other: int | None = None  # the level of another type's item, whose section is not read

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
            opened = _FENCE.match(stripped)
            fence = opened.group(1) if opened else None
            is_fence = fence is not None
        else:  # inside a fence nothing is a heading or a field; the lines are still text
            is_fence = True
            if _closes(stripped, fence):
                fence = None
        if is_fence:
            if current is not None:
                current.body.append(raw)
            continue
        if heading := _heading(raw):
            token = heading.token
            if token is not None and pattern is not None and pattern.fullmatch(token):
                close()
                current, other = _Open(token, number, heading.title, heading.level), None
                continue
            if token is not None:
                leads.append(Lead(token, item_type.name, path, number))
                if _item_shaped(token, patterned):  # another item's section starts here
                    close()
                    current, other = None, heading.level
                    continue
            if current is not None and heading.level > current.level:
                current.body.append(heading.text)  # a sub-heading: part of the item's text
                continue
            close()
            current = None
            if other is not None and heading.level <= other:
                other = None
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
            tokens = [s.strip() for s in value.split(",")]
            prefix = config.change_requests.prefix if config.change_requests else None
            for token in tokens:
                if not ID_TOKEN.fullmatch(token) or (prefix and not token.startswith(prefix)):
                    wrong.append(findings.not_an_id(current.id, CHANGE, token, path, number))
            if current.change_line is not None:
                reason = (
                    f"a second Change field for {current.id} (the first is at line "
                    f"{current.change_line})"
                )
                wrong.append(findings.cannot_parse(path, number, reason))
            else:
                current.change_line = number
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


def form(marker: str, target: str) -> str:
    """How an item read by this extractor declares a link — for a gap's next move."""
    return f"`{marker}: {target}` under its heading"


def _heading(raw: str) -> _Heading | None:
    """A heading line, read — or `None` for any other line."""
    found = _HEADING.match(raw)
    if found is None:
        return None
    level, words = len(found.group(1)), found.group(2)
    lead = _LEADING_ID.match(words)
    if lead is None:
        return _Heading(level, words, None, words)
    return _Heading(level, words, lead.group(1), _SEPARATOR.sub("", lead.group(2)))


def _item_shaped(token: str, patterned: list[ItemType]) -> bool:
    """Whether an ID is one of this repo's kinds: its pattern, or the prefix it starts with."""
    stem = token.split("-", 1)[0]
    for item_type in patterned:
        pattern, prefix = item_type.id_pattern, item_type.id_prefix or ""
        if (pattern is not None and pattern.fullmatch(token)) or (
            prefix and (token.startswith(prefix) or stem == prefix.split("-", 1)[0])
        ):
            return True
    return False


def _closes(stripped: str, fence: str) -> bool:
    """Whether a line closes the open fence: its own character, at least as long, nothing after."""
    run = _FENCE.match(stripped)
    return (
        run is not None
        and run.group(1)[0] == fence[0]
        and len(run.group(1)) >= len(fence)
        and not run.group(2).strip()
    )


def _lines(text: str) -> list[tuple[int, str]]:
    """Numbered lines, with a leading frontmatter block left out."""
    lines = list(enumerate(text.splitlines(), start=1))
    if lines and lines[0][1].strip() == "---":
        for index, (_, raw) in enumerate(lines[1:], start=1):
            if raw.strip() in {"---", "..."}:
                return lines[index + 1 :]
    return lines
